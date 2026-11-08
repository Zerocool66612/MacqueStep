import os,shutil,configparser
from pathlib import Path
from PySide6.QtCore import Qt,QProcess
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *
def application_entries(roots=None):
 if roots is None:roots=[Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'applications',Path.home()/'.local/share/flatpak/exports/share/applications',Path('/var/lib/flatpak/exports/share/applications')]+[Path(path)/'applications' for path in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if path]
 seen=set();entries=[]
 for root in roots:
  if not Path(root).is_dir():continue
  for path in sorted(Path(root).rglob('*.desktop')):
   identifier=str(path.relative_to(root)).replace('/','-')
   if identifier in seen:continue
   seen.add(identifier)
   try:
    parser=configparser.ConfigParser(interpolation=None,strict=False);parser.read(path,encoding='utf-8');data=parser['Desktop Entry']
    if data.get('Type')!='Application' or data.get('Hidden','false').lower()=='true' or data.get('NoDisplay','false').lower()=='true':continue
    if data.get('TryExec') and not shutil.which(data['TryExec']):continue
    if not data.get('Exec') or not data.get('Name'):continue
    entries.append({'name':data['Name'],'comment':data.get('Comment',''),'icon':data.get('Icon',''),'path':str(path)})
   except (OSError,UnicodeError,configparser.Error,KeyError):continue
 return sorted(entries,key=lambda entry:entry['name'].casefold())
def launch_application(parent, path):
 gio=shutil.which('gio')
 if not gio:
  QMessageBox.warning(parent,'Launch application','The desktop-entry launcher (gio) is missing.');return False
 result=QProcess.startDetached(gio,['launch',str(path)])
 started=result[0] if isinstance(result,tuple) else bool(result)
 if not started:
  QMessageBox.warning(parent,'Launch application','The application could not be started.');return False
 # Native windows must remain visible above the desktop preview.
 window=QWidget.window(parent)
 if window.isFullScreen():window.showNormal();window.showMaximized()
 return True
class HostApps(QWidget):
 def __init__(self):
  super().__init__();v=QVBoxLayout(self);notice=QLabel('Installed applications open in separate windows.\nDouble-click an application to launch it.');notice.setWordWrap(True);v.addWidget(notice);self.search=QLineEdit();self.search.setPlaceholderText('Search installed applications…');v.addWidget(self.search);self.items=QListWidget();v.addWidget(self.items,1);self.status=QLabel();v.addWidget(self.status);refresh=QPushButton('Refresh installed apps');refresh.clicked.connect(self.refresh);v.addWidget(refresh);self.search.textChanged.connect(self.filter);self.items.itemActivated.connect(self.launch);self.refresh()
 def refresh(self):
  self.items.clear();self.entries=application_entries()
  for entry in self.entries:
   icon=QIcon(entry['icon']) if entry['icon'].startswith('/') else QIcon.fromTheme(entry['icon']);item=QListWidgetItem(icon,entry['name']);item.setToolTip(entry['comment']);item.setData(Qt.UserRole,entry['path']);self.items.addItem(item)
  self.status.setText(f'{len(self.entries)} installed applications'+(' • gio is unavailable; launching disabled' if not shutil.which('gio') else ''));self.filter(self.search.text())
 def filter(self,text):
  for i in range(self.items.count()):item=self.items.item(i);item.setHidden(text.casefold() not in (item.text()+' '+item.toolTip()).casefold())
 def launch(self,item):
  launch_application(self,item.data(Qt.UserRole))
