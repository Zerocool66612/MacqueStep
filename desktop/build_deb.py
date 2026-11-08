#!/usr/bin/env python3
"""Build a data-only Debian package using distro-provided Qt bindings."""
import argparse,shutil,subprocess,tempfile
from pathlib import Path
VERSION='0.23'
def build(output):
 source=Path(__file__).resolve().parent;output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='macaquestep-deb-') as tmp:
  root=Path(tmp);app=root/'usr/share/macaquestep-preview';app.mkdir(parents=True)
  for p in source.iterdir():
   if p.suffix in ('.py','.md','.txt','.sh','.svg'):shutil.copy2(p,app/p.name)
  shutil.copytree(source/'assets',app/'assets');control=root/'DEBIAN';control.mkdir()
  (control/'control').write_text('Package: macaquestep-preview\nVersion: '+VERSION+'\nSection: x11\nPriority: optional\nArchitecture: all\nMaintainer: Drew Owen\nDepends: python3 (>= 3.10), python3-pyside6.qtwidgets (>= 6.8), python3-pyside6.qtmultimedia (>= 6.8), python3-pyside6.qtmultimediawidgets (>= 6.8), python3-pyside6.qtsvg (>= 6.8), python3-pyside6.qtprintsupport (>= 6.8), python3-pyte, python3-yaml, qml6-module-qtquick, qml6-module-qtquick-window, qml6-module-qtquick-layouts, qml6-module-qtquick-controls, qml6-module-qtquick-templates, qml6-module-qtqml-workerscript\nRecommends: xdg-utils, libglib2.0-bin\nDescription: MacaqueSTEP desktop preview by Drew\n NeXT and Window Maker inspired desktop application with workspace Clip,\n launchers, terminal, files, organizer, sounds, and multiple themes.\n This package does not replace the host desktop or install a bootable OS.\n')
  binary=root/'usr/bin';binary.mkdir(parents=True);launcher=binary/'macaquestep-preview';launcher.write_text('#!/bin/sh\nexec /usr/bin/python3 /usr/share/macaquestep-preview/desktop.py "$@"\n');launcher.chmod(0o755)
  recovery=binary/'macaquestep-classic-menus';recovery.write_text('#!/bin/sh\nexec /usr/bin/python3 /usr/share/macaquestep-preview/desktop.py --classic-menus "$@"\n');recovery.chmod(0o755)
  integration=source.parent/'config/includes.chroot'
  for relative in ('usr/bin/macaquestep-install','usr/lib/macaquestep/installer-root','usr/share/polkit-1/actions/org.macaquestep.install.policy'):
   original=integration/relative
   if original.is_file():
    target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
  entries=root/'usr/share/applications';entries.mkdir(parents=True);(entries/'macaquestep-preview.desktop').write_text('[Desktop Entry]\nType=Application\nName=MacaqueSTEP Preview\nComment=Window Maker inspired desktop — Made by Drew\nExec=macaquestep-preview\nIcon=macaquestep-preview\nTerminal=false\nCategories=Utility;\nStartupNotify=true\n')
  (entries/'macaquestep-classic-menus.desktop').write_text('[Desktop Entry]\nType=Application\nName=MacaqueSTEP '+VERSION+' — Classic Menus\nComment=Show the embedded File and Edit menu strip\nExec=macaquestep-classic-menus\nIcon=macaquestep-preview\nTerminal=false\nCategories=Utility;\n')
  icons=root/'usr/share/icons/hicolor/scalable/apps';icons.mkdir(parents=True);shutil.copy2(source/'assets/monkey.svg',icons/'macaquestep-preview.svg')
  docs=root/'usr/share/doc/macaquestep-preview';docs.mkdir(parents=True);shutil.copy2(source/'README.md',docs/'README.md');(docs/'copyright').write_text('MacaqueSTEP — Made by Drew.\nOriginal project source and assets. No project-wide license has been specified.\nThird-party runtime dependencies are installed separately and retain their respective licenses.\n')
  subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(output)],check=True)
 return output
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(Path(__file__).resolve().parent.parent/'macaquestep-preview_0.23_all.deb'));args=parser.parse_args();print(build(args.output))
