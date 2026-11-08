#!/usr/bin/env python3
"""Private JSON/PTY bridge. The GUI never forks after initializing Qt."""
import os,sys,pty,select,json,base64,fcntl,termios,struct,signal,shutil

def main():
 pid,fd=pty.fork()
 if pid==0:
  os.environ['TERM']='xterm';os.environ['COLORTERM']='truecolor'
  shell=os.environ.get('SHELL','/bin/sh');shell=shutil.which(shell) or '/bin/sh'
  os.chdir(os.path.expanduser('~'));os.execv(shell,[shell,'-i']);os._exit(127)
 def send(value):sys.stdout.write(json.dumps(value)+'\n');sys.stdout.flush()
 buffer=b'';alive=True
 try:
  while alive:
   reads,_,_=select.select([fd,sys.stdin.fileno()],[],[],.1)
   if fd in reads:
    try:data=os.read(fd,65536)
    except OSError:data=b''
    if not data:break
    send({'data':base64.b64encode(data).decode('ascii')})
   if sys.stdin.fileno() in reads:
    chunk=os.read(sys.stdin.fileno(),65536)
    if not chunk:break
    buffer+=chunk
    while b'\n' in buffer:
     line,buffer=buffer.split(b'\n',1)
     try:
      message=json.loads(line)
      if 'write' in message:os.write(fd,base64.b64decode(message['write']))
      if 'resize' in message:
       rows,cols=message['resize'];fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',max(2,min(200,rows)),max(10,min(400,cols)),0,0))
      if message.get('close'):alive=False;break
     except (ValueError,KeyError,TypeError,OSError):pass
   done,status=os.waitpid(pid,os.WNOHANG)
   if done:pid=None;break
 except (BrokenPipeError,OSError):pass
 finally:
  if pid:
   try:
    foreground=os.tcgetpgrp(fd)
    if foreground!=pid:os.killpg(foreground,signal.SIGHUP)
   except OSError:pass
   try:os.killpg(pid,signal.SIGHUP)
   except OSError:pass
  os.close(fd)
  if pid:
   # Ensure children are reaped even when their shell ignores hangup.
   import time
   for _ in range(10):
    try:
     if os.waitpid(pid,os.WNOHANG)[0]:pid=None;break
    except ChildProcessError:pid=None;break
    time.sleep(.02)
   if pid:
    try:os.killpg(pid,signal.SIGKILL)
    except OSError:pass
    try:os.waitpid(pid,0)
    except ChildProcessError:pass
if __name__=='__main__':main()
