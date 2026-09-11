from pathlib import Path
s=Path('dynamic_replay_014346/scripts/export_template_timeline.py').read_text(encoding='utf-8');s=s[:s.index('def main():')]
s=s.replace('NanshanGate014346','MeituanLane0512189').replace("+52,6)","+data['source_video_start_s'],6)")
s=s.replace("root=E.Element('OpenSCENARIO')","root=E.Element('OpenSCENARIO')")
s=s.replace("if a.get('color'):sub(props,'Property',name='color',value=a['color'])","if a.get('color'):sub(props,'Property',name='color',value=a['color'])\n  if a['id']=='ego':sub(props,'Property',name='type',value='ego_vehicle')")
s=s.replace("else 'motorbike' if a['category'] in ['motorcycle','tricycle','parked'] else 'car'","else 'bus' if a['category']=='bus' else 'van' if a['category']=='van' else 'motorbike' if a['category'] in ['motorcycle','tricycle','parked'] else 'car'")
# Set weather to source overcast; keep the template's exact six parameters and element form.
s=s.replace("story=sub(sb,'Story',name='MyStory')","actions.find('.//Weather').set('cloudState','overcast');actions.find('.//Sun').set('intensity','0.2')\n story=sub(sb,'Story',name='MyStory')")
Path('dynamic_replay_0512189/scripts/export_template.py').write_text(s,encoding='utf-8')
