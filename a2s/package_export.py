"""Export verified Windows CARLA maps without any editor/core CARLA binaries."""
import zipfile
from .common import PROJECT,IDS,read,write,sha
from .unreal_package import ROOT,PACKAGE


def build():
    entries={};maps=[]
    cooked=ROOT/'Saved/Cooked/WindowsNoEditor/CarlaUE4/Content'/PACKAGE
    for sid in IDS:
        out=PROJECT/'outputs'/sid;r=read(out/'validation/carla_imported/runtime_report.json')
        receipt=read(out/'validation/unreal_import_receipt.json')
        if not r.get('success') or not r.get('imported_geometry_complete') or r['engine_surface_check']['misses']:
            raise RuntimeError('Complete engine verification required: '+sid)
        maps.append(dict(scene_id=sid,map=receipt['unreal_map'],meshes=receipt['mesh_count']))
        for f in receipt['files']:
            path=cooked/f['path']
            if sha(path)!=f['sha256']:raise RuntimeError('Cooked asset differs from verified installation: '+str(path))
            entries[path]=f['sha256']
        xodr=out/'map'/(receipt['map_name']+'.xodr')
        entries[xodr]=receipt['xodr_sha256']
    dest=PROJECT/'outputs/carla_package';dest.mkdir(exist_ok=True)
    archive=dest/'Accident2SimScenes_CARLA_0.9.15_Windows.zip'
    manifest=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for path,digest in entries.items():
            if path.suffix=='.xodr':relative='Maps/'+path.stem+'/OpenDrive/'+path.name
            else:relative=path.relative_to(cooked).as_posix()
            member='CarlaUE4/Content/'+PACKAGE+'/'+relative
            z.write(path,member);manifest.append(dict(path=member,sha256=digest,bytes=path.stat().st_size))
        z.writestr('IMPORT_README.txt','CARLA 0.9.15 Windows map resources\nExtract into WindowsNoEditor (next to CarlaUE4.exe).\n'
                   'Only the Accident2SimScenes content namespace is included; no CARLA core programs or plugins.\n'
                   'Connect using matching CARLA 0.9.15 Python API, then call client.load_world(full map path).\n\n'
                   +'\n'.join(m['scene_id']+' : '+m['map'] for m in maps))
    write(dest/'package_manifest.json',dict(target='CARLA 0.9.15 Windows',maps=maps,files=manifest,archive_sha256=sha(archive)))
    print('PACKAGE_EXPORTED',archive,archive.stat().st_size,flush=True)


if __name__=='__main__':build()
