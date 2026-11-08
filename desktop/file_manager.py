import os,shutil,json
from pathlib import Path
from PySide6.QtCore import Qt,QDir,QThread,Signal,QFile,QModelIndex,QMimeData,QUrl
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtWidgets import *
from storage import duplicate_file
from fileops import TransferJob
class CopyJob(QThread):
 result=Signal(str,bool)
 def __init__(self,src,dst,parent=None):super().__init__(parent);self.src=src;self.dst=dst
 def run(self):
  try:duplicate_file(self.src,self.dst);self.result.emit('Copied '+Path(self.src).name,True)
  except Exception as e:self.result.emit(str(e),False)
class FileManager(QWidget):
 def __init__(self,desktop,compact=False):
  super().__init__();self.desktop=desktop;self.history=[];self.hpos=-1;self.copied=None;self.jobs=[]
  v=QVBoxLayout(self);bar=QHBoxLayout();self.back=QPushButton('←');self.forward=QPushButton('→');up=QPushButton('↑');self.path=QLineEdit();go=QPushButton('Go')
  for b in (self.back,self.forward,up):b.setFixedWidth(35);bar.addWidget(b)
  bar.addWidget(self.path,1);bar.addWidget(go);v.addLayout(bar);tools=QHBoxLayout();self.filter=QLineEdit();self.filter.setPlaceholderText('Filter names in this folder…');tools.addWidget(self.filter,1);self.hidden=QCheckBox('Hidden');tools.addWidget(self.hidden);v.addLayout(tools)
  split=QSplitter();self.places=QListWidget();self.places.setMaximumWidth(170)
  for title,p in [('Home',Path.home()),('Documents',Path.home()/'Documents'),('Downloads',Path.home()/'Downloads'),('Pictures',Path.home()/'Pictures'),('Music',Path.home()/'Music'),('Videos',Path.home()/'Videos'),('Filesystem',Path('/'))]:item=QListWidgetItem(title);item.setData(Qt.UserRole,str(p));self.places.addItem(item)
  self.model=QFileSystemModel(self);self.model.setReadOnly(True);self.model.setRootPath(str(Path.home()));self.view=QTreeView();self.view.setModel(self.model);self.view.setSelectionMode(QAbstractItemView.ExtendedSelection);self.view.setRootIsDecorated(False);self.view.setAlternatingRowColors(True);self.view.setSortingEnabled(True);self.view.sortByColumn(0,Qt.AscendingOrder);self.view.setColumnWidth(0,280)
  split.addWidget(self.places);split.addWidget(self.view);self.places.setVisible(not compact);split.setStretchFactor(1,1);v.addWidget(split,1);self.status=QLabel();v.addWidget(self.status);buttons=QGridLayout()
  for i,(title,fn) in enumerate([('New folder',self.mkdir),('Copy',self.copy),('Cut',self.cut),('Paste',self.paste),('Rename',self.rename),('Move to Trash',self.trash),('Properties',self.properties)]):b=QPushButton(title);b.clicked.connect(fn);buttons.addWidget(b,i//4,i%4)
  v.addLayout(buttons);go.clicked.connect(lambda:self.navigate(self.path.text()));self.path.returnPressed.connect(lambda:self.navigate(self.path.text()));up.clicked.connect(lambda:self.navigate(Path(self.path.text()).parent));self.back.clicked.connect(lambda:self.travel(-1));self.forward.clicked.connect(lambda:self.travel(1));self.places.itemClicked.connect(lambda i:self.navigate(i.data(Qt.UserRole)));self.hidden.toggled.connect(self.set_filter);self.filter.textChanged.connect(self.filter_changed);self.view.doubleClicked.connect(self.open)
  self.view.setContextMenuPolicy(Qt.CustomContextMenu);self.view.customContextMenuRequested.connect(self.menu)
  for keys,fn in [('Ctrl+C',self.copy),('Ctrl+X',self.cut),('Ctrl+V',self.paste),('F2',self.rename)]:a=QAction(self.view);a.setShortcut(QKeySequence(keys));a.setShortcutContext(Qt.WidgetWithChildrenShortcut);a.triggered.connect(fn);self.view.addAction(a)
  self.setup_bookmarks()
  self.navigate(Path.home())
 def set_filter(self,*_):self.model.setFilter(QDir.AllEntries|QDir.NoDotAndDotDot|(QDir.Hidden if self.hidden.isChecked() else QDir.Filter(0)))
 def filter_changed(self,s):self.model.setNameFilters(['*'+s+'*'] if s else []);self.model.setNameFilterDisables(False)
 def navigate(self,p,record=True):
  p=Path(p).expanduser().absolute()
  if not p.is_dir() or not os.access(p,os.R_OK|os.X_OK):QMessageBox.warning(self,'Folder','This folder is unavailable or access is denied.');return
  self.filter.clear();self.view.clearSelection();self.view.setCurrentIndex(QModelIndex());self.path.setText(str(p));self.view.setRootIndex(self.model.index(str(p)))
  if record:self.history=self.history[:self.hpos+1];self.history.append(str(p));self.hpos=len(self.history)-1
  self.back.setEnabled(self.hpos>0);self.forward.setEnabled(self.hpos<len(self.history)-1)
  try:self.status.setText(f'{shutil.disk_usage(p).free//1024**3} GB available')
  except OSError:self.status.setText(str(p))
 def travel(self,step):
  pos=self.hpos+step
  if 0<=pos<len(self.history):self.hpos=pos;self.navigate(self.history[pos],False)
 def selected(self):
  idx=self.view.currentIndex();return Path(self.model.filePath(idx)) if idx.isValid() else None
 def open(self,index):
  if not index.isValid():return
  p=Path(self.model.filePath(index))
  if p.is_dir():self.navigate(p)
  else:self.desktop.open_path(p)
 def mkdir(self):
  name,ok=QInputDialog.getText(self,'New folder','Folder name')
  if not ok or not name:return
  if name in ('.','..') or '/' in name:QMessageBox.warning(self,'Folder','Enter one folder name.');return
  try:(Path(self.path.text())/name).mkdir()
  except OSError as e:QMessageBox.warning(self,'Folder',str(e))
 def selected_paths(self):
  return [Path(self.model.filePath(index)) for index in self.view.selectionModel().selectedRows(0)]
 def copy(self):self.clipboard(False)
 def cut(self):self.clipboard(True)
 def clipboard(self,move):
  paths=self.selected_paths()
  if not paths:
   p=self.selected();paths=[p] if p is not None else []
  if not paths:return
  mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths]);mime.setData('application/x-macaquestep-action',b'move' if move else b'copy');QApplication.clipboard().setMimeData(mime);self.status.setText(f'{len(paths)} items ready to '+('move' if move else 'copy'))
 def paste(self):
  mime=QApplication.clipboard().mimeData();paths=[url.toLocalFile() for url in mime.urls() if url.isLocalFile()] if mime and mime.hasUrls() else []
  if not paths:return
  move=bytes(mime.data('application/x-macaquestep-action'))==b'move';self.start_transfer(paths,self.path.text(),move)
 def start_transfer(self,paths,folder,move=False):
  if self.jobs:QMessageBox.information(self,'File operation','Wait for the current transfer to finish or cancel it.');return
  job=TransferJob(paths,folder,move,self);self.jobs.append(job);self.status.setText('Moving…' if move else 'Copying…')
  progress=QProgressDialog('Transferring files…','Cancel',0,0,self);progress.setWindowModality(Qt.NonModal);progress.setMinimumDuration(300);progress.canceled.connect(job.requestInterruption)
  job.progress.connect(lambda name,count:(self.status.setText(f'{name} • {count//1024:,} KB transferred'),progress.setLabelText(name)))
  def done(successes,errors,canceled):
   progress.reset();self.desktop.play_sound('error' if errors else 'complete');self.status.setText(f'{len(successes)} items completed'+(' • canceled' if canceled else '')+(f' • {len(errors)} failed' if errors else ''))
   self.desktop.record_activity('File transfer '+('canceled' if canceled else 'finished'),f'{len(successes)} completed; {len(errors)} failed')
   if errors:QMessageBox.warning(self,'Transfer results','\n'.join(errors[:20]))
   if move and len(successes)==len(paths) and not errors and not canceled:QApplication.clipboard().clear()
  job.completed.connect(done);job.finished.connect(lambda:self.jobs.remove(job));job.finished.connect(progress.deleteLater);job.finished.connect(job.deleteLater);job.start()
 def rename(self):
  p=self.selected()
  if p is None:return
  name,ok=QInputDialog.getText(self,'Rename','New name',text=p.name)
  if not ok or not name or name==p.name:return
  if name in ('.','..') or '/' in name:QMessageBox.warning(self,'Rename','Enter one file or folder name.');return
  f=QFile(str(p))
  if not f.rename(str(p.with_name(name))):QMessageBox.warning(self,'Rename',f.errorString())
 def trash(self):
  paths=self.selected_paths()
  if not paths:
   p=self.selected();paths=[p] if p is not None else []
  if not paths:return
  if QMessageBox.question(self,'Move to Trash',f'Move {len(paths)} selected items to the system Trash?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  errors=[]
  for p in paths:
   file=QFile(str(p))
   if not file.moveToTrash():errors.append(p.name+': '+file.errorString())
  if len(errors)<len(paths):self.desktop.play_sound('trash')
  if len(errors)<len(paths):self.desktop.record_activity('Moved items to Trash',str(len(paths)-len(errors))+' items')
  if errors:QMessageBox.warning(self,'Trash','\n'.join(errors))
 def properties(self):
  p=self.selected()
  if p is None:return
  try:stat=p.lstat();QMessageBox.information(self,'Properties',f'{p}\n\nSize: {stat.st_size:,} bytes\nPermissions: {oct(stat.st_mode & 0o777)}\nType: {"Symbolic link" if p.is_symlink() else "Folder" if p.is_dir() else "File"}')
  except OSError as e:QMessageBox.warning(self,'Properties',str(e))
 def menu(self,pos):
  idx=self.view.indexAt(pos)
  if idx.isValid():self.view.setCurrentIndex(idx)
  m=QMenu(self)
  for name,fn in [('Open',lambda:self.open(self.view.currentIndex())),('Copy',self.copy),('Cut',self.cut),('Paste',self.paste),('Rename',self.rename),('Move to Trash',self.trash),('Properties',self.properties),('Copy path',self.copy_path),('Calculate checksums…',lambda:self.desktop.checksum_tool(self.selected()))]:m.addAction(name,fn)
  m.exec(self.view.viewport().mapToGlobal(pos))

 def setup_bookmarks(self):
  row=QGridLayout();self.bookmarks=QComboBox();self.bookmarks.setMinimumWidth(80);row.addWidget(self.bookmarks,0,0,1,3)
  for i,(title,fn) in enumerate([('Go',self.go_bookmark),('Bookmark folder',self.add_bookmark),('Remove bookmark',self.remove_bookmark)]):button=QPushButton(title);button.clicked.connect(fn);row.addWidget(button,1,i)
  self.layout().insertLayout(2,row);self.refresh_bookmarks()
  for keys,fn in [('Ctrl+L',lambda:(self.path.setFocus(),self.path.selectAll())),('Alt+Left',lambda:self.travel(-1)),('Alt+Right',lambda:self.travel(1)),('F5',self.refresh_folder),('Ctrl+D',self.add_bookmark)]:
   action=QAction(self);action.setShortcut(QKeySequence(keys));action.setShortcutContext(Qt.WidgetWithChildrenShortcut);action.triggered.connect(fn);self.addAction(action)
  action=QAction(self.view);action.setShortcut(QKeySequence('Ctrl+Shift+C'));action.setShortcutContext(Qt.WidgetWithChildrenShortcut);action.triggered.connect(self.copy_path);self.view.addAction(action)
 def bookmark_paths(self):
  try:rows=json.loads(self.desktop.settings.value('folder_bookmarks','[]'))
  except (ValueError,TypeError):return []
  return list(dict.fromkeys(p for p in rows if isinstance(p,str) and p.startswith('/') and len(p)<4096))[:100] if isinstance(rows,list) else []
 def refresh_bookmarks(self):
  self.bookmarks.clear()
  for path in self.bookmark_paths():self.bookmarks.addItem(Path(path).name+' — '+path,path)
 def save_bookmarks(self,paths):
  self.desktop.settings.setValue('folder_bookmarks',json.dumps(paths[:100]))
  for panel in self.desktop.findChildren(FileManager):panel.refresh_bookmarks()
  self.refresh_bookmarks()
 def add_bookmark(self):
  path=str(Path(self.path.text()).expanduser().absolute())
  if Path(path).is_dir():self.save_bookmarks(self.bookmark_paths()+([] if path in self.bookmark_paths() else [path]));self.status.setText('Folder bookmarked.')
 def remove_bookmark(self):
  path=self.bookmarks.currentData()
  if path:self.save_bookmarks([p for p in self.bookmark_paths() if p!=path])
 def go_bookmark(self):
  path=self.bookmarks.currentData()
  if path:self.navigate(path)
 def copy_path(self):
  paths=self.selected_paths()
  if not paths:
   path=self.selected();paths=[path] if path else [Path(self.path.text())]
  QApplication.clipboard().setText('\n'.join(str(p) for p in paths));self.status.setText('Path copied.')
 def refresh_folder(self):
  if self.jobs:self.status.setText('Wait for the active transfer before refreshing.');return
  current=self.path.text();old=self.model;self.model=QFileSystemModel(self);self.model.setReadOnly(True);self.model.setRootPath(current);self.view.setModel(self.model);self.view.sortByColumn(0,Qt.AscendingOrder);self.view.setColumnWidth(0,280);self.set_filter();self.navigate(current,False);old.deleteLater()
 def can_close(self):
  if self.jobs:self.status.setText('Wait for the file transfer or cancel it before closing.');return False
  return True
