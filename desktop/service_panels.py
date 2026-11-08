"""Setup, app software, accessibility, locking and personal-file recovery."""
import json,os,time
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QSettings
from PySide6.QtWidgets import *
from service_tasks import Task
from storage import data_root
class ServicesPanel(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.job=None;self.v=QVBoxLayout(self);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);self.v.addWidget(self.status)
 def request(self,p,callback=None):
  if self.job:return
  self.status.setText('Working…');self.job=Task(self,Task.helper('desktop_services.py'),p,timeout=630000 if p['action'].startswith('flatpak-') else 65000)
  def done(ok,text):
   self.job=None
   if not ok:self.d.record_activity('Service failed',p['action']);self.status.setText(text);return
   try:data=json.loads(text)
   except ValueError:self.status.setText('The service returned unreadable data.');return
   self.d.record_activity('Service completed',p['action']);self.status.setText(data.get('message','Completed.'))
   if callback:callback(data)
  self.job.done.connect(done)
 def can_close(self):
  if self.job:self.status.setText('Wait for this operation to finish.');return False
  return True
class SoftwareCenter(ServicesPanel):
 def __init__(self,d):
  super().__init__(d);self.status.setText('Manage Flatpak applications for your account. Enable Flathub once; browsing and downloads require internet.')
  self.query=QLineEdit();self.query.setPlaceholderText('Search Flathub…');self.query.returnPressed.connect(self.search);self.v.addWidget(self.query);row=QHBoxLayout();self.v.addLayout(row)
  for title,fn in [('Enable Flathub…',self.enable),('Search',self.search),('Installed',lambda:self.request({'action':'flatpak-installed'},self.loaded)),('Available updates',lambda:self.request({'action':'flatpak-updates'},self.loaded))]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  self.items=QListWidget();self.items.setWordWrap(True);self.v.addWidget(self.items,1);row=QHBoxLayout();self.v.addLayout(row)
  for title,fn in [('Install…',lambda:self.selected_action('flatpak-install')),('Launch',lambda:self.selected_action('flatpak-launch')),('Remove…',lambda:self.selected_action('flatpak-remove')),('Update all…',self.update)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
 def confirm(self,text):return QMessageBox.question(self,'Software Center',text,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes
 def loaded(self,data):
  self.items.clear()
  for row in data.get('rows',[]):
   fields=row.split('\t');item=QListWidgetItem(' · '.join(fields));item.setData(Qt.UserRole,fields[0].strip());self.items.addItem(item)
  self.status.setText(f'{self.items.count()} results. Select an app.')
 def search(self):self.request({'action':'flatpak-search','query':self.query.text()},self.loaded)
 def enable(self):
  if self.confirm('Add the official Flathub repository for your account?'):self.request({'action':'flatpak-enable'})
 def selected_action(self,op):
  item=self.items.currentItem()
  if not item:self.status.setText('Select an application first.');return
  appid=item.data(Qt.UserRole)
  if op=='flatpak-launch' or self.confirm(('Install ' if op=='flatpak-install' else 'Remove ')+appid+'? Application data is retained when removed.'):self.request({'action':op,'id':appid})
 def update(self):
  if self.confirm('Download and apply all available user Flatpak updates?'):self.request({'action':'flatpak-update'})
class Accessibility(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);form=QFormLayout();v.addLayout(form);self.size=QSpinBox();self.size.setRange(11,24);self.size.setValue(int(d.settings.value('text_size',13)));form.addRow('Interface text size',self.size)
  self.contrast=QCheckBox('High contrast and stronger focus outlines');self.contrast.setChecked(d.settings.value('high_contrast',False,type=bool));v.addWidget(self.contrast)
  self.motion=QCheckBox('Reduce motion');self.motion.setChecked(d.settings.value('reduce_motion',False,type=bool));v.addWidget(self.motion);b=QPushButton('Apply');b.clicked.connect(self.apply);v.addWidget(b)
  note=QLabel('Applies to built-in MacaqueSTEP windows. Native apps have their own accessibility settings. Reduced motion shows a still welcome card for the full welcome duration. Tab/Shift+Tab navigates controls; Space activates buttons.');note.setWordWrap(True);v.addWidget(note);v.addStretch()
 def apply(self):
  for key,value in [('text_size',self.size.value()),('high_contrast',self.contrast.isChecked()),('reduce_motion',self.motion.isChecked())]:self.d.settings.setValue(key,value)
  self.d.apply_theme(self.d.theme)
class LockSleep(ServicesPanel):
 def __init__(self,d):
  super().__init__(d);self.status.setText('Locking uses LightDM/light-locker in the MacaqueSTEP X11 login session. Suspend is requested only after lock readiness is confirmed. Lid policy remains managed by logind.')
  for title,fn in [('Lock now',lambda:self.request({'action':'lock'})),('Lock then suspend…',self.suspend),('Inspect lock / lid policy',lambda:self.request({'action':'lock-status'}))]:b=QPushButton(title);b.clicked.connect(fn);self.v.addWidget(b)
  self.v.addStretch()
 def suspend(self):
  if QMessageBox.question(self,'Suspend','Save your work first. Lock this session, then suspend?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.request({'action':'suspend'})
class SetupAssistant(ServicesPanel):
 def __init__(self,d):
  super().__init__(d);self.status.setText('Set up your MacaqueSTEP desktop. Apply each choice when ready.');self.pages=QStackedWidget();self.v.addWidget(self.pages,1)
  appearance=QWidget();form=QFormLayout(appearance);self.mode=QComboBox();self.mode.addItems(['Classic','Light','Dark']);self.mode.setCurrentText(d.theme);form.addRow('Theme',self.mode)
  from decorations import STYLES
  self.decor=QComboBox()
  for value,title in STYLES.items():self.decor.addItem(title,value)
  self.decor.setCurrentIndex(max(0,self.decor.findData(d.settings.value('decoration_style','modern'))));form.addRow('Window decorations',self.decor)
  self.side=QComboBox();self.side.addItems(['Left','Right']);self.side.setCurrentText(d.settings.value('dock_side','Right'));form.addRow('Side dock',self.side)
  self.sounds=QCheckBox('Enable desktop sounds');self.sounds.setChecked(d.settings.value('sounds_enabled',True,type=bool));form.addRow(self.sounds)
  b=QPushButton('Apply desktop preferences');b.clicked.connect(self.appearance);form.addRow(b);self.pages.addWidget(appearance)
  network=QWidget();v=QVBoxLayout(network);b=QPushButton('Network connections…');b.clicked.connect(self.network);v.addWidget(b);self.zones=QComboBox();self.zones.setEditable(True);v.addWidget(self.zones);b=QPushButton('Load time zones');b.clicked.connect(lambda:self.request({'action':'zones'},lambda data:self.zones.addItems(data['zones'])));v.addWidget(b);b=QPushButton('Apply time zone');b.clicked.connect(lambda:self.request({'action':'timezone','zone':self.zones.currentText()}));v.addWidget(b);v.addStretch();self.pages.addWidget(network)
  essentials=QWidget();v=QVBoxLayout(essentials)
  for title,fn in [('Accessibility',d.accessibility_panel),('Lock & Sleep',d.lock_sleep),('Software Center',d.software_center),('Personal Backup & Recovery',d.personal_recovery),('Organizer Backups',d.backups)]:b=QPushButton(title+'…');b.clicked.connect(fn);v.addWidget(b)
  v.addStretch();self.pages.addWidget(essentials);row=QHBoxLayout();self.v.addLayout(row);self.back=QPushButton('Back');self.back.clicked.connect(lambda:self.page(-1));row.addWidget(self.back);self.next=QPushButton('Next');self.next.clicked.connect(self.advance);row.addWidget(self.next);self.page(0)
 def appearance(self):
  self.d.settings.setValue('decoration_style',self.decor.currentData());self.d.settings.setValue('sounds_enabled',self.sounds.isChecked());self.d.apply_theme(self.mode.currentText());self.d.dock_side(self.side.currentText());self.status.setText('Desktop preferences applied.')
 def network(self):
  from PySide6.QtCore import QProcess
  if os.environ.get('MACAQUESTEP_SESSION')!='1':self.status.setText('Open network connections from the MacaqueSTEP login session.');return
  started=QProcess.startDetached('nm-connection-editor',[])
  if not (started[0] if isinstance(started,tuple) else started):self.status.setText('Network connection editor is unavailable.')
 def page(self,delta):self.pages.setCurrentIndex(max(0,min(2,self.pages.currentIndex()+delta)));self.back.setEnabled(self.pages.currentIndex()>0);self.next.setText('Finish' if self.pages.currentIndex()==2 else 'Next')
 def advance(self):
  if self.job:return
  if self.pages.currentIndex()<2:self.page(1);return
  from first_welcome import state_directory
  (state_directory()/'setup-pending').unlink(missing_ok=True);self.d.settings.setValue('setup_completed',True);self.next.setEnabled(False);self.status.setText('Setup complete. You can reopen this assistant from Tools.')

class PersonalRecovery(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.worker=None;v=QVBoxLayout(self);note=QLabel('Back up a visible personal subfolder within your home. Symlinks and hidden files are excluded. Limit: 250 MB / 10,000 files. Recover into a new folder; existing documents are never replaced. Organizer backups remain available separately.');note.setWordWrap(True);v.addWidget(note)
  for title,fn in [('Back up a personal folder…',self.backup),('Recover personal backup…',self.recover),('Restore recovered appearance / accessibility…',self.preferences)]:b=QPushButton(title);b.clicked.connect(fn);v.addWidget(b)
  self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);v.addWidget(self.status);v.addStretch()
 def can_close(self):
  if self.worker and self.worker.isRunning():self.status.setText('Wait for backup or recovery to finish.');return False
  return True
 def start(self,fn,args):
  if not self.can_close():return
  from personal_backups import BackupWorker
  self.worker=BackupWorker(fn,args,self);self.worker.done.connect(lambda path:self.status.setText('Completed: '+path));self.worker.failed.connect(lambda error:self.status.setText('Could not finish: '+error));self.status.setText('Working…');self.worker.start()
 def backup(self):
  from personal_backups import create_backup
  folder=QFileDialog.getExistingDirectory(self,'Choose personal folder',str(Path.home()/'Documents'))
  if not folder:return
  root=Path(folder).resolve();home=Path.home().resolve()
  if root==home or not root.is_relative_to(home) or any(part.startswith('.') for part in root.relative_to(home).parts):self.status.setText('Choose a visible subfolder inside your home folder.');return
  destination=QFileDialog.getSaveFileName(self,'Save personal backup',str(home/('MacaqueSTEP-Personal-'+time.strftime('%Y%m%d-%H%M%S')+'.zip')),'ZIP (*.zip)')[0]
  if destination:self.start(create_backup,(root,preference_snapshot(self.d.settings),destination,True))
 def recover(self):
  from personal_backups import recover_backup
  archive=QFileDialog.getOpenFileName(self,'Recover personal backup',str(Path.home()),'ZIP (*.zip)')[0]
  if not archive:return
  parent=QFileDialog.getExistingDirectory(self,'Choose parent for a new recovered folder',str(Path.home()))
  if parent:self.start(recover_backup,(archive,parent))
 def preferences(self):
  path=QFileDialog.getOpenFileName(self,'Choose recovered desktop-state.json',str(Path.home()),'JSON (*.json)')[0]
  if not path:return
  try:
   if Path(path).stat().st_size>65536:raise ValueError('Preference file exceeds 64 KB.')
   values=validate_preferences(json.loads(Path(path).read_text()))
   if QMessageBox.question(self,'Recover preferences','Apply recovered appearance and accessibility? Current preferences will be saved first. Files and app startup commands are unchanged.',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
   backup=data_root()/('preferences-before-recovery-'+str(time.time_ns())+'.json')
   with backup.open('x') as f:json.dump(preference_snapshot(self.d.settings),f)
   for key,value in values.items():self.d.settings.setValue(key,value)
   self.d.apply_theme(self.d.settings.value('theme',self.d.theme));self.d.dock_side(self.d.settings.value('dock_side','Right'));self.d.set_bar_style(self.d.settings.value('desktop_bar_style','classic'));self.status.setText('Preferences recovered. Previous choices: '+str(backup))
  except (OSError,ValueError,TypeError) as error:self.status.setText(str(error))
PREF_ENUMS={'theme':('Classic','Light','Dark'),'decoration_style':('modern','traffic','classic','wmaker'),'dock_side':('Left','Right'),'desktop_bar_style':('none','classic','toolbar')}
PREF_BOOLS=('high_contrast','reduce_motion','sounds_enabled','decoration_zoom')
def validate_preferences(data):
 if not isinstance(data,dict):raise ValueError('Expected a preference object.')
 values={}
 for key,choices in PREF_ENUMS.items():
  if key in data:
   if data[key] not in choices:raise ValueError('Invalid '+key)
   values[key]=data[key]
 for key in PREF_BOOLS:
  if key in data:
   if type(data[key]) is not bool:raise ValueError('Invalid '+key)
   values[key]=data[key]
 for key,low,high in [('text_size',11,24),('titlebar_height',30,48)]:
  if key in data:
   if type(data[key]) is not int or not low<=data[key]<=high:raise ValueError('Invalid '+key)
   values[key]=data[key]
 if not values:raise ValueError('No supported appearance or accessibility settings were found.')
 return values
def preference_snapshot(settings):return {key:settings.value(key) for key in list(PREF_ENUMS)+list(PREF_BOOLS)+['text_size','titlebar_height'] if settings.contains(key)}

class ModernServices:
 def service_window(self,key,title,cls):
  if key in self.windows:self.reopen(key);return self.windows[key]
  return self.window(key,title,cls(self),(100,60,760,570))
 def setup_assistant(self):return self.service_window('setup','Setup Assistant',SetupAssistant)
 def software_center(self):return self.service_window('software','Software Center',SoftwareCenter)
 def accessibility_panel(self):return self.service_window('accessibility','Accessibility',Accessibility)
 def lock_sleep(self):return self.service_window('lock-sleep','Lock & Sleep',LockSleep)
 def personal_recovery(self):return self.service_window('personal-backups','Personal Backup & Recovery',PersonalRecovery)
 def apply_accessibility(self):
  from PySide6.QtGui import QFont
  font=QFont(self.font());font.setPixelSize(max(11,min(24,int(self.settings.value('text_size',13)))));self.setFont(font)
  size=font.pixelSize();self.setStyleSheet(self.styleSheet()+f'QWidget {{font-size:{size}px;}}')
  if hasattr(self,'side_app_menu'):
   for button in self.side_app_menu.buttons.values():button.setFixedHeight(max(26,size+10))
   self.side_app_menu.title.setFixedHeight(max(28,size+12));self.update_side_menu_geometry()
  if self.settings.value('high_contrast',False,type=bool):self.setStyleSheet(self.styleSheet()+'QWidget {color:#ffffff;background-color:#111111;} QLineEdit,QTextEdit,QPlainTextEdit,QListView,QTreeView,QTableView {background:#000000;color:#ffffff;selection-background-color:#ffff00;selection-color:#000000;} QPushButton,QToolButton,QComboBox,QSpinBox {border:1px solid #ffffff;} QWidget:focus {border:2px solid #ffff00;}')
 def maybe_open_setup(self):
  from first_welcome import state_directory,installation_token
  pending=state_directory()/'setup-pending'
  token=installation_token()
  if os.environ.get('MACAQUESTEP_SESSION')=='1' and token and pending.is_file() and pending.read_text()==token:self.setup_assistant()
