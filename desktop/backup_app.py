import json,sqlite3,zipfile,tempfile,os
from pathlib import Path
from PySide6.QtCore import QSaveFile,QIODevice
from PySide6.QtWidgets import *
from storage import data_root

def create_backup(store,settings,path):
 preferences={str(k):settings.value(k) for k in settings.allKeys() if isinstance(settings.value(k),(str,int,float,bool,list,dict))}
 with tempfile.TemporaryDirectory() as folder:
  database=Path(folder)/'organizer.sqlite3';connection=sqlite3.connect(database)
  try:store.db.backup(connection)
  finally:connection.close()
  temp=Path(folder)/'backup.zip'
  with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:archive.write(database,'organizer.sqlite3');archive.writestr('preferences.json',json.dumps(preferences));archive.writestr('manifest.json',json.dumps({'format':'MacaqueSTEP backup','version':1}))
  output=QSaveFile(str(path));data=temp.read_bytes()
  if not output.open(QIODevice.WriteOnly) or output.write(data)!=len(data) or not output.commit():raise OSError(output.errorString())

def validate_backup(path):
 with zipfile.ZipFile(path) as archive:
  required={'organizer.sqlite3','preferences.json','manifest.json'}
  if set(archive.namelist())!=required:raise ValueError('This is not a MacaqueSTEP backup.')
  if any(info.file_size>32*1024**2 for info in archive.infolist()):raise ValueError('Backup entries exceed the supported size.')
  manifest=json.loads(archive.read('manifest.json'))
  if manifest.get('format')!='MacaqueSTEP backup' or manifest.get('version')!=1:raise ValueError('Unsupported backup format.')
  data=archive.read('organizer.sqlite3');preferences=json.loads(archive.read('preferences.json'))
  if not isinstance(preferences,dict):raise ValueError('Invalid preferences.')
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'check.sqlite3';path.write_bytes(data);db=sqlite3.connect(path)
  try:
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed.')
   for table,columns in [('notes',{'id','title','body'}),('tasks',{'id','title','done'})]:
    info={row[1] for row in db.execute('PRAGMA table_info('+table+')')}
    if not columns<=info:raise ValueError('Missing organizer tables.')
  finally:db.close()
 return data,preferences

def schedule_restore(path):
 validate_backup(path);source=Path(path)
 if source.stat().st_size>64*1024**2:raise ValueError('Backup file exceeds 64 MB.')
 file=QSaveFile(str(data_root()/'pending-restore.zip'));payload=source.read_bytes()
 if not file.open(QIODevice.WriteOnly) or file.write(payload)!=len(payload) or not file.commit():raise OSError(file.errorString())
def apply_pending_restore(settings):
 root=data_root();pending=root/'pending-restore.zip'
 if not pending.exists():return False
 data,values=validate_backup(pending);current=root/'organizer.sqlite3'
 if current.exists():
  import shutil;shutil.copy2(current,root/'organizer-before-restore.sqlite3')
 file=QSaveFile(str(current))
 if not file.open(QIODevice.WriteOnly) or file.write(data)!=len(data) or not file.commit():raise OSError(file.errorString())
 allowed_booleans={'high_contrast','reduce_motion','decoration_zoom','left_menu_enabled','top_bar_visible','running_visible','running_group','running_current_only','running_follow_side','restore_layout','sounds_enabled','sounds_startup','sounds_windows','sounds_menus','sounds_alerts','wm_focus_follows_mouse','wm_raise_on_focus','dock_double_click','dock_fit','clip_visible','clip_collapsed_0','clip_collapsed_1','clip_collapsed_2','clip_collapsed_3'}
 ranges={'text_size':(11,24),'titlebar_height':(30,48),'dock_size':(24,68),'running_icon_size':(24,56)}
 enums={'decoration_style':{'modern','traffic','classic','wmaker'},'theme':{'Classic','Light','Dark'},'dock_side':{'Left','Right'},'wallpaper':{'Geometry','Gradient'},'wm_double_click':{'Shade','Maximize'},'desktop_bar_style':{'classic','toolbar','none'},'desktop_bar_last':{'classic','toolbar'}}
 for key,value in values.items():
  if key=='sounds_volume' and type(value) in (int,float):settings.setValue(key,max(0,min(1,value)))
  elif key in allowed_booleans and type(value)==bool:settings.setValue(key,value)
  elif key in ranges and type(value)==int:settings.setValue(key,max(ranges[key][0],min(ranges[key][1],value)))
  elif key in enums and isinstance(value,str) and value in enums[key]:settings.setValue(key,value)
  elif key in {'floating_menu_position','folder_bookmarks','wallpaper_file','layouts_v3','core_spaces_v05','wm_rules','wm_workspace_names','wm_drawers','session_profiles','session_startup','keyboard_bindings','running_pins_v14','dock_launchers_v12','clip_launchers_0','clip_launchers_1','clip_launchers_2','clip_launchers_3'} and isinstance(value,str):settings.setValue(key,value)
 settings.sync();pending.unlink();return True
class Backups(QWidget):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;v=QVBoxLayout(self);text=QLabel('Back up Notes, Tasks, and desktop preferences.\nUser documents, media, and wallpaper image files are not included.\nRestore takes effect on the next launch.');text.setWordWrap(True);v.addWidget(text)
  for title,fn in [('Create backup…',self.create),('Validate backup…',self.validate),('Restore on next launch…',self.restore)]:button=QPushButton(title);button.clicked.connect(fn);v.addWidget(button)
  self.status=QLabel('Backups stay where you choose to save them.');self.status.setWordWrap(True);v.addWidget(self.status);v.addStretch()
 def create(self):
  if not self.desktop.flush_notes():return
  path=QFileDialog.getSaveFileName(self,'Save backup',str(Path.home()/'MacaqueSTEP-backup.zip'),'ZIP (*.zip)')[0]
  if not path:return
  try:create_backup(self.desktop.store,self.desktop.settings,path);self.status.setText('Backup saved: '+path)
  except Exception as e:QMessageBox.warning(self,'Backup',str(e))
 def validate(self):
  path=QFileDialog.getOpenFileName(self,'Validate backup',str(Path.home()),'ZIP (*.zip)')[0]
  if not path:return
  try:validate_backup(path);self.status.setText('Backup passed validation.')
  except Exception as e:QMessageBox.warning(self,'Backup',str(e))
 def restore(self):
  path=QFileDialog.getOpenFileName(self,'Restore backup',str(Path.home()),'ZIP (*.zip)')[0]
  if not path:return
  if QMessageBox.question(self,'Restore backup','Replace Notes, Tasks, and saved preferences with this backup on the next launch?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  try:schedule_restore(path);self.status.setText('Restore scheduled. Close the preview and launch it again. A recovery copy of the previous organizer will be retained.')
  except Exception as e:QMessageBox.warning(self,'Restore',str(e))
