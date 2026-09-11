from pathlib import Path
p=Path('dynamic_replay_0512189/scripts/export_template.py');s=p.read_text(encoding='utf-8')
s=s.replace("O=P/'template_compatible';O.mkdir(exist_ok=True)","O=P/'template_compatible';O.mkdir(exist_ok=True)\nPLAYBACK_OFFSET=.30\nACTIVATION_LEAD=.20\ndef staging(index):return {'x':-135+(index%6)*17,'y':-48-(index//6)*6,'z':.25,'h':0}")
s=s.replace("conditionEdge='rising'","conditionEdge='none'")
s=s.replace(" story=sub(sb,'Story',name='MyStory')", " for index,a in enumerate(data['actors']):\n  s=a['samples'][0] if a['start_t']==0 else staging(index)\n  private=sub(actions,'Private',entityRef=mapping[a['id']]);world(sub(sub(private,'PrivateAction'),'TeleportAction'),dict(s,z=s['z']+.15),unit)\n  sa=sub(sub(sub(private,'PrivateAction'),'LongitudinalAction'),'SpeedAction');sub(sa,'SpeedActionDynamics',dynamicsShape='step',value=0,dynamicsDimension='time');sub(sub(sa,'SpeedActionTarget'),'AbsoluteTargetSpeed',value=0)\n story=sub(sb,'Story',name='MyStory')")
s=s.replace(" offset=.04\n for a in data['actors']:"," offset=PLAYBACK_OFFSET\n for index,a in enumerate(data['actors']):")
s=s.replace("{'t':a['start_t'],'pose':a['samples'][0]", "{'t':a['start_t']+offset-ACTIVATION_LEAD,'pose':dict(a['samples'][0],z=a['samples'][0]['z']+.15)")
s=s.replace("  events.sort(key=lambda e:e['t'])", "  if a['end_t']<data['duration_s']:\n   events.append({'t':a['end_t']+offset+.20,'pose':staging(index),'speed':0.,'route':None,'type':'exit_staging'})\n  events.sort(key=lambda e:e['t'])")
s=s.replace("priority='parallel');action_index=0", "priority='parallel',maximumExecutionCount=1);action_index=0")
s=s.replace("   event_rows.append(","   source_t=a['start_t'] if e['type']=='activation' else a['end_t'] if e['type']=='exit_staging' else e['t']-offset\n   event_rows.append(")
s=s.replace("round(e['t']-(0 if e['type']=='activation' else offset)+data['source_video_start_s'],6)","round(source_t+data['source_video_start_s'],6)")
a=s.index(" stop=copy.deepcopy(template.find('Storyboard/Story/Act/StopTrigger'))");b=s.index(' return root,event_rows,run_rows',a)
s=s[:a]+" # Full-clip replay stops on time only, without inherited collision conditions.\n trigger(act,'StopTrigger',data['duration_s']+.60,'ActTimeout')\n trigger(sb,'StopTrigger',data['duration_s']+.60,'ScenarioTimeout')\n"+s[b:]
s=s.replace("|{'Pedestrian'}", "|{'Pedestrian','Private'}").replace('max(times)<=120.05','max(times)<=120.50').replace("for k in ['x','y','z'])\n  report", "for k in ['x','y'])\n  report").replace('Pedestrian only (needed for visible people)','Pedestrian for visible people; Private for explicit per-entity Init')
a=s.index(" actions=sr.find('Storyboard/Init/Actions')");b=s.index(' # Storyboard time stop',a)
s=s[:a]+''' for a in data['actors']:
  if a['end_t']<120:
   name=mapping[a['id']];man=sr.find('.//Maneuver[@name="'+name+'_EventsManeuver"]');ev=man.findall('Event')[-1]
   for action in ev.findall('Action'):ev.remove(action)
   action=E.Element('Action',name=name+'_Delete');ev.insert(0,action)
   ea=sub(sub(action,'GlobalAction'),'EntityAction',entityRef=name);sub(ea,'DeleteEntityAction')
'''+s[b:]
s=s.replace("120.10,'ScenarioTimeout'","120.60,'ScenarioTimeout'").replace("{'motion_time_offset_s':.04,","{'motion_time_offset_s':PLAYBACK_OFFSET,'activation_lead_s':ACTIVATION_LEAD,")
p.write_text(s,encoding='utf-8')
q=Path('dynamic_replay_0512189/scripts/export_xosc.py');q.write_text(q.read_text(encoding='utf-8').replace("conditionEdge='rising'","conditionEdge='none'"),encoding='utf-8')
