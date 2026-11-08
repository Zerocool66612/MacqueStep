#!/usr/bin/env python3
"""Install/remove only this app's user-level menu entry."""
import os,sys
from pathlib import Path
folder=Path(__file__).resolve().parent
entry=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'applications'/'macaquestep-preview.desktop'
marker='X-MacaqueSTEP-Managed=true'
def quote(value):return '"'+str(value).replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')+'"'
if '--remove' in sys.argv:
 if entry.exists() and marker in entry.read_text():entry.unlink();print('Removed MacaqueSTEP menu launcher.')
 else:print('No managed launcher found.')
else:
 python=folder/'.venv/bin/python'
 if not python.exists():raise SystemExit('Run bash run.sh once first so the private Python environment is ready.')
 if entry.exists() and marker not in entry.read_text():raise SystemExit('A different launcher already uses this name; it was left unchanged.')
 entry.parent.mkdir(parents=True,exist_ok=True)
 entry.write_text('[Desktop Entry]\nType=Application\nName=MacaqueSTEP Preview\nComment=NeXT-inspired desktop preview\nExec='+quote(python)+' '+quote(folder/'desktop.py')+'\nIcon='+str(folder/'assets/monkey.svg')+'\nTerminal=false\nCategories=Utility;\n'+marker+'\n')
 print('Installed MacaqueSTEP Preview in your applications menu. Keep this folder in place.')
