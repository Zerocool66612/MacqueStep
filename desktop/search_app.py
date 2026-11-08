import os
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal
from PySide6.QtWidgets import *
class SearchJob(QThread):
 found=Signal(list);finished_search=Signal(int,int,bool)
 def __init__(self,root,query,hidden,parent=None):super().__init__(parent);self.root=root;self.query=query.casefold();self.hidden=hidden
 def run(self):
  count=0;denied=0;batch=[]
  def error(_):
   nonlocal denied;denied+=1
  for folder,dirs,files in os.walk(self.root,followlinks=False,onerror=error):
   if self.isInterruptionRequested():break
   dirs[:]=[name for name in dirs if (self.hidden or not name.startswith('.')) and not Path(folder,name).is_symlink()]
   for name in dirs+files:
    if self.isInterruptionRequested():break
    if not self.hidden and name.startswith('.'):continue
    if self.query in name.casefold():
     batch.append(str(Path(folder,name)));count+=1
     if len(batch)>=50:self.found.emit(batch);batch=[]
     if count>=1000:break
   if count>=1000:break
  if batch:self.found.emit(batch)
  self.finished_search.emit(count,denied,self.isInterruptionRequested())
class Search(QWidget):
 def __init__(self,desktop):
  super().__init__();self.desktop=desktop;self.job=None;v=QVBoxLayout(self);row=QHBoxLayout();self.root=QLineEdit(str(Path.home()));browse=QPushButton('Folder…');row.addWidget(self.root,1);row.addWidget(browse);v.addLayout(row);row=QHBoxLayout();self.query=QLineEdit();self.query.setPlaceholderText('Find files or folders by name…');self.hidden=QCheckBox('Include hidden');self.go=QPushButton('Search');stop=QPushButton('Stop');row.addWidget(self.query,1);row.addWidget(self.hidden);row.addWidget(self.go);row.addWidget(stop);v.addLayout(row);self.items=QListWidget();v.addWidget(self.items,1);self.status=QLabel('Search names recursively • up to 1,000 results • symbolic-link folders are skipped');v.addWidget(self.status);browse.clicked.connect(self.browse);self.go.clicked.connect(self.start);self.query.returnPressed.connect(self.start);stop.clicked.connect(self.stop);self.items.itemActivated.connect(self.open)
 def browse(self):
  path=QFileDialog.getExistingDirectory(self,'Search folder',self.root.text())
  if path:self.root.setText(path)
 def start(self):
  if self.job and self.job.isRunning():return
  root=Path(self.root.text()).expanduser()
  if not root.is_dir() or not self.query.text().strip():return
  self.items.clear();self.go.setEnabled(False);self.status.setText('Searching…');self.job=SearchJob(str(root),self.query.text().strip(),self.hidden.isChecked(),self);self.job.found.connect(lambda paths:self.items.addItems(paths));self.job.finished_search.connect(lambda count,denied,canceled:self.status.setText(f'{count} results'+(' • limit reached' if count>=1000 else '')+(' • canceled' if canceled else '')+f' • {denied} inaccessible folders'));self.job.finished.connect(lambda:self.go.setEnabled(True));self.job.start()
 def stop(self):
  if self.job:self.job.requestInterruption()
 def open(self,item):
  p=Path(item.text())
  if p.is_dir():self.desktop.files();self.desktop.windows['files'].content.navigate(p)
  else:self.desktop.open_path(p)
 def shutdown(self):
  self.stop();return not self.job or self.job.wait(1500)
