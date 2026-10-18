# SPDX-License-Identifier: GPL-3.0-or-later
"""Opt-in synthetic staging publisher. No receiver writes or network access."""
import fcntl
import json
import os
from pathlib import Path
import secrets
import stat
import time
from datetime import datetime,timezone

from .archive_files import directory,names,read_file,hash_prefix,Lines,FILE_SECONDS
from .parser import parse_stream,Issue,SourceFormatError
from .ingest import SourceReadError


def _private_file(descriptor,name,flags):
    fd=os.open(name,flags|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=descriptor)
    info=os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1:
        os.close(fd);raise SourceReadError('sync_statusdatei_unzulaessig')
    return fd


def _audit(descriptor,event):
    fd=_private_file(descriptor,'.bienen-sync.jsonl',os.O_WRONLY|os.O_APPEND)
    with os.fdopen(fd,'a',encoding='utf-8') as log:
        log.write(json.dumps(dict(event,utc=datetime.now(timezone.utc).isoformat()),ensure_ascii=False)+'\n')
        log.flush();os.fsync(log.fileno())


def _publish(source_fd,target_fd,name,config):
    temporary='.bienen-sync-'+secrets.token_hex(12)+'.part'
    created=False
    try:
        with read_file(source_fd,name) as (source,info):
            deadline=time.monotonic()+FILE_SECONDS
            digest=hash_prefix(source,info.st_size,deadline)
            try:
                with read_file(target_fd,name) as (existing,target_info):
                    if hash_prefix(existing,target_info.st_size,deadline)==digest:
                        event=dict(file=name,status='unchanged',sha256=digest,bytes=info.st_size)
                        # Still verify source identity on leaving read_file.
                        unchanged=event
                    else:unchanged=None
            except SourceReadError:
                # Only ENOENT is acceptable; symlinks/permissions/special files
                # are diagnosed by the no-follow stat below and never replaced.
                try:os.stat(name,dir_fd=target_fd,follow_symlinks=False)
                except FileNotFoundError:unchanged=None
                else:raise
            if unchanged is None:
                fd=os.open(temporary,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o640,dir_fd=target_fd)
                created=True
                with os.fdopen(fd,'w+b') as copy:
                    source.seek(0);remaining=info.st_size
                    while remaining:
                        if time.monotonic()>deadline:raise SourceReadError('sync_zeitbudget')
                        chunk=source.read(min(65536,remaining))
                        if not chunk:raise SourceReadError('sync_quelle_verkuerzt')
                        copy.write(chunk);remaining-=len(chunk)
                    copy.flush();copy.seek(0)
                    lines=Lines(copy,0,0,deadline)
                    for item in parse_stream(lines,config['profile'],expected_stand=config['source_stand'],expected_device=config['source_device']):
                        if isinstance(item,Issue):raise SourceFormatError('sync_csv_unvollstaendig_oder_ungueltig')
                    if lines.partial:raise SourceFormatError('sync_partielles_ende')
                    if hash_prefix(copy,info.st_size,deadline)!=digest:raise SourceReadError('sync_hash_abweichung')
                    os.fsync(copy.fileno())
        # Source stat/inode verification has succeeded before any publication.
        if unchanged is not None:
            _audit(target_fd,unchanged);return unchanged
        event=dict(file=name,sha256=digest,bytes=info.st_size)
        _audit(target_fd,dict(event,status='prepared'))
        os.replace(temporary,name,src_dir_fd=target_fd,dst_dir_fd=target_fd)
        created=False;os.fsync(target_fd)
        result=dict(event,status='published');_audit(target_fd,result)
        return result
    finally:
        if created:os.unlink(temporary,dir_fd=target_fd)


def sync_synthetic(config):
    """Requires explicit declaration and synthetic identities, existing separate roots."""
    if config.get('synthetic') is not True or config.get('source_stand')!='synthetic' or not config.get('source_device','').startswith('synthetic-'):
        raise ValueError('Synchronisierung ausschließlich für deklarierte synthetische Testquellen')
    source=Path(config['source']).absolute();target=Path(config['staging']).absolute()
    if source==target or source in target.parents or target in source.parents:
        raise ValueError('Quelle und Staging müssen getrennte Verzeichnisse sein')
    with directory(source) as source_fd,directory(target) as target_fd:
        if (os.fstat(source_fd).st_dev,os.fstat(source_fd).st_ino)==(os.fstat(target_fd).st_dev,os.fstat(target_fd).st_ino):
            raise ValueError('Quelle und Staging dürfen nicht dieselbe Verzeichnisidentität haben')
        lock=_private_file(target_fd,'.bienen-sync.lock',os.O_RDWR)
        try:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise SourceReadError('sync_bereits_aktiv') from None
            try:selected=names(source_fd,config['pattern'])
            except (OSError,SourceReadError):
                _audit(target_fd,dict(status='scan_failed',code='sync_quellauswahl_abgewiesen'));raise
            if not selected:raise SourceReadError('sync_keine_dateien')
            result=[]
            for name in selected:
                try:result.append(_publish(source_fd,target_fd,name,config))
                except (OSError,SourceReadError,SourceFormatError):
                    event=dict(file=name,status='failed',code='sync_datei_abgewiesen')
                    _audit(target_fd,event);result.append(event)
            return {'synthetic':True,'success':all(e['status']!='failed' for e in result),'files':result}
        finally:os.close(lock)
