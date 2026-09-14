"""Native locomotion with explicitly logged reconstruction constraints.

The input tracks are uncalibrated reconstructions. Constraints preserve accident
timing where those tracks exceed the stock model's capabilities; these runs are
not free collision-dynamics validation.
"""
import math
import carla
import numpy as np
from .common import wrap
from .motion import motion_kind, reference, RiderFollower, walker_command, clamp


class MotionRuntime:
    def __init__(self, entities, tracks, dt, tire_friction=None, overrides=None):
        self.entities={e['actor_id']:e for e in entities}
        self.tracks=tracks;self.dt=dt;self.states={};self.samples=[]
        self.kinds={aid:motion_kind(e) for aid,e in self.entities.items()}
        self.tire_friction=tire_friction
        self.overrides=overrides or {}
        for aid,override in self.overrides.items():
            if aid not in self.entities or override.get('mode')!='recorded' or not override.get('reason'):
                raise ValueError('Invalid motion exception: '+aid)
            self.kinds[aid]='unsupported_static_conflict'

    def native(self, aid):
        return self.kinds[aid] in ('walker','two_wheeler')

    def initialize(self, aid, actor, t):
        kind=self.kinds[aid];r=reference(self.tracks[aid],t)
        state=dict(kind=kind,blueprint=actor.type_id,position=[],yaw=[],corrections=0,
                   max_correction_m=0.,speed_assists=0,bone_ranges={},moving_samples=0,
                   reference_speed_command=r['motion_speed'])
        if kind=='two_wheeler':
            physics=actor.get_physics_control()  # only native, physics-enabled actors
            wheels=physics.wheels;angles=[w.max_steer_angle for w in wheels if w.max_steer_angle>0]
            if self.tire_friction is not None:
                for wheel in wheels:wheel.tire_friction=self.tire_friction
                physics.wheels=wheels;actor.apply_physics_control(physics)
            wheelbase=clamp((max(w.position.x for w in wheels)-min(w.position.x for w in wheels))/100,.8,3.)
            state['follower']=RiderFollower(wheelbase,max(angles) if angles else 50)
            state['follower'].integral=1.
            actor.apply_control(carla.VehicleControl(throttle=.55,manual_gear_shift=True,gear=2 if r['motion_speed']>5 else 1))
            actor.set_target_velocity(carla.Vector3D(x=r['vx'],y=r['vy']))
        else:
            actor.blend_pose(0.)
        self.states[aid]=state

    def control(self, aid, actor, t):
        s=self.states[aid];r=reference(self.tracks[aid],t)
        tr=actor.get_transform();center=tr.transform(carla.Location(actor.bounding_box.location))
        dx,dy=r['x']-center.x,r['y']-center.y;error=math.hypot(dx,dy)
        # A bounded positional tether is distinct from the native controller and
        # audited as such. Never describe a tethered run as pure physical tracking.
        correction=max(0.,error-.20)
        changed=False
        if correction>0:
            amount=min(correction,.18)
            if error>1.:amount=error-.20
            tr.location.x+=dx/error*amount;tr.location.y+=dy/error*amount
            s['corrections']+=1;s['max_correction_m']=max(s['max_correction_m'],amount);changed=True
        ground=center.z-actor.bounding_box.extent.z
        if abs(ground-r['z'])>.25:
            tr.location.z+=r['z']-ground+.02;changed=True
        yaw_error=wrap(r['motion_yaw']-tr.rotation.yaw)
        if s['kind']=='two_wheeler' and r['motion_speed']>.15 and abs(yaw_error)>12:
            tr.rotation.yaw+=clamp(yaw_error,-4.,4.);changed=True
        if changed:actor.set_transform(tr)
        center=tr.transform(carla.Location(actor.bounding_box.location))
        if s['kind']=='walker':
            cmd=walker_command(self.tracks[aid],t,center.x,center.y,max_speed=4.7)
            actor.apply_control(carla.WalkerControl(direction=carla.Vector3D(x=cmd['dx'],y=cmd['dy']),speed=cmd['speed']))
        else:
            v=actor.get_velocity();speed=math.hypot(v.x,v.y)
            cmd=s['follower'].step(self.tracks[aid],t,center.x,center.y,tr.rotation.yaw,speed,self.dt)
            actor.apply_control(carla.VehicleControl(throttle=cmd['throttle'],brake=cmd['brake'],steer=cmd['steer']))
            s['reference_speed_command']+=clamp(r['motion_speed']-s['reference_speed_command'],-6*self.dt,4*self.dt)
            if abs(speed-r['motion_speed'])>.75:
                # At high reference speeds, integrating from the observed speed
                # repeatedly loses the same gearbox/drag decrement and never
                # catches up. Integrate the bounded reference command instead.
                assisted=s['reference_speed_command'] if r['motion_speed']>10 else speed+clamp(r['motion_speed']-speed,-6*self.dt,4*self.dt)
                a=math.radians(tr.rotation.yaw)
                actor.set_target_velocity(carla.Vector3D(x=assisted*math.cos(a),y=assisted*math.sin(a),z=v.z))
                s['speed_assists']+=1

    def observe(self, aid, actor, state, t, frame, sample_bones=False):
        s=self.states[aid];r=reference(self.tracks[aid],t)
        tr=state.get_transform();c=tr.transform(carla.Location(actor.bounding_box.location));v=state.get_velocity()
        error=math.hypot(c.x-r['x'],c.y-r['y']);s['position'].append(error)
        if r['motion_speed']>.15:s['yaw'].append(abs(wrap(tr.rotation.yaw-r['motion_yaw'])));s['moving_samples']+=1
        self.samples.append(dict(actor_id=aid,replay_time_s=t,carla_frame=frame,x=c.x,y=c.y,
            yaw_carla_deg=tr.rotation.yaw,speed_m_s=math.hypot(v.x,v.y),position_error_m=error,
            reference_speed_m_s=r['motion_speed'],constraint_count=s['corrections']))
        if sample_bones and s['kind']=='walker':
            for bone in actor.get_bones().bone_transforms:
                if 'foot' not in bone.name.lower():continue
                p=bone.component.location;xyz=np.array([p.x,p.y,p.z])
                lo,hi=s['bone_ranges'].get(bone.name,(xyz.copy(),xyz.copy()))
                s['bone_ranges'][bone.name]=(np.minimum(lo,xyz),np.maximum(hi,xyz))

    def summary(self):
        result={}
        for aid,s in self.states.items():
            p=s['position'];y=s['yaw']
            result[aid]=dict(kind=s['kind'],blueprint=s['blueprint'],samples=len(p),
                position_p95_m=float(np.percentile(p,95)) if p else None,
                position_max_m=max(p,default=None),moving_yaw_p95_deg=float(np.percentile(y,95)) if y else 0,
                trajectory_constraint_steps=s['corrections'],max_constraint_step_m=s['max_correction_m'],
                speed_assist_steps=s['speed_assists'],moving_samples=s['moving_samples'],
                foot_component_ranges_m={k:float(np.linalg.norm(hi-lo)) for k,(lo,hi) in s['bone_ranges'].items()})
        return dict(version='motion_full_v1',control_hz=1/self.dt,actors=result,
            unsupported_models={aid:kind for aid,kind in self.kinds.items() if kind.startswith('unsupported')},
            policy='native locomotion with logged trajectory constraints; recorded accident timing preserved',
            constraint_counter_scope='horizontal position corrections; ground/yaw stabilization and speed assistance are also enabled',
            tire_friction=self.tire_friction,friction_application='per native vehicle wheel; no overlap trigger',
            speed_assistance='bounded reference-speed integrator above 10 m/s; native-speed correction below',
            recorded_exceptions=self.overrides,
            free_collision_dynamics_validated=False)
