"""Execute an isolated recipe; omit its expensive presentation renders."""
import sys
from pathlib import Path
path=Path(sys.argv[sys.argv.index('--')+1]).resolve()
sys.path.insert(0,str(path.parent))
code=path.read_text(encoding='utf-8-sig')
code=code.replace('bpy.ops.render.render(write_still=True)', 'None # presentation renders skipped by Recon2Sim')
exec(compile(code,str(path),'exec'), {'__file__':str(path),'__name__':'__main__'})
