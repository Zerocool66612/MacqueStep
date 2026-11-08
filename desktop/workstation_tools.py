"""Read-only workstation tools and explicit, user-driven file navigation."""
import os,json,time,hashlib,stat,heapq
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QRect
from PySide6.QtWidgets import *

def readable_size(n):
 for suffix in ('B','KiB','MiB','GiB','TiB'):
  if n<1024 or suffix=='TiB':return f'{n:.1f} {suffix}'
  n/=1024

class ReadJob(QThread):
 result=Signal(object);failed=Signal(str)
 def __init__(self,fn,parent=None):super().__init__(parent);self.fn=fn
 def run(self):
  try:self.result.emit(self.fn(self.isInterruptionRequested))
  except Exception as error:self.failed.emit(str(error))
class ReadPanel(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.job=None;self.v=QVBoxLayout(self);self.status=QLabel();self.status.setWordWrap(True);self.status.setTextFormat(Qt.PlainText);self.v.addWidget(self.status)
 def work(self,fn,callback):
  if self.job and self.job.isRunning():self.status.setText('Wait for the current scan or cancel it.');return False
  job=ReadJob(fn,self);self.job=job;job.result.connect(callback);job.failed.connect(lambda message:self.status.setText('Could not finish: '+message));job.finished.connect(lambda:self.finished(job));job.start();return True
 def finished(self,job):
  if self.job is job:self.job=None
  job.deleteLater()
 def cancel(self):
  if self.job:self.job.requestInterruption();self.status.setText('Canceling…')
 def can_close(self):
  if self.job and self.job.isRunning():self.cancel();return False
  return True

def checksum(path,cancel=lambda:False):
 p=Path(path)
 if p.is_symlink() or not p.is_file():raise ValueError('Choose a regular file, not a folder or symbolic link.')
 # O_NOFOLLOW rejects a substituted symlink at open time on Linux.
 fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));sha256=hashlib.sha256();sha512=hashlib.sha512();count=0
 with os.fdopen(fd,'rb') as stream:
  before=os.fstat(stream.fileno())
  if not stat.S_ISREG(before.st_mode):raise ValueError('Special files cannot be hashed.')
  while True:
   if cancel():raise ValueError('Checksum canceled.')
   block=stream.read(1024*1024)
   if not block:break
   sha256.update(block);sha512.update(block);count+=len(block)
  after=os.fstat(stream.fileno())
  if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('The file changed during hashing. Try again after saving it.')
 return {'path':str(p),'bytes':count,'sha256':sha256.hexdigest(),'sha512':sha512.hexdigest()}
class Checksums(ReadPanel):
 def __init__(self,d,path=None):
  super().__init__(d);row=QHBoxLayout();self.v.addLayout(row);self.path=QLineEdit(str(path or ''));self.path.setPlaceholderText('Choose a file to verify…');row.addWidget(self.path,1);button=QPushButton('Choose…');button.clicked.connect(self.choose);row.addWidget(button)
  row=QHBoxLayout();self.v.addLayout(row)
  for title,fn in [('Calculate',self.calculate),('Cancel',self.cancel),('Copy SHA-256',self.copy)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  self.output=QPlainTextEdit();self.output.setReadOnly(True);self.v.addWidget(self.output,1);self.expected=QLineEdit();self.expected.setPlaceholderText('Optional expected SHA-256 digest (64 hex characters)');self.expected.textChanged.connect(self.compare);self.v.addWidget(self.expected);self.digest=None
  self.status.setText('SHA-256 and SHA-512 are calculated locally. No file is uploaded.')
 def choose(self):
  p=QFileDialog.getOpenFileName(self,'Choose file for checksums',str(Path.home()))[0]
  if p:self.path.setText(p)
 def calculate(self):
  p=self.path.text();self.digest=None;self.output.clear();self.status.setText('Calculating…')
  self.work(lambda cancel:checksum(p,cancel),self.loaded)
 def loaded(self,data):
  self.digest=data;self.output.setPlainText(data['path']+'\n'+readable_size(data['bytes'])+'\n\nSHA-256\n'+data['sha256']+'\n\nSHA-512\n'+data['sha512']);self.compare();self.d.record_activity('Checksums calculated',data['path'])
 def compare(self):
  if not self.digest:return
  expected=self.expected.text().strip().lower()
  if not expected:self.status.setText('Checksums ready.');return
  if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):self.status.setText('Enter exactly 64 hexadecimal characters for SHA-256.');return
  self.status.setText('SHA-256 matches.' if expected==self.digest['sha256'] else 'SHA-256 does not match.')
 def copy(self):
  if self.digest:QApplication.clipboard().setText(self.digest['sha256'])

def folder_usage(path,cancel=lambda:False,limit=100000):
 root=Path(path).expanduser().absolute()
 if root.is_symlink() or not root.is_dir():raise ValueError('Choose an accessible directory, not a symbolic link.')
 buckets={};largest=[];count=0;errors=0;limited=False;stack=[root]
 while stack:
  if cancel():raise ValueError('Scan canceled.')
  directory=stack.pop()
  try:
   with os.scandir(directory) as entries:
    for entry in entries:
     if cancel():raise ValueError('Scan canceled.')
     count+=1
     if count>limit:limited=True;break
     try:
      if entry.is_symlink():continue
      p=Path(entry.path);metadata=entry.stat(follow_symlinks=False)
      if stat.S_ISDIR(metadata.st_mode):stack.append(p);continue
      if not stat.S_ISREG(metadata.st_mode):continue
      key=p.relative_to(root).parts[0];buckets[key]=buckets.get(key,0)+metadata.st_size
      item=(metadata.st_size,str(p))
      if len(largest)<100:heapq.heappush(largest,item)
      elif item>largest[0]:heapq.heapreplace(largest,item)
     except OSError:errors+=1
  except OSError:errors+=1
  if limited:break
 return {'root':str(root),'entries':min(count,limit),'limited':limited,'errors':errors,'total':sum(buckets.values()),'buckets':sorted(buckets.items(),key=lambda x:x[1],reverse=True),'largest':sorted(largest,reverse=True)}
class DiskUsage(ReadPanel):
 def __init__(self,d):
  super().__init__(d);row=QHBoxLayout();self.v.addLayout(row);self.path=QLineEdit(str(Path.home()));row.addWidget(self.path,1)
  for title,fn in [('Choose…',self.choose),('Scan',self.scan),('Cancel',self.cancel)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  self.tabs=QTabWidget();self.v.addWidget(self.tabs,1);self.folders=QTreeWidget();self.folders.setHeaderLabels(['Top-level item','Logical file size']);self.tabs.addTab(self.folders,'Folder totals');self.largest=QTreeWidget();self.largest.setHeaderLabels(['File','Logical size']);self.tabs.addTab(self.largest,'100 largest files')
  self.folders.itemActivated.connect(self.open_item);self.largest.itemActivated.connect(self.open_item);self.status.setText('Read-only scan: logical file sizes, not allocated disk space. Symlinks and special files are skipped. Limit: 100,000 entries.')
 def choose(self):
  p=QFileDialog.getExistingDirectory(self,'Choose folder to analyze',self.path.text())
  if p:self.path.setText(p)
 def scan(self):
  p=self.path.text();self.status.setText('Scanning…');self.work(lambda cancel:folder_usage(p,cancel),self.loaded)
 def loaded(self,data):
  self.folders.clear();self.largest.clear()
  for name,size in data['buckets']:
   item=QTreeWidgetItem([name,readable_size(size)]);item.setData(0,Qt.UserRole,str(Path(data['root'])/name));self.folders.addTopLevelItem(item)
  for size,path in data['largest']:
   item=QTreeWidgetItem([path,readable_size(size)]);item.setData(0,Qt.UserRole,path);self.largest.addTopLevelItem(item)
  self.status.setText(readable_size(data['total'])+f" · {data['entries']:,} entries · {data['errors']} inaccessible items"+(' · entry limit reached; partial results' if data['limited'] else ''));self.d.record_activity('Disk scan finished',data['root'])
 def open_item(self,item,*_):
  p=Path(item.data(0,Qt.UserRole));self.d.files();self.d.windows['files'].content.navigate(p if p.is_dir() else p.parent)

def system_sample(proc=Path('/proc')):
 first=(proc/'stat').read_text().splitlines()[0].split()[1:];cpu=[int(x) for x in first[:8]];memory={}
 for line in (proc/'meminfo').read_text().splitlines():
  fields=line.replace(':','').split()
  if len(fields)>1:memory[fields[0]]=int(fields[1])*1024
 received=sent=0
 for line in (proc/'net/dev').read_text().splitlines()[2:]:
  if ':' not in line:continue
  name,values=line.split(':',1)
  if name.strip()=='lo':continue
  fields=values.split();received+=int(fields[0]);sent+=int(fields[8])
 return {'cpu_total':sum(cpu),'cpu_idle':cpu[3]+(cpu[4] if len(cpu)>4 else 0),'ram_total':memory.get('MemTotal',0),'ram_used':max(0,memory.get('MemTotal',0)-memory.get('MemAvailable',memory.get('MemFree',0))),'swap_total':memory.get('SwapTotal',0),'swap_used':max(0,memory.get('SwapTotal',0)-memory.get('SwapFree',0)),'received':received,'sent':sent,'time':time.monotonic()}
class SystemMonitor(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.previous=None;v=QVBoxLayout(self);self.bars={};form=QFormLayout();v.addLayout(form)
  for name in ('CPU','Memory','Swap'):bar=QProgressBar();bar.setRange(0,100);form.addRow(name,bar);self.bars[name]=bar
  self.detail=QLabel();self.detail.setWordWrap(True);self.detail.setTextFormat(Qt.PlainText);v.addWidget(self.detail);self.network=QLabel();v.addWidget(self.network);self.pause=QCheckBox('Pause sampling');v.addWidget(self.pause);button=QPushButton('Audio, brightness & battery…');button.clicked.connect(d.system_controls);v.addWidget(button);v.addStretch();self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(1500);self.refresh()
 def refresh(self):
  if self.pause.isChecked():return
  try:
   data=system_sample();old=self.previous;self.previous=data
   for key,total,used in [('Memory','ram_total','ram_used'),('Swap','swap_total','swap_used')]:self.bars[key].setValue(round(100*data[used]/data[total]) if data[total] else 0)
   if old:
    delta=data['cpu_total']-old['cpu_total'];idle=data['cpu_idle']-old['cpu_idle'];self.bars['CPU'].setValue(max(0,min(100,round(100*(1-idle/delta)))) if delta>0 else 0);seconds=max(.01,data['time']-old['time']);self.network.setText('Network ↓ '+readable_size(max(0,data['received']-old['received'])/seconds)+'/s   ↑ '+readable_size(max(0,data['sent']-old['sent'])/seconds)+'/s')
   self.detail.setText('Memory: '+readable_size(data['ram_used'])+' / '+readable_size(data['ram_total'])+'\nSwap: '+readable_size(data['swap_used'])+' / '+readable_size(data['swap_total'])+'\nRead-only system sampling. Network totals exclude loopback.')
  except (OSError,ValueError,IndexError) as error:self.detail.setText('System sampling unavailable: '+str(error))
 def can_close(self):return True
class RecentDocuments(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);self.items=QListWidget();v.addWidget(self.items,1);row=QHBoxLayout();v.addLayout(row)
  for title,fn in [('Open',self.open),('Show enclosing folder',self.folder),('Refresh',self.refresh),('Clear recent list…',self.clear)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  note=QLabel('Only files you open through MacaqueSTEP are recorded. Clearing this list does not delete files.');note.setWordWrap(True);v.addWidget(note);self.items.itemActivated.connect(lambda *_:self.open());self.refresh()
 def refresh(self):
  self.items.clear()
  for path in self.d.recent_paths():
   item=QListWidgetItem(path+(' · missing' if not Path(path).is_file() else ''));item.setData(Qt.UserRole,path);self.items.addItem(item)
 def selected(self):item=self.items.currentItem();return item.data(Qt.UserRole) if item else None
 def open(self):
  path=self.selected()
  if path and Path(path).is_file():self.d.open_path(Path(path))
 def folder(self):
  path=self.selected()
  if path and Path(path).parent.is_dir():self.d.files();self.d.windows['files'].content.navigate(Path(path).parent)
 def clear(self):
  if QMessageBox.question(self,'Recent documents','Clear the recent-document history?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:self.d.settings.setValue('recent_documents','[]');self.refresh()
class ActivityCenter(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);self.items=QListWidget();v.addWidget(self.items,1);row=QHBoxLayout();v.addLayout(row);clear=QPushButton('Clear session log');clear.clicked.connect(self.clear);row.addWidget(clear);refresh=QPushButton('Refresh');refresh.clicked.connect(self.refresh);row.addWidget(refresh);note=QLabel('Built-in desktop activity for this session only. This is not a system-wide notification service.');note.setWordWrap(True);v.addWidget(note);self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(2000);self.refresh()
 def refresh(self):
  rows=getattr(self.d,'activity_rows',[])
  if self.items.count()==len(rows) and self.items.count() and self.items.item(0).data(Qt.UserRole)==rows[0]['id']:return
  self.items.clear()
  for event in rows:
   item=QListWidgetItem(event['time']+'  '+event['title']+('\n'+event['detail'] if event['detail'] else ''));item.setData(Qt.UserRole,event['id']);self.items.addItem(item)
 def clear(self):self.d.activity_rows=[];self.items.clear()
 def can_close(self):return True
class DualPaneFiles(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;v=QVBoxLayout(self);row=QHBoxLayout();v.addLayout(row)
  for title,left,move in [('Copy →',True,False),('← Copy',False,False),('Move →',True,True),('← Move',False,True)]:b=QPushButton(title);b.clicked.connect(lambda checked=False,l=left,m=move:self.transfer(l,m));row.addWidget(b)
  from file_manager import FileManager
  self.left=FileManager(d,compact=True);self.right=FileManager(d,compact=True);split=QSplitter();split.setMinimumWidth(760);split.addWidget(self.left);split.addWidget(self.right);self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setWidget(split);v.addWidget(self.scroll,1);note=QLabel('Select items in the source pane, then copy or move them to the folder shown in the other pane. Existing files are never overwritten.');note.setWordWrap(True);v.addWidget(note)
 def active_file_manager(self,target=None):
  if target is not None and (target is self.right or self.right.isAncestorOf(target)):return self.right
  return self.left
 def transfer(self,left,move):
  source,destination=(self.left,self.right) if left else (self.right,self.left);paths=source.selected_paths()
  if not paths:
   selected=source.selected();paths=[selected] if selected else []
  if paths:
   if move and QMessageBox.question(self,'Move selected items',f'Move {len(paths)} items to the other pane’s folder?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
   source.start_transfer([str(p) for p in paths],destination.path.text(),move)
 def can_close(self):
  if self.left.jobs or self.right.jobs:return False
  return True

class WorkstationTools:
 def tool_window(self,key,title,cls):
  if key in self.windows:self.reopen(key);return self.windows[key]
  return self.window(key,title,cls(self),(60,45,1050 if key=='dual-files' else 820,640))
 def dual_files(self):return self.tool_window('dual-files','Two-Pane Files',DualPaneFiles)
 def disk_usage(self):return self.tool_window('disk-usage','Disk Usage',DiskUsage)
 def system_monitor(self):return self.tool_window('system-monitor','System Monitor',SystemMonitor)
 def checksum_tool(self,path=None):
  window=self.tool_window('checksums','File Checksums',Checksums)
  if path:window.content.path.setText(str(path))
  return window
 def recent_documents(self):return self.tool_window('recent','Recent Documents',RecentDocuments)
 def activity_center(self):return self.tool_window('activity','Activity Center',ActivityCenter)
 def record_activity(self,title,detail=''):
  rows=getattr(self,'activity_rows',[]);rows.insert(0,{'id':time.time_ns(),'time':time.strftime('%H:%M:%S'),'title':str(title)[:100],'detail':str(detail)[:500]});self.activity_rows=rows[:200]
 def recent_paths(self):
  try:rows=json.loads(self.settings.value('recent_documents','[]'))
  except (ValueError,TypeError):return []
  return [p for p in rows if isinstance(p,str) and len(p)<4096][:50] if isinstance(rows,list) else []
 def remember_document(self,path):
  try:
   p=Path(path).expanduser().absolute()
   if p.is_file():
    rows=[str(p)]+[old for old in self.recent_paths() if old!=str(p)];self.settings.setValue('recent_documents',json.dumps(rows[:50]));self.record_activity('Opened document',str(p))
  except OSError:pass
 def open_path(self,path):
  result=super().open_path(path);self.remember_document(path);return result
