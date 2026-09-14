"""Trajectory-following primitives, independent of CARLA for offline validation.

Recorded positions remain the reference. Controllers never silently retime an
accident or teleport a moving actor to conceal a tracking failure.
"""
import math
from .common import interpolate, wrap

ORIGINAL_SCENES = ('014346', '019742', '016955', '024388', '0512189', '0508656', 'ANA031')


def clamp(value, low, high):
    return max(low, min(high, value))


def motion_kind(entity):
    """Semantic exceptions take precedence over stock substitute blueprints."""
    name = (entity['actor_id'] + ' ' + entity.get('entity_name', '')).lower()
    if 'sweeper' in name or '清扫' in name:
        return 'unsupported_sweeper'
    if entity['type'] == 'tricycle' or any(s in name for s in ('tricycle', 'trike', '三轮', 'canopy')):
        return 'unsupported_tricycle'
    if entity['type'] == 'pedestrian':
        return 'walker'
    if entity['type'] in ('bicycle', 'motorbike'):
        return 'two_wheeler'
    return 'recorded'


def reference(rows, t, window=.16):
    """Estimate velocity from metric displacement, not possibly stale speed CSV.

    Symmetric local differences suppress heading noise; stationary headings come
    from the recorded pose. Shortest-angle arithmetic handles +/-180 crossings.
    """
    pose = interpolate(rows, t)
    if pose is None:
        return None
    ta = max(rows[0]['replay_time_s'], t-window)
    tb = min(rows[-1]['replay_time_s'], t+window)
    a, b = interpolate(rows, ta), interpolate(rows, tb)
    dt = max(tb-ta, 1e-6)
    vx, vy = (b['x']-a['x'])/dt, (b['y']-a['y'])/dt
    speed = math.hypot(vx, vy)
    return dict(pose, vx=vx, vy=vy, motion_speed=speed,
                motion_yaw=math.degrees(math.atan2(vy, vx)) if speed > .08 else pose['yaw_carla_deg'])


class RiderFollower:
    """Pure-pursuit steering + bounded PI speed tracking in actor coordinates."""
    def __init__(self, wheelbase=1.5, max_steer_degrees=50):
        self.wheelbase = wheelbase
        self.max_steer = math.radians(max_steer_degrees)
        self.integral = 0.
        self.steer = 0.

    def step(self, rows, t, x, y, yaw, speed, dt):
        ref = reference(rows, t)
        angle = math.radians(yaw)
        along = (ref['x']-x)*math.cos(angle)+(ref['y']-y)*math.sin(angle)
        desired = clamp(ref['motion_speed'] + .65*along, 0., 22.)
        # A longer lookahead at speed avoids oscillatory handlebar corrections.
        ahead = min(rows[-1]['replay_time_s'], t+clamp(2.0/max(desired, .5), .35, 1.2))
        target = reference(rows, ahead)
        dx, dy = target['x']-x, target['y']-y
        lateral = -dx*math.sin(angle)+dy*math.cos(angle)
        curvature = 2*lateral/max(dx*dx+dy*dy, .5)
        steer = clamp(math.atan(self.wheelbase*curvature)/self.max_steer, -1., 1.)
        self.steer += clamp(steer-self.steer, -1.5*dt, 1.5*dt)
        err = desired-speed
        self.integral = clamp(self.integral+err*dt, -3., 3.)
        effort = .5*err+.4*self.integral + (.15 if desired > .1 else 0.)
        return dict(steer=self.steer, throttle=clamp(effort, 0., 1.),
                    brake=clamp(-effort, 0., 1.) if desired > .08 else 1.,
                    desired_speed=desired, reference=ref)


def walker_command(rows, t, x, y, max_speed=3.):
    ref = reference(rows, t)
    vx = ref['vx']+2.5*(ref['x']-x)
    vy = ref['vy']+2.5*(ref['y']-y)
    speed = math.hypot(vx, vy)
    if speed < .025:
        return dict(dx=0., dy=0., speed=0., reference=ref)
    return dict(dx=vx/speed, dy=vy/speed, speed=min(speed, max_speed), reference=ref)
