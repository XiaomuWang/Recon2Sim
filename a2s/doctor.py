"""Read-only local dependency/server check. Does not load or replace a CARLA world."""
import importlib
import sys
from datetime import datetime,timezone
from .common import PROJECT,write
from .pipeline import blender_exe


def main():
    report=dict(checked_at=datetime.now(timezone.utc).isoformat(),python=sys.version,dependencies={})
    for name in ['numpy','scipy','cv2','PIL','lxml','carla']:
        try:
            module=importlib.import_module(name);report['dependencies'][name]=dict(available=True,version=getattr(module,'__version__','available'))
        except ImportError as e: report['dependencies'][name]=dict(available=False,error=str(e))
    try:report['blender_executable']=str(blender_exe())
    except RuntimeError as e:report['blender_error']=str(e)
    try:
        import carla
        c=carla.Client('localhost',2000);c.set_timeout(2)
        report['carla_server']=dict(connected=True,version=c.get_server_version(),available_maps=c.get_available_maps())
    except Exception as e:report['carla_server']=dict(connected=False,host='localhost',port=2000,error=str(e))
    write(PROJECT/'outputs/environment_check.json',report)
    print(report['carla_server'],flush=True)

if __name__=='__main__':main()
