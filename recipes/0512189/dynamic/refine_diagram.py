from pathlib import Path
p=Path('dynamic_replay_0512189/scripts/render_topdown.py');s=p.read_text(encoding='utf-8-sig').replace('380-y*7.8','380-y*6.0').replace("yy=624+(i//4)*35;dr.text((xx,yy),a['label_zh'],font=small,fill='#b3ccc6')","yy=666+(i//4)*31;col=tuple(map(int,a['color'].split(','))) if a.get('color') else (193,124,166);dr.rounded_rectangle((xx,yy+4,xx+16,yy+17),radius=3,fill=col);dr.text((xx+23,yy),a['label_zh'],font=small,fill='#b3ccc6')")
p.write_text(s,encoding='utf-8')
