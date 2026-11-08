#!/usr/bin/env python3
"""Apply MacaqueSTEP overrides to Debian's maintained installer configuration."""
from pathlib import Path
import yaml

def configure(root):
 root=Path(root).resolve()
 def path(relative):return root/relative.lstrip('/')
 branding=path('/etc/calamares/branding/macaquestep/branding.desc')
 data=yaml.safe_load(branding.read_text())
 if not data.get('slideshow'):raise ValueError('MacaqueSTEP installer branding requires slideshow')
 p=path('/etc/calamares/settings.conf');settings=yaml.safe_load(p.read_text());settings['branding']='macaquestep';settings['prompt-install']=True
 for phase in settings['sequence']:
  if 'exec' in phase:
   tasks=phase['exec']
   if 'macaquestep-cleanup' not in tasks:tasks.insert(tasks.index('displaymanager'),'macaquestep-cleanup')
 # Preserve Debian's bootloader/initramfs/APT ordering and helpers.
 p.write_text(yaml.safe_dump(settings,sort_keys=False))
 p=path('/etc/calamares/modules/displaymanager.conf');data=yaml.safe_load(p.read_text());data['displaymanagers']=['lightdm'];data['defaultDesktopEnvironment']={'executable':'/usr/bin/macaquestep-session','desktopFile':'macaquestep'};p.write_text(yaml.safe_dump(data,sort_keys=False))
 p=path('/etc/calamares/modules/welcome.conf');data=yaml.safe_load(p.read_text());requirements=data.setdefault('requirements',{});requirements['requiredStorage']=25;requirements['requiredRam']=2.0
 for key in ('check','required'):
  requirements[key]=list(dict.fromkeys(requirements.get(key,[])+['internet']))
 p.write_text(yaml.safe_dump(data,sort_keys=False))
 p=path('/etc/os-release');data=p.read_text();data='\n'.join('PRETTY_NAME="MacaqueSTEP 0.23 (Debian GNU/Linux 13)"' if line.startswith('PRETTY_NAME=') else line for line in data.splitlines())+'\n';p.write_text(data)
 path('/etc/issue').write_text('MacaqueSTEP 0.23 — Made by Drew\\n \\l\n')
if __name__=='__main__':
 import sys
 configure(sys.argv[1] if len(sys.argv)>1 else '/')
