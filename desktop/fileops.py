"""Cancellable staged copies and same-filesystem, no-overwrite moves."""
import os,shutil,tempfile,stat
from pathlib import Path
from PySide6.QtCore import QThread,Signal,QFile,QDir
class Cancelled(Exception):pass

def transfer_item(source,destination,move=False,cancel=lambda:False,progress=lambda n:None):
 src=Path(source);dst=Path(destination)
 if cancel():raise Cancelled('Canceled')
 if dst.exists() or dst.is_symlink():raise FileExistsError('Destination already exists: '+dst.name)
 if not src.exists() and not src.is_symlink():raise FileNotFoundError(str(src))
 if src.is_dir() and not src.is_symlink() and (dst.parent.resolve()==src.resolve() or src.resolve() in dst.parent.resolve().parents):raise ValueError('Cannot copy or move a folder into itself.')
 if move:
  if os.stat(src.parent).st_dev!=os.stat(dst.parent).st_dev:raise OSError('Cross-filesystem moves are unsupported; copy first. Source remains in place.')
  ok=QDir(str(src.parent)).rename(src.name,str(dst)) if src.is_dir() and not src.is_symlink() else QFile(str(src)).rename(str(dst))
  if not ok:raise OSError('Move failed. Cross-filesystem moves are unsupported; copy the item first. Source remains in place.')
  return
 if src.is_symlink():os.symlink(os.readlink(src),dst);return
 stage=Path(tempfile.mkdtemp(prefix='.macaquestep-copy-',dir=str(dst.parent)))
 payload=stage/'payload'
 def copy_file(a,b):
  if cancel():raise Cancelled('Canceled')
  if not stat.S_ISREG(os.stat(a).st_mode):raise ValueError('Special files cannot be copied.')
  with open(a,'rb') as reader,open(b,'xb') as writer:
   while True:
    if cancel():raise Cancelled('Canceled')
    block=reader.read(1024*1024)
    if not block:break
    writer.write(block);progress(len(block))
  shutil.copystat(a,b);return str(b)
 try:
  if src.is_dir():shutil.copytree(src,payload,symlinks=True,copy_function=copy_file)
  else:copy_file(src,payload)
  if cancel():raise Cancelled('Canceled')
  # Qt rename refuses an existing destination; publish only after copying completes.
  ok=QDir(str(stage)).rename('payload',str(dst)) if payload.is_dir() else QFile(str(payload)).rename(str(dst))
  if not ok:raise OSError('Could not publish copy; destination may already exist.')
 finally:shutil.rmtree(stage,ignore_errors=True)
class TransferJob(QThread):
 progress=Signal(str,int);completed=Signal(list,list,bool)
 def __init__(self,sources,folder,move=False,parent=None):super().__init__(parent);self.sources=list(sources);self.folder=Path(folder);self.move=move;self.bytes=0
 def run(self):
  successes=[];errors=[];canceled=False
  for source in self.sources:
   if self.isInterruptionRequested():canceled=True;break
   try:
    def report(n):self.bytes+=n;self.progress.emit(Path(source).name,self.bytes)
    transfer_item(source,self.folder/Path(source).name,self.move,self.isInterruptionRequested,report);successes.append(str(source));self.progress.emit(Path(source).name,self.bytes)
   except Cancelled:canceled=True;break
   except Exception as e:errors.append(Path(source).name+': '+str(e))
  self.completed.emit(successes,errors,canceled)
