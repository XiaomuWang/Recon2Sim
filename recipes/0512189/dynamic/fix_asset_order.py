from pathlib import Path
p=Path('dynamic_replay_0512189/scripts/build_dynamic_assets.py');s=p.read_text();k=s.index('def box(c,d,ma,bevel=');helpers=s[k:];s=s[:k];i=s.index('# ---- video-informed');s=s[:i]+helpers+'\n'+s[i:];p.write_text(s)
