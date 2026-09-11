"""Python 3.8-compatible entry point for research recipes written for Python 3.9+."""
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def indent(elem, space='  ', level=0):
    if isinstance(elem, ET.ElementTree): elem=elem.getroot()
    if len(elem):
        if not elem.text or not elem.text.strip(): elem.text='\n'+space*(level+1)
        for child in elem: indent(child, space, level+1)
        if not child.tail or not child.tail.strip(): child.tail='\n'+space*level
    if level and (not elem.tail or not elem.tail.strip()): elem.tail='\n'+space*level

if not hasattr(ET,'indent'): ET.indent=indent
path=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(path.parent))
runpy.run_path(str(path),run_name='__main__')
