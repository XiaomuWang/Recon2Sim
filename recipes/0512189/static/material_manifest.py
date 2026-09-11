"""Run with Blender after build_scene.py to document the source PBR nodes."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'MeituanLane0512189.blend'))
used={m.name for o in bpy.context.scene.objects if o.type=='MESH' for m in o.data.materials if m}
items=[]
for m in bpy.data.materials:
 if m.name not in used or not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if p is None:continue
 d={'material':m.name,'base_color_linear':list(p.inputs['Base Color'].default_value),'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value,'textures':[],'two_sided_recommended':m.name.startswith('Leaf')}
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   fn=Path(n.image.filepath).name
   d['textures'].append({'path':'textures/'+fn,'color_space':n.image.colorspace_settings.name,'usage':'normal' if '_normal' in fn else 'roughness' if '_roughness' in fn else 'basecolor'})
 items.append(d)
(P/'material_manifest.json').write_text(json.dumps({'materials':items,'note':'Source Blender PBR settings. Reconnect external roughness/normal maps in Unreal if FBX auto-import does not preserve them.'},indent=2))
print('Material manifest:',len(items))
