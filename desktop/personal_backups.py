"""Portable volume backups; recovery writes to a fresh folder, never overwrites."""
import json,os,stat,time,zipfile,shutil,tempfile
from pathlib import Path,PurePosixPath
from PySide6.QtCore import QThread,Signal
from PySide6.QtWidgets import *
LIMIT=250*1024*1024
COUNT=10000

def create_backup(root,state,destination,exclude_hidden=False):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('A file already exists there. Choose a new backup filename.')
    if destination.is_relative_to(root):raise ValueError('Save the backup outside Personal Files so it cannot include itself.')
    entries=[];total=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[n for n in dirs if not (Path(parent)/n).is_symlink() and (not exclude_hidden or not n.startswith('.'))]
        for name in files:
            p=Path(parent)/name
            if p.is_symlink() or (exclude_hidden and name.startswith('.')):continue
            if not p.resolve().is_relative_to(root):raise ValueError('A file moved outside the volume during backup.')
            metadata=p.stat()
            if not stat.S_ISREG(metadata.st_mode):continue
            size=metadata.st_size;total+=size;entries.append(p)
            if total>LIMIT or len(entries)>COUNT:raise ValueError('This backup tool supports up to 250 MB and 10,000 files.')
    fd,temp=tempfile.mkstemp(prefix='.macaque-backup-',dir=destination.parent);os.close(fd)
    try:
        with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('backup-info.json',json.dumps({'format':'macaquestep-personal-backup','version':1,'time':time.time()}));z.writestr('desktop-state.json',json.dumps(state,indent=2))
            # Store directories too, including empty user folders and app aliases.
            for parent,dirs,files in os.walk(root,followlinks=False):
                dirs[:]=[n for n in dirs if not (Path(parent)/n).is_symlink() and (not exclude_hidden or not n.startswith('.'))]
                for name in dirs:
                    p=Path(parent)/name;z.writestr('Personal Files/'+p.relative_to(root).as_posix()+'/',b'')
            for p in entries:z.write(p,'Personal Files/'+p.relative_to(root).as_posix())
        with zipfile.ZipFile(temp) as check:
            if len(check.infolist())>COUNT+2000 or sum(e.file_size for e in check.infolist())>LIMIT:raise ValueError('Backup exceeds the supported size/entry limit.')
        # Exclusive creation preserves old backups on Linux and removable drives.
        fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as output,open(temp,'rb') as source:shutil.copyfileobj(source,output)
        except Exception:destination.unlink(missing_ok=True);raise
    finally:Path(temp).unlink(missing_ok=True)
    return str(destination)

def recover_backup(archive,parent):
    parent=Path(parent).resolve();parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist();total=0;seen=set()
        if len(entries)>COUNT+2000:raise ValueError('Too many backup entries.')
        for entry in entries:
            name=entry.filename;parts=PurePosixPath(name).parts
            if name.startswith('/') or '\\' in name or any(p in ('.','..') for p in parts) or ':' in name:raise ValueError('Unsafe backup path.')
            if not (name in ('backup-info.json','desktop-state.json') or parts and parts[0]=='Personal Files'):raise ValueError('Unexpected backup entry.')
            if name in seen or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Duplicate or symbolic-link backup entry.')
            seen.add(name);total+=entry.file_size
            if total>LIMIT:raise ValueError('Backup expands beyond the 250 MB recovery limit.')
        if z.getinfo('backup-info.json').file_size>65536:raise ValueError('Backup metadata is too large.')
        info=json.loads(z.read('backup-info.json'))
        if info.get('format')!='macaquestep-personal-backup' or info.get('version')!=1:raise ValueError('This is not a supported MacaqueSTEP backup.')
        destination=Path(tempfile.mkdtemp(prefix='Recovered-',dir=parent))
        try:
            for entry in entries:
                target=destination/entry.filename
                if not target.resolve().is_relative_to(destination):raise ValueError('Unsafe recovery destination.')
                if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(entry) as source,target.open('xb') as output:
                    written=0
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        written+=len(block)
                        if written>entry.file_size or written>LIMIT:raise ValueError('Invalid expanded file size.')
                        output.write(block)
        except Exception:shutil.rmtree(destination);raise
    return str(destination)

class BackupWorker(QThread):
    done=Signal(str);failed=Signal(str)
    def __init__(self,fn,args,parent):super().__init__(parent);self.fn=fn;self.args=args
    def run(self):
        try:self.done.emit(self.fn(*self.args))
        except Exception as ex:self.failed.emit(str(ex))
