"""Isolated native Unreal commandlet pipeline for CARLA FBX map packages.

Uses the locally built UE 4.26.2/CARLA editor without changing its source assets.
New assets and cooked files stay in Recon2Sim/ue_import until installation.
"""
import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path
from .common import PROJECT,IDS,read,write,sha
from .fbx_names import prepare as prepare_names

SOURCE=Path(os.environ.get('A2S_EDITOR_PROJECT','D:/code/carla-0.9.12/Unreal/CarlaUE4'))
ENGINE=Path(os.environ.get('A2S_UE_ENGINE','D:/Engine'))
ROOT=PROJECT/'ue_import'
PACKAGE='Accident2SimScenes'
TARGET=Path(os.environ.get('A2S_CARLA_ROOT','D:/code/CARLA_0.9.15/WindowsNoEditor/CarlaUE4'))


def clear_scene(content,name):
    """Remove only this generated scene, leaving other maps and core assets intact."""
    if not re.fullmatch(r'[A-Za-z0-9_]+',name):raise ValueError('Unsafe scene name')
    base=(content/PACKAGE).resolve()
    candidates=[base/'Maps'/name]
    if (base/'Static').exists():candidates.extend(p/name for p in (base/'Static').iterdir() if p.is_dir())
    for path in candidates:
        if not path.exists():continue
        if base not in path.resolve().parents:raise RuntimeError('Scene path escaped package')
        for nested in path.rglob('*'):
            if nested.is_dir() and base not in nested.resolve().parents:raise RuntimeError('Unexpected scene directory link')
        shutil.rmtree(path)


def setup():
    ROOT.mkdir(exist_ok=True)
    for folder in ['Config','Binaries','Plugins']:
        shutil.copytree(SOURCE/folder,ROOT/folder,dirs_exist_ok=True,
            ignore=shutil.ignore_patterns('Intermediate','CarlaDependencies','*.pdb','*.lib','*.exp','*.exe','*.target'))
    shutil.copy2(SOURCE/'CarlaUE4.uproject',ROOT/'CarlaUE4.uproject')
    config=read(ROOT/'CarlaUE4.uproject')
    config['Plugins']=[p for p in config['Plugins'] if p['Name'] not in ['PythonScriptPlugin','EditorScriptingUtilities']]
    write(ROOT/'CarlaUE4.uproject',config)
    (ROOT/'Content').mkdir(exist_ok=True)
    link=ROOT/'Content/Carla'
    if not link.exists():
        subprocess.run(['powershell','-NoProfile','-Command',"New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(SOURCE/'Content/Carla')+"' | Out-Null"],check=True)
    # Never save source Carla assets: only /Game/Accident2SimScenes is writable output.
    (ROOT/'logs').mkdir(exist_ok=True)
    return ROOT/'CarlaUE4.uproject'


def settings(sid):
    out=PROJECT/'outputs'/sid;cfg=read(out/'scene_config.json');name=cfg['map_name']
    prepared=ROOT/'fbx'/name/(name+'.fbx')
    aliases=prepare_names(out/'map'/(name+'.fbx'),prepared)
    if any(re.search(r'light|sign|_tile_',n,re.I) for n in aliases['mesh_names']):
        raise RuntimeError('Reserved native importer marker remains in FBX mesh name')
    write(out/'validation/fbx_import_names.json',aliases)
    options=dict(bImportMesh=True,bImportMaterials=True,bImportTextures=True,bImportAsSkeletal=False,
        MeshTypeToImport=0,bConvertScene=True,bConvertSceneUnit=True,
        StaticMeshImportData=dict(bCombineMeshes=False,bAutoGenerateCollision=False,bConvertScene=True,bConvertSceneUnit=True,
            bForceFrontXAxis=False,bTransformVertexToAbsolute=True,bGenerateLightmapUVs=True,
            NormalImportMethod=2,ImportUniformScale=1.0))
    setting=ROOT/(sid+'_import.json')
    write(setting,{'ImportGroups':[dict(ImportSettings=options,FactoryName='FbxFactory',
        DestinationPath='/Game/'+PACKAGE+'/Maps/'+name,bReplaceExisting='true',FileNames=[str(prepared)]) ]})
    folder=ROOT/'Content'/PACKAGE/'Maps'/name/'OpenDrive';folder.mkdir(parents=True,exist_ok=True)
    shutil.copy2(out/'map'/(name+'.xodr'),folder/(name+'.xodr'))
    write(ROOT/'Content'/PACKAGE/'Config'/(PACKAGE+'.Package.json'),dict(props=[],maps=[dict(name=name,path='/Game/'+PACKAGE+'/Maps/'+name,use_carla_materials=False)]))
    return setting,name


def run(name,args,label):
    # Distance fields are optional rendering data, independent of triangle
    # collision. Embree voxelization of the large terrain makes builds impractical.
    engine_ini=ROOT/'Config/DefaultEngine.ini'
    config=engine_ini.read_text(encoding='utf-8-sig')
    config=re.sub(r'(?m)^r.GenerateMeshDistanceFields=.*$', 'r.GenerateMeshDistanceFields=False',config)
    if '[DevOptions.Shaders]' not in config:
        config+='\n[DevOptions.Shaders]\nWorkerProcessPriority=0\nNumUnusedShaderCompilingThreads=8\n'
    config=re.sub(r'(?m)^NumUnusedShaderCompilingThreads=.*$', 'NumUnusedShaderCompilingThreads=8',config)
    engine_ini.write_text(config,encoding='utf-8')
    log=ROOT/'logs'/(label+'.log')
    shader_dir=PROJECT/'runtime/ue_shaders';shader_dir.mkdir(parents=True,exist_ok=True)
    cmd=[str(ENGINE/'Engine/Binaries/Win64/UE4Editor-Cmd.exe'),str(ROOT/'CarlaUE4.uproject'),'-run='+name,
         '-unattended','-nosplash','-nop4','-nosourcecontrol','-nosound','-stdout','-FullStdOutLogOutput',
         '-ShaderWorkingDir='+str(shader_dir),'-abslog='+str(log)]+args
    env=dict(os.environ);env['UE-LocalDataCachePath']=str(PROJECT/'runtime/ue_ddc')
    with (ROOT/'logs'/(label+'_console.log')).open('w',encoding='utf-8') as f:
        p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError('Unreal '+label+' failed '+str(p.returncode)+': '+str(log))
    print('UNREAL_COMPLETE',label,flush=True)


def build(sid,from_stage='import'):
    if not (ROOT/'CarlaUE4.uproject').exists():setup()
    if from_stage=='import':clear_scene(ROOT/'Content',read(PROJECT/'outputs'/sid/'scene_config.json')['map_name'])
    setting,name=settings(sid)
    stage=['import','move','prepare','cook'].index(from_stage)
    if stage<=0:run('ImportAssets',['-importSettings='+str(setting),'-replaceexisting'],sid+'_import')
    if stage<=1:run('MoveAssets',['-PackageName='+PACKAGE,'-Maps='+name,'-nullrhi'],sid+'_move')
    if stage<=2:run('PrepareAssetsForCooking',['-PackageName='+PACKAGE,'-OnlyPrepareMaps=1','-nullrhi'],sid+'_prepare')
    map_path=ROOT/'Content'/PACKAGE/'Maps'/name/(name+'.umap')
    if not map_path.exists():raise RuntimeError('Commandlet did not produce map: '+str(map_path))
    write(PROJECT/'outputs'/sid/'validation/unreal_native_import.json',dict(scene_id=sid,map_name=name,
        editor_project=str(ROOT/'CarlaUE4.uproject'),editor_version='UE 4.26.2 / CARLA editor 0.9.12',target_runtime='CARLA 0.9.15 Windows',
        source_fbx_sha256=sha(PROJECT/'outputs'/sid/'map'/(name+'.fbx')),map_created=True,runtime_verified=False))
    cook(sid,name)


def cook(label,name):
    # UE4 skips CookDir enumeration when SkipSoftReferences is enabled. Supply
    # every new package through an ini list instead, avoiding that engine trap.
    editor_ini=ROOT/'Config/DefaultEditor.ini'
    ini=editor_ini.read_text(encoding='utf-8-sig') if editor_ini.exists() else ''
    ini=re.sub(r'(?ms)^\[A2SCookAssets\].*?(?=^\[|\Z)','',ini)
    entries=['/Game/'+p.relative_to(ROOT/'Content').with_suffix('').as_posix()
             for p in (ROOT/'Content'/PACKAGE).rglob('*') if p.suffix in ['.uasset','.umap'] and (label=='batch' or name in p.parts)]
    editor_ini.write_text(ini+'\n[A2SCookAssets]\n'+'\n'.join('+Map='+p for p in entries)+'\n',encoding='utf-8')
    extra=[] if label=='batch' else ['-OutputDir='+str(ROOT/'Saved/SingleCook'/label/'[Platform]')]
    run('Cook',['-TargetPlatform=WindowsNoEditor','-Map=/Game/'+PACKAGE+'/Maps/'+name+'/'+name,
                '-MapIniSection=A2SCookAssets','-NoDefaultMaps','-NoGameAlwaysCook',
                '-SkipHardReferences','-SkipSoftReferences','-LogCmds=LogCook Verbose,LogTexture Verbose',
                '-CookCultures=en','-unversioned','-compressed','-iterate']+extra,label+'_cook')
    if label!='batch':
        single=ROOT/'Saved/SingleCook'/label/'WindowsNoEditor/CarlaUE4/Content'/PACKAGE
        if not (single/'Maps'/name/(name+'.umap')).is_file():raise RuntimeError('Single-scene cooked map missing')
        destination=ROOT/'Saved/Cooked/WindowsNoEditor/CarlaUE4/Content'
        clear_scene(destination,name)
        for src in single.rglob('*'):
            if src.is_file() and name in src.relative_to(single).parts:
                dst=destination/PACKAGE/src.relative_to(single);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)


def build_many(ids):
    """Share editor startup and shader caches across a batch of reconstructed maps."""
    if not (ROOT/'CarlaUE4.uproject').exists():setup()
    groups=[];maps=[]
    for sid in ids:
        clear_scene(ROOT/'Content',read(PROJECT/'outputs'/sid/'scene_config.json')['map_name'])
        setting,name=settings(sid);groups.extend(read(setting)['ImportGroups'])
        maps.append(dict(name=name,path='/Game/'+PACKAGE+'/Maps/'+name,use_carla_materials=False))
    write(ROOT/'Content'/PACKAGE/'Config'/(PACKAGE+'.Package.json'),dict(props=[],maps=maps))
    batch=ROOT/'batch_import.json';write(batch,dict(ImportGroups=groups))
    run('ImportAssets',['-importSettings='+str(batch),'-replaceexisting'],'batch_import')
    # Use Unreal's response-file support to preserve the quoted space-separated map list.
    arguments=ROOT/'batch_move_args.txt'
    arguments.write_text('-PackageName='+PACKAGE+' -Maps="'+' '.join(m['name'] for m in maps)+'"',encoding='utf-8')
    run('MoveAssets',['-CmdLineFile='+str(arguments),'-nullrhi'],'batch_move')
    run('PrepareAssetsForCooking',['-PackageName='+PACKAGE,'-OnlyPrepareMaps=1','-nullrhi'],'batch_prepare')
    for sid,m in zip(ids,maps):
        if not (ROOT/'Content'/PACKAGE/'Maps'/m['name']/(m['name']+'.umap')).is_file():
            raise RuntimeError('Missing batch map: '+sid)
        write(PROJECT/'outputs'/sid/'validation/unreal_native_import.json',dict(scene_id=sid,map_name=m['name'],
            editor_version='UE 4.26.2 / CARLA editor 0.9.12',target_runtime='CARLA 0.9.15 Windows',
            source_fbx_sha256=sha(PROJECT/'outputs'/sid/'map'/(m['name']+'.fbx')),map_created=True,runtime_verified=False))
    for sid,m in zip(ids,maps):
        cook(sid,m['name'])


def install(sid,target=TARGET):
    """Install only our namespaced cooked assets; never replace CARLA core assets."""
    out=PROJECT/'outputs'/sid;cfg=read(out/'scene_config.json');name=cfg['map_name']
    cooked=ROOT/'Saved/Cooked/WindowsNoEditor/CarlaUE4/Content'/PACKAGE
    mapfile=cooked/'Maps'/name/(name+'.umap')
    if not mapfile.is_file() or not mapfile.with_suffix('.uexp').is_file():
        raise RuntimeError('Cooked map and export data are required: '+str(mapfile))
    mesh_files=[p for p in (cooked/'Static').rglob('*.uasset') if name in p.parts]
    expected_meshes=read(out/'validation/fbx/fbx_validation.json')['mesh_count']
    active_meshes=[p for p in mesh_files if not re.search('light|sign',p.stem,re.I)]
    if len(active_meshes)!=expected_meshes:
        raise RuntimeError('Incomplete cooked FBX meshes: '+str(len(active_meshes))+'/'+str(expected_meshes))
    for asset in mesh_files:
        if not asset.with_suffix('.uexp').is_file():raise RuntimeError('Missing mesh export data: '+str(asset))
    if not (target/'Binaries/Win64/CarlaUE4-Win64-Shipping.exe').is_file():
        raise RuntimeError('Target is not a packaged Windows CARLA installation')
    destination=(target/'Content'/PACKAGE).resolve()
    if destination.parent!=(target/'Content').resolve():raise RuntimeError('Unsafe destination')
    files=[]
    for src in cooked.rglob('*'):
        if not src.is_file():continue
        relative=src.relative_to(cooked)
        if name not in relative.parts:continue
        if src.suffix.lower() not in ['.uasset','.uexp','.ubulk','.umap']:continue
        dst=destination/relative;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        files.append(dict(path=str(relative),sha256=sha(dst),bytes=dst.stat().st_size))
    xodr=out/'map'/(name+'.xodr');xdst=destination/'Maps'/name/'OpenDrive'/xodr.name
    xdst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(xodr,xdst)
    receipt=dict(scene_id=sid,map_name=name,package=PACKAGE,
        unreal_map='/Game/'+PACKAGE+'/Maps/'+name+'/'+name,
        fbx_sha256=sha(out/'map'/(name+'.fbx')),xodr_sha256=sha(xodr),
        installed_directory=str(destination),files=files,mesh_count=len(active_meshes),name_aliases=read(out/'validation/fbx_import_names.json'),method='native FBX ImportAssets + PrepareAssetsForCooking + Windows Cook',
        editor_version='UE 4.26.2 / CARLA editor 0.9.12',target_version='0.9.15',mesh_distance_fields=False,runtime_verified=False)
    write(out/'validation/unreal_import_receipt.json',receipt)
    print('INSTALLED',name,len(files),'assets; runtime validation still required',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['setup','build','install']);p.add_argument('--scene',default='014346');p.add_argument('--from-stage',choices=['import','move','prepare','cook'],default='import');a=p.parse_args()
    selected=list(IDS) if a.scene=='all' else a.scene.split(',')
    if a.command=='setup':setup()
    elif a.command=='install':
        for sid in selected:install(sid)
    elif len(selected)>1:
        if a.from_stage!='import':p.error('Batch resume is not supported; select a single scene to resume')
        build_many(selected)
    else:build(a.scene,a.from_stage)
