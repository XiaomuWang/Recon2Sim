"""Rename only FBX object/material name strings, preserving all geometry bytes.

The CARLA 0.9.12 preparation commandlet drops meshes whose names or material
names contain 'light' or 'sign'. Equal-length aliases avoid this legacy filter.
The reserved '_Tile_' marker also misclassifies ordinary paving as a tiled map.
"""
import re
import struct
from pathlib import Path
from .common import sha,write


def prepare(source,destination):
    source=Path(source);destination=Path(destination)
    original=source.read_bytes();data=bytearray(original)
    if not original.startswith(b'Kaydara FBX Binary  \x00\x1a\x00'):
        raise ValueError('Binary FBX required')
    version=struct.unpack_from('<I',data,23)[0]
    fmt='<QQQB' if version>=7500 else '<IIIB';header=struct.calcsize(fmt)
    changes=[];mesh_names=[]
    def visit(offset):
        end,count,propbytes,namelen=struct.unpack_from(fmt,data,offset)
        if end==0:return None
        if end>len(data) or end<=offset:raise ValueError('Invalid FBX node offset')
        node=bytes(data[offset+header:offset+header+namelen]);pos=offset+header+namelen
        values=[]
        for index in range(count):
            kind=chr(data[pos]);pos+=1;value=None
            if kind in 'SR':
                length=struct.unpack_from('<I',data,pos)[0];pos+=4
                value=bytes(data[pos:pos+length])
                if kind=='S' and index==1 and node in [b'Model',b'Geometry',b'Material']:
                    replaced=re.sub(b'light',b'lumen',value,flags=re.I)
                    replaced=re.sub(b'sign',b'bord',replaced,flags=re.I)
                    replaced=re.sub(b'_tile_',b'_Pave_',replaced,flags=re.I)
                    if replaced!=value:
                        assert len(replaced)==length
                        data[pos:pos+length]=replaced
                        changes.append(dict(node=node.decode(),old=value.split(b'\0')[0].decode('utf-8'),
                                            new=replaced.split(b'\0')[0].decode('utf-8'),offset=pos,length=length))
                        value=replaced
                pos+=length
            elif kind in 'fdlibc':
                length,encoding,compressed=struct.unpack_from('<III',data,pos);pos+=12+compressed
            else:
                sizes={'Y':2,'C':1,'I':4,'F':4,'D':8,'L':8}
                if kind not in sizes:raise ValueError('Unknown FBX property '+kind)
                pos+=sizes[kind]
            values.append(value)
        if pos!=offset+header+namelen+propbytes:raise ValueError('FBX property boundary mismatch')
        if node==b'Model' and len(values)>2 and values[2]==b'Mesh':
            mesh_names.append(values[1].split(b'\0')[0].decode('utf-8'))
        while pos<end:
            child=visit(pos)
            if child is None:break
            pos=child
        return end
    pos=27
    while pos<len(data)-header:
        end=visit(pos)
        if end is None:break
        pos=end
    restored=bytearray(data)
    for c in changes:restored[c['offset']:c['offset']+c['length']]=original[c['offset']:c['offset']+c['length']]
    if restored!=original:raise AssertionError('Unexpected change outside FBX names')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    result=dict(source=str(source),prepared=str(destination),source_sha256=sha(source),prepared_sha256=sha(destination),
                version=version,renames=changes,mesh_names=mesh_names,mesh_count=len(mesh_names),
                geometry_and_all_non_name_bytes_identical=True)
    write(destination.with_suffix('.names.json'),result)
    return result
