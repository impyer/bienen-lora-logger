# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit local file inventory, read-only, without raw payload/path output."""
from pathlib import Path
import time

from .archive_files import directory,names,read_file,hash_prefix,Lines,FILE_SECONDS
from .parser import parse_stream,CsvHeader,Issue


def inspect_config(config):
    path=config['path'];pattern=config.get('pattern');reports=[]
    root=path if pattern else str(Path(path).parent)
    with directory(root) as descriptor:
        selected=names(descriptor,pattern) if pattern else [Path(path).name]
        for number,name in enumerate(selected,1):
            with read_file(descriptor,name) as (stream,before):
                deadline=time.monotonic()+FILE_SECONDS
                lines=Lines(stream,0,0,deadline);count=0;errors=0;first=None;last=None;fields=[]
                for item in parse_stream(lines,config['profile'],expected_stand=config['source_stand'],expected_device=config['source_device']):
                    if isinstance(item,CsvHeader):fields=list(item.fields)
                    elif isinstance(item,Issue):errors+=1
                    else:
                        count+=1;first=min(first,item.time) if first else item.time;last=max(last,item.time) if last else item.time
                reports.append(dict(file_number=number,bytes=before.st_size,records=count,issues=errors,
                    partial_tail=lines.partial,fields=fields,first=first.isoformat() if first else None,
                    last=last.isoformat() if last else None,sha256=hash_prefix(stream,before.st_size,deadline)))
    return {'files':len(reports),'details':reports,'read_only':True,'identities':'Nur Konfigurationsabgleich; DB-IDs separat mit inventory prüfen'}
