import os,platform
from pathlib import Path
from PySide6.QtCore import Qt,QStorageInfo
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import *
from foundation import icon
VERSION='0.23'
def hardware_summary():
 cpu=platform.processor() or platform.machine()
 try:
  for line in Path('/proc/cpuinfo').read_text().splitlines():
   if line.startswith('model name'):cpu=line.split(':',1)[1].strip();break
 except OSError:pass
 try:memory=f'{os.sysconf("SC_PHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")/1024**3:.1f} GB'
 except (OSError,ValueError,AttributeError):memory='Not reported'
 return {'Processor':cpu,'CPU threads':str(os.cpu_count() or 'Not reported'),'Memory':memory,'Architecture':platform.machine(),'Host system':platform.system()+' '+platform.release(),'Computer name':platform.node()}
class About(QWidget):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;v=QVBoxLayout(self);self.tabs=QTabWidget();v.addWidget(self.tabs,1)
  overview=QWidget();overview.setObjectName('aboutPage');row=QHBoxLayout(overview);picture=QLabel();picture.setObjectName('aboutLogo');picture.setPixmap(icon('monkey').pixmap(104,104));picture.setAlignment(Qt.AlignTop);row.addWidget(picture);details=QVBoxLayout();heading=QLabel('MacaqueSTEP');heading.setStyleSheet('font-size:28px;font-weight:700');details.addWidget(heading);details.addWidget(QLabel('Version '+VERSION+' • Desktop Preview'));credit=QLabel('Made by Drew');credit.setStyleSheet('font-size:16px;font-weight:600');details.addWidget(credit);details.addWidget(QLabel('A classic desktop. A new beginning.'));form=QFormLayout()
  for key,value in hardware_summary().items():label=QLabel(value);label.setWordWrap(True);label.setTextInteractionFlags(Qt.TextSelectableByMouse);form.addRow(key,label)
  details.addLayout(form);details.addStretch();row.addLayout(details,1);self.tabs.addTab(overview,'Overview')
  displays=QWidget();displays.setObjectName('aboutPage');layout=QVBoxLayout(displays);self.display_list=QPlainTextEdit();self.display_list.setReadOnly(True);layout.addWidget(self.display_list);refresh=QPushButton('Refresh displays');refresh.clicked.connect(self.refresh_displays);layout.addWidget(refresh);self.tabs.addTab(displays,'Displays')
  storage=QWidget();storage.setObjectName('aboutPage');layout=QVBoxLayout(storage);self.volumes=QTreeWidget();self.volumes.setHeaderLabels(['Volume / location','Capacity','Available','Access']);self.volumes.setColumnWidth(0,290);layout.addWidget(self.volumes,1);buttons=QHBoxLayout();refresh=QPushButton('Refresh storage');refresh.clicked.connect(self.refresh_storage);open_button=QPushButton('Open selected location');open_button.clicked.connect(self.open_volume);buttons.addWidget(refresh);buttons.addWidget(open_button);layout.addLayout(buttons);self.tabs.addTab(storage,'Storage')
  support=QWidget();support.setObjectName('aboutPage');layout=QVBoxLayout(support);description=QLabel('MacaqueSTEP is currently a desktop preview on your host operating system.\nUse these tools for help, diagnostics, backups, and project status.');description.setWordWrap(True);layout.addWidget(description)
  for title,fn in [('MacaqueSTEP Help',desktop.help_center),('System Report',desktop.system_info),('Backups & Restore',desktop.backups),('Project Status & OS Readiness',desktop.project_status)]:button=QPushButton(title);button.clicked.connect(fn);layout.addWidget(button)
  layout.addStretch();self.tabs.addTab(support,'Support');footer=QHBoxLayout()
  for title,fn in [('Settings…',desktop.settings_hub),('System Report…',desktop.system_info),('Sound Effects…',desktop.sound_preferences)]:button=QPushButton(title);button.clicked.connect(fn);footer.addWidget(button)
  v.addLayout(footer);self.refresh_displays();self.refresh_storage()
 def refresh_displays(self):
  lines=[]
  for n,screen in enumerate(QGuiApplication.screens(),1):
   size=screen.size();ratio=screen.devicePixelRatio();lines.extend([f'Display {n}: {screen.name()}',f'Resolution: {round(size.width()*ratio)} × {round(size.height()*ratio)} pixels',f'Logical size: {size.width()} × {size.height()}',f'Scale: {ratio:g}×',f'Refresh rate: {screen.refreshRate():.1f} Hz',''])
  self.display_list.setPlainText('\n'.join(lines) if lines else 'No display information is available.')
 def refresh_storage(self):
  self.volumes.clear()
  for volume in QStorageInfo.mountedVolumes():
   if not volume.isValid() or not volume.isReady() or volume.bytesTotal()<=0:continue
   row=QTreeWidgetItem([volume.rootPath(),f'{volume.bytesTotal()/1024**3:.1f} GB',f'{volume.bytesAvailable()/1024**3:.1f} GB','Read only' if volume.isReadOnly() else 'Read/write']);row.setData(0,Qt.UserRole,volume.rootPath());self.volumes.addTopLevelItem(row)
 def open_volume(self):
  item=self.volumes.currentItem()
  if item:self.desktop.files();self.desktop.windows['files'].content.navigate(item.data(0,Qt.UserRole))
class SettingsHub(QWidget):
 def __init__(self,desktop):
  super().__init__();v=QVBoxLayout(self);search=QLineEdit();search.setPlaceholderText('Search settings…');v.addWidget(search);self.items=QListWidget();v.addWidget(self.items,1)
  self.entries=[('Appearance, wallpaper & desktop',desktop.preferences),('Dock, windows & workspaces',desktop.preferences),('Window behavior and app rules',desktop.rules_panel),('Launcher drawers',desktop.open_drawers),('Sound effects',desktop.sound_preferences),('Volume, microphone / audio output',desktop.system_controls),('Displays — reported display information',lambda:desktop.about_tab(1)),('Storage — volumes and available space',lambda:desktop.about_tab(2)),('Network, Bluetooth & battery',desktop.system_controls),('Backups & Restore',desktop.backups),('Installed host applications',desktop.host_apps),('System Report',desktop.system_info),('About MacaqueSTEP',desktop.about),('Project Status & OS Readiness',desktop.project_status)]
  # Host controls provide output volume; input-device selection remains host-managed.
  self.entries[5]=('Audio output volume and mute',desktop.system_controls)
  self.entries.extend([('Workspace Clip and side-dock fitting',desktop.preferences),('Draggable Drawer Shelf',desktop.drawer_shelf),('Desktop Sessions',desktop.sessions_panel),('Keyboard Shortcuts',desktop.shortcuts_panel),('Unix Readiness Inventory',desktop.readiness_panel)])
  self.entries.extend([('Two-pane file management',desktop.dual_files),('File checksums',desktop.checksum_tool),('Disk usage analyzer',desktop.disk_usage),('System Monitor',desktop.system_monitor),('Recent Documents',desktop.recent_documents),('Activity Center',desktop.activity_center),('Setup Assistant',desktop.setup_assistant),('Software Center',desktop.software_center),('Accessibility',desktop.accessibility_panel),('Lock & Sleep',desktop.lock_sleep),('Personal Backup & Recovery',desktop.personal_recovery)])
  for title,_ in self.entries:self.items.addItem(title)
  def filter_items(text):
   for i in range(self.items.count()):self.items.item(i).setHidden(text.casefold() not in self.items.item(i).text().casefold())
  search.textChanged.connect(filter_items);self.items.itemActivated.connect(lambda item:self.entries[self.items.row(item)][1]());note=QLabel('Hardware controls depend on the host. Display information is read-only; change resolution through host display settings.');note.setWordWrap(True);v.addWidget(note)
