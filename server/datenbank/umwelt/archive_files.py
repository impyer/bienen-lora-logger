# SPDX-License-Identifier: GPL-3.0-or-later
"""Narrow, nonrecursive, read-only source discovery; never follow symlinks."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import stat
import time

from .ingest import SourceReadError
from .parser import MAX_RECORD_BYTES

MAX_FILES = 240
MAX_FILE_BYTES = 512 * 1024 * 1024
FILE_SECONDS = 300


def compile_pattern(pattern):
    if not isinstance(pattern,str) or len(pattern)>120 or pattern.count('{YYYY}')!=1 or pattern.count('{MM}')!=1:
        raise ValueError('Archivmuster benötigt genau {YYYY} und {MM}')
    plain = pattern.replace('{YYYY}','').replace('{MM}','')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',plain) or '..' in plain:
        raise ValueError('Archivmuster enthält unzulässige Zeichen')
    return re.compile(re.escape(pattern).replace(r'\{YYYY\}',r'[0-9]{4}').replace(r'\{MM\}',r'(?:0[1-9]|1[0-2])')+r'\Z')


@contextmanager
def directory(path):
    """Walk every absolute path component with O_NOFOLLOW, including parents."""
    absolute = Path(path).absolute()
    descriptor = os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in absolute.parts[1:]:
            if part in {'.','..'}:
                raise SourceReadError('quellpfad_unzulaessig')
            child = os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=descriptor)
            os.close(descriptor); descriptor=child
        yield descriptor
    except OSError as exc:
        raise SourceReadError('quellverzeichnis_nicht_lesbar_oder_symlink') from exc
    finally:
        os.close(descriptor)


def names(descriptor,pattern):
    matcher = compile_pattern(pattern)
    found = []
    # scandir is lazy: unrelated directory entries are not accumulated.
    with os.scandir(descriptor) as entries:
        inspected = 0
        for entry in entries:
            inspected += 1
            if inspected>10000:
                raise SourceReadError('staging_ueber_10000_eintraege')
            if matcher.fullmatch(entry.name):
                if not entry.is_file(follow_symlinks=False):
                    raise SourceReadError('archiv_ist_symlink_oder_spezialdatei')
                found.append(entry.name)
                if len(found)>MAX_FILES:
                    raise SourceReadError('archiv_ueber_240_dateien')
    return sorted(found)


def identity(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


@contextmanager
def read_file(descriptor,name):
    try:
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=descriptor)
        with os.fdopen(fd,'rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise SourceReadError('quelle_keine_regulaere_datei')
            if info.st_size>MAX_FILE_BYTES:
                raise SourceReadError('quelle_ueber_512_mib')
            yield stream,info
            current=os.stat(name,dir_fd=descriptor,follow_symlinks=False)
            if identity(info)!=identity(os.fstat(stream.fileno())) or identity(info)!=identity(current):
                raise SourceReadError('quelle_waehrend_lesen_geaendert')
    except OSError as exc:
        raise SourceReadError('quelle_nicht_lesbar') from exc


def hash_prefix(stream,size,deadline):
    stream.seek(0); digest=hashlib.sha256(); remaining=size
    while remaining:
        if time.monotonic()>deadline:
            raise SourceReadError('dateizeitbudget_300_s')
        data=stream.read(min(65536,remaining))
        if not data:
            raise SourceReadError('quelle_waehrend_lesen_geaendert')
        digest.update(data);remaining-=len(data)
    return digest.hexdigest()


class Lines:
    def __init__(self,stream,offset,line,deadline):
        self.stream=stream;stream.seek(offset)
        self.offset=offset;self.line=line;self.partial=False;self.deadline=deadline
    def __iter__(self):return self
    def __next__(self):
        if time.monotonic()>self.deadline:
            raise SourceReadError('dateizeitbudget_300_s')
        data=self.stream.readline(MAX_RECORD_BYTES+1)
        if not data:raise StopIteration
        if len(data)>MAX_RECORD_BYTES:
            raise SourceReadError('csv_record_ueber_64_kib')
        if not data.endswith(b'\n'):
            self.partial=True;raise StopIteration
        try:text=data.decode('utf-8')
        except UnicodeError as exc:raise SourceReadError('csv_nicht_utf8') from exc
        self.offset=self.stream.tell();self.line+=1
        return text
