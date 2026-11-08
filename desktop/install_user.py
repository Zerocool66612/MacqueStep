#!/usr/bin/env python3
"""Reversible per-user installation with an isolated runtime and atomic activation."""
import argparse,json,os,shlex,shutil,subprocess,sys,uuid
from pathlib import Path
VERSION='0.23'
MARKER='MacaqueSTEP user installer v1'
def paths(prefix):
 data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
 return Path(prefix).expanduser().absolute(),Path.home()/'.local/bin/macaquestep-preview',data/'applications/macaquestep-preview.desktop'
def desktop_quote(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')+'"'
def install(prefix,system_python=False):
 root,wrapper,entry=paths(prefix);recovery=wrapper.with_name('macaquestep-classic-menus');recovery_entry=entry.with_name('macaquestep-classic-menus.desktop');source=Path(__file__).resolve().parent;marker=root/'.macaquestep-install'
 if root.is_symlink():raise ValueError('Installation prefix must not be a symlink.')
 if root.exists() and any(root.iterdir()) and (not marker.is_file() or marker.read_text()!=MARKER):raise ValueError('Choose an empty installation directory or an existing managed MacaqueSTEP installation.')
 wrapper_tag='# '+MARKER+' '+str(root)
 for executable in (wrapper,recovery):
  if executable.exists() and wrapper_tag not in executable.read_text():raise ValueError('An unmanaged launcher already exists: '+str(executable))
 entry_tag='X-MacaqueSTEP-UserInstall='+str(root)
 if entry.exists() and entry_tag not in entry.read_text():
  if 'X-MacaqueSTEP-Managed=true' not in entry.read_text():raise ValueError('An unmanaged menu entry already exists: '+str(entry))
 if recovery_entry.exists() and entry_tag not in recovery_entry.read_text():raise ValueError('An unmanaged menu entry already exists: '+str(recovery_entry))
 # Check supported runtime before changing the active launcher.
 root.mkdir(parents=True,exist_ok=True);releases=root/'releases';releases.mkdir(exist_ok=True);release=releases/(VERSION+'-'+uuid.uuid4().hex[:12]);release.mkdir()
 try:
  for p in source.iterdir():
   if p.suffix in ('.py','.md','.txt','.sh','.svg'):shutil.copy2(p,release/p.name)
  shutil.copytree(source/'assets',release/'assets')
  if system_python:python=Path(sys.executable).absolute()
  else:
   subprocess.run([sys.executable,'-m','venv',str(release/'.venv')],check=True);python=release/'.venv/bin/python';subprocess.run([str(python),'-m','pip','install','-r',str(release/'requirements.txt')],check=True)
  check='import PySide6,pyte; from PySide6 import QtWidgets,QtMultimedia,QtMultimediaWidgets,QtSvg,QtPrintSupport; assert tuple(map(int,PySide6.__version__.split(".")[:2])) >= (6,8)'
  subprocess.run([str(python),'-c',check],check=True)
  (release/'.macaquestep-release').write_text(MARKER);(release/'start').write_text('#!/bin/sh\nexec '+shlex.quote(str(python))+' '+shlex.quote(str(release/'desktop.py'))+' "$@"\n');(release/'start').chmod(0o755)
  temporary=root/('current-'+uuid.uuid4().hex);temporary.symlink_to(release.relative_to(root));temporary.replace(root/'current');marker.write_text(MARKER)
  wrapper.parent.mkdir(parents=True,exist_ok=True);wrapper.write_text('#!/bin/sh\n'+wrapper_tag+'\nexec '+shlex.quote(str(root/'current/start'))+' "$@"\n');wrapper.chmod(0o755)
  recovery.write_text('#!/bin/sh\n'+wrapper_tag+'\nexec '+shlex.quote(str(root/'current/start'))+' --classic-menus "$@"\n');recovery.chmod(0o755)
  entry.parent.mkdir(parents=True,exist_ok=True);entry.write_text('[Desktop Entry]\nType=Application\nName=MacaqueSTEP Preview\nComment=Window Maker inspired desktop — Made by Drew\nExec='+desktop_quote(wrapper)+'\nIcon='+str(root/'current/assets/monkey.svg')+'\nTerminal=false\nCategories=Utility;\n'+entry_tag+'\n')
  recovery_entry.write_text('[Desktop Entry]\nType=Application\nName=MacaqueSTEP '+VERSION+' — Classic Menus\nComment=Show the embedded File and Edit menu strip\nExec='+desktop_quote(recovery)+'\nIcon='+str(root/'current/assets/monkey.svg')+'\nTerminal=false\nCategories=Utility;\n'+entry_tag+'\n')
 except Exception:
  # A failed runtime preparation cannot replace a previously working current link.
  if not (root/'current').is_symlink() or (root/'current').resolve()!=release:shutil.rmtree(release)
  raise
 print('Installed MacaqueSTEP '+VERSION+'. Open MacaqueSTEP Preview from your applications menu.\nLauncher: '+str(wrapper))
def uninstall(prefix):
 root,wrapper,entry=paths(prefix);marker=root/'.macaquestep-install'
 if root.is_symlink() or not marker.is_file() or marker.read_text()!=MARKER:raise ValueError('No managed user installation at this prefix.')
 for executable in (wrapper,wrapper.with_name('macaquestep-classic-menus')):
  if executable.is_file() and '# '+MARKER+' '+str(root) in executable.read_text():executable.unlink()
 for item in (entry,entry.with_name('macaquestep-classic-menus.desktop')):
  if item.is_file() and 'X-MacaqueSTEP-UserInstall='+str(root) in item.read_text():item.unlink()
 current=root/'current'
 if current.is_symlink() and current.resolve().is_relative_to(root/'releases'):current.unlink()
 releases=root/'releases'
 if releases.is_dir():
  for release in releases.iterdir():
   if not release.is_symlink() and release.is_dir() and (release/'.macaquestep-release').is_file() and (release/'.macaquestep-release').read_text()==MARKER:shutil.rmtree(release)
  try:releases.rmdir()
  except OSError:pass
 marker.unlink()
 try:root.rmdir()
 except OSError:pass
 print('Removed the managed user installation. Notes, tasks, and preferences were kept.')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prefix',default=str(Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'macaquestep-preview'));parser.add_argument('--use-system-python',action='store_true',help='Use the current interpreter only when supported dependencies are already installed.');parser.add_argument('--uninstall',action='store_true');args=parser.parse_args()
 try:uninstall(args.prefix) if args.uninstall else install(args.prefix,args.use_system_python)
 except (ValueError,OSError,subprocess.CalledProcessError) as error:raise SystemExit('Installation failed: '+str(error))
