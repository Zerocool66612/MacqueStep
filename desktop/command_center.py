"""Searchable desktop actions and validated desktop-level shortcut overrides."""
import json
from PySide6.QtCore import Qt,QEvent
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtWidgets import *
LABELS={'F11':'Toggle full screen','Esc':'Return to windowed mode','Ctrl+Alt+T':'Terminal','Ctrl+Space':'Applications','Ctrl+Tab':'Next window','Ctrl+Alt+W':'Open Windows','Ctrl+Alt+O':'Workspace overview','Ctrl+Alt+F':'File search','Ctrl+Alt+S':'Shade active window','Ctrl+Alt+D':'Customize drawers','Ctrl+Alt+PgDown':'Next workspace','Ctrl+Alt+PgUp':'Previous workspace'}
EXTRA=[('Show Classic Menus','Ctrl+Alt+M','show_classic_menus'),('Show / hide top bar','Ctrl+Alt+B','toggle_top_bar'),('Command palette','Ctrl+Alt+P','command_palette'),('Desktop sessions','Ctrl+Alt+L','sessions_panel'),('Show desktop / restore windows','Ctrl+Alt+H','show_desktop'),('Undo layout','Ctrl+Alt+Z','undo_layout')]
TOOLS=[('Two-Pane Files', 'dual_files'), ('Disk Usage', 'disk_usage'), ('System Monitor', 'system_monitor'), ('File Checksums', 'checksum_tool'), ('Recent Documents', 'recent_documents'), ('Activity Center', 'activity_center')]+[('Setup Assistant','setup_assistant'),('Software Center','software_center'),('Accessibility','accessibility_panel'),('Lock & Sleep','lock_sleep'),('Personal Backup & Recovery','personal_recovery'),('Drawer Shelf','drawer_shelf'),('File Viewer','files'),('Terminal','terminal'),('Text Editor','editor'),('Notes','notes'),('Tasks','tasks'),('Paint','paint_app'),('Calculator','calculator'),('Clock & Timer','clock_app'),('File Search','search_files'),('Settings','settings_hub'),('Sound Effects','sound_preferences'),('Desktop Sessions','sessions_panel'),('Keyboard Shortcuts','shortcuts_panel'),('Launcher Drawers','open_drawers'),('Window Rules','rules_panel'),('System Report','system_info'),('Unix Readiness Inventory','readiness_panel'),('Backups','backups'),('Project Status','project_status'),('Help','help_center'),('About MacaqueSTEP','about')]
def sequence(text):return QKeySequence.fromString(text,QKeySequence.PortableText)
def validate_bindings(bindings):
 seen=[]
 for key,text in bindings.items():
  if not isinstance(text,str) or len(text)>100:raise ValueError('Invalid shortcut.')
  if not text:continue
  seq=sequence(text)
  if seq.isEmpty() or seq.count()!=1 or not seq.toString(QKeySequence.PortableText):raise ValueError('Use one valid key combination per action.')
  for other,old in seen:
   if seq.matches(old)!=QKeySequence.NoMatch or old.matches(seq)!=QKeySequence.NoMatch:raise ValueError(f'Shortcut conflict: {key} and {other}.')
  seen.append((key,seq))
 return True
class Commands:
 def setup_commands(self):
  self.command_actions={};self.command_defaults={};self.command_labels={}
  for action in self.actions():
   default=action.shortcut().toString(QKeySequence.PortableText)
   if not default:continue
   self.command_actions[default]=action;self.command_defaults[default]=default
   label=LABELS.get(default,'Workspace '+default[-1] if default.startswith('Ctrl+Alt+') and default[-1:] in '1234' else 'Snap '+default.rsplit('+',1)[-1]);self.command_labels[default]=label
  for label,default,method in EXTRA:
   action=QAction(label,self);action.setShortcut(sequence(default));action.triggered.connect(getattr(self,method));self.addAction(action);self.command_actions[default]=action;self.command_defaults[default]=default;self.command_labels[default]=label
  try:
   saved=json.loads(self.settings.value('keyboard_bindings','{}'))
   if isinstance(saved,dict):
    bindings={key:saved.get(key,value) for key,value in self.command_defaults.items()};self.set_bindings(bindings,save=False)
  except (ValueError,TypeError):pass
 def set_bindings(self,bindings,save=True):
  if set(bindings)!=set(self.command_actions):raise ValueError('Incomplete keyboard configuration.')
  validate_bindings(bindings)
  for key,action in self.command_actions.items():action.setShortcut(sequence(bindings[key]))
  if save:self.settings.setValue('keyboard_bindings',json.dumps(bindings))
 def shortcuts_panel(self):
  if 'shortcuts' in self.windows:self.reopen('shortcuts');return
  self.window('shortcuts','Keyboard Shortcuts',ShortcutsPanel(self),(100,60,700,610))
 def command_palette(self):
  dialog=Palette(self);dialog.exec()
class ShortcutsPanel(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.editors={};v=QVBoxLayout(self);note=QLabel('Change desktop shortcuts. Use Clear to disable one. Duplicate combinations are rejected. App-local editing shortcuts and host desktop shortcuts are separate.');note.setWordWrap(True);v.addWidget(note);table=QTableWidget(len(d.command_actions),2);table.setHorizontalHeaderLabels(['Desktop action','Shortcut']);table.setEditTriggers(QAbstractItemView.NoEditTriggers);table.horizontalHeader().setStretchLastSection(True);table.setColumnWidth(0,330);v.addWidget(table)
  for row,(key,action) in enumerate(d.command_actions.items()):
   table.setItem(row,0,QTableWidgetItem(d.command_labels[key]));editor=QKeySequenceEdit(action.shortcut());editor.setMaximumSequenceLength(1);editor.setClearButtonEnabled(True);table.setCellWidget(row,1,editor);self.editors[key]=editor
  row=QHBoxLayout()
  for label,callback in [('Apply shortcuts',self.apply),('Restore defaults',self.defaults)]:button=QPushButton(label);button.clicked.connect(callback);row.addWidget(button)
  v.addLayout(row);self.status=QLabel('Changes take effect when you press Apply.');self.status.setWordWrap(True);v.addWidget(self.status)
 def apply(self):
  try:self.d.set_bindings({key:edit.keySequence().toString(QKeySequence.PortableText) for key,edit in self.editors.items()});self.status.setText('Saved and applied.')
  except ValueError as error:self.status.setText(str(error))
 def defaults(self):
  for key,edit in self.editors.items():edit.setKeySequence(sequence(self.d.command_defaults[key]))
  self.status.setText('Default combinations loaded. Press Apply to save them.')
class Palette(QDialog):
 def __init__(self,d):
  super().__init__(d);self.setWindowTitle('Command Palette');self.resize(650,520);v=QVBoxLayout(self);self.search=QLineEdit();self.search.setPlaceholderText('Find apps, open windows, workspaces, or actions…');v.addWidget(self.search);self.items=QListWidget();v.addWidget(self.items,1);self.entries=[]
  for title,method in TOOLS:self.entries.append(('Open '+title,getattr(d,method)))
  for key,w in d.windows.items():self.entries.append(('Window: '+w.windowTitle()+' · '+d.workspace_name(w.property('workspace') or 0),lambda k=key:d.activate_running(k,False)))
  for i in range(4):self.entries.append(('Switch to '+d.workspace_name(i),lambda n=i:d.switch_workspace(n)))
  for title,callback in [('Show Classic Menus',d.show_classic_menus),('Show / hide top bar',d.toggle_top_bar),('Tile workspace',d.tile_workspace),('Cascade workspace',d.cascade_workspace),('Undo layout',d.undo_layout),('Show desktop / restore windows',d.show_desktop),('Workspace overview',d.overview),('Shade active window',d.shade_active)]:self.entries.append((title,callback))
  self.search.installEventFilter(self);self.search.textChanged.connect(self.filter);self.search.returnPressed.connect(self.run);self.items.itemActivated.connect(self.run);self.filter('');self.search.setFocus()
 def eventFilter(self,obj,event):
  if obj is self.search and event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Up,Qt.Key_Down):
   if self.items.count():self.items.setCurrentRow(max(0,min(self.items.count()-1,self.items.currentRow()+(1 if event.key()==Qt.Key_Down else -1))))
   return True
  return super().eventFilter(obj,event)
 def filter(self,text):
  self.items.clear();terms=text.casefold().split()
  for index,(label,_) in enumerate(self.entries):
   if all(term in label.casefold() for term in terms):item=QListWidgetItem(label);item.setData(Qt.UserRole,index);self.items.addItem(item)
  if self.items.count():self.items.setCurrentRow(0)
 def run(self,*_):
  item=self.items.currentItem()
  if item:callback=self.entries[item.data(Qt.UserRole)][1];self.accept();callback()
