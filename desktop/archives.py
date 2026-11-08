import zipfile,tarfile,shutil
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
class Archives(QWidget):
 def __init__(self,path=None):
  super().__init__();self.archive=None;self.path=None;self.members=[];v=QVBoxLayout(self);row=QHBoxLayout()
  for title,fn in [('Open archive',self.choose),('Preview text',self.preview),('Extract selected file',self.extract)]:b=QPushButton(title);b.clicked.connect(fn);row.addWidget(b)
  v.addLayout(row);self.items=QTreeWidget();self.items.setHeaderLabels(['Name','Size','Type']);self.items.setColumnWidth(0,440);v.addWidget(self.items,1);self.status=QLabel('ZIP and TAR archives • selected-file extraction up to 16 MB');v.addWidget(self.status)
  if path:self.load(path)
 def choose(self):
  p=QFileDialog.getOpenFileName(self,'Open archive',str(Path.home()),'Archives (*.zip *.tar *.tar.gz *.tgz *.tar.bz2 *.tar.xz)')[0]
  if p:self.load(p)
 def load(self,path):
  try:
   if Path(path).stat().st_size>256*1024**2:raise ValueError('Choose an archive smaller than 256 MB for this preview.')
   archive=zipfile.ZipFile(path) if zipfile.is_zipfile(path) else tarfile.open(path,'r:*');members=[]
   for i,info in enumerate(archive.infolist() if isinstance(archive,zipfile.ZipFile) else archive):
    if i>=10000:archive.close();raise ValueError('Archive contains more than 10,000 entries.')
    name=info.filename if hasattr(info,'filename') else info.name;size=info.file_size if hasattr(info,'file_size') else info.size
    regular=not info.is_dir() and ((info.external_attr>>16)&0o170000)!=0o120000 if isinstance(archive,zipfile.ZipFile) else info.isfile()
    members.append((name,size,regular,info))
   if self.archive:self.archive.close()
   self.archive=archive;self.path=str(path);self.members=members;self.items.clear()
   for i,(name,size,regular,_) in enumerate(members):item=QTreeWidgetItem([name,f'{size:,}', 'File' if regular else 'Folder / link']);item.setData(0,Qt.UserRole,i);self.items.addTopLevelItem(item)
   self.status.setText(f'{Path(path).name} • {len(members)} entries • no files extracted')
  except (OSError,ValueError,zipfile.BadZipFile,tarfile.TarError) as e:QMessageBox.warning(self,'Archive',str(e))
 def selected(self):
  item=self.items.currentItem()
  if item is None:return None
  return self.members[item.data(0,Qt.UserRole)]
 def read_member(self,limit):
  member=self.selected()
  if member is None:return None
  name,size,regular,info=member
  if not regular:raise ValueError('Select a regular file; folders and links are not extracted.')
  if size>limit:raise ValueError(f'Selected file exceeds the {limit//1024**2} MB limit.')
  stream=self.archive.open(info) if isinstance(self.archive,zipfile.ZipFile) else self.archive.extractfile(info)
  with stream:data=stream.read(limit+1)
  if len(data)>limit:raise ValueError('Expanded file exceeds the size limit.')
  return name,data
 def preview(self):
  try:
   value=self.read_member(1024**2)
   if value is None:return
   name,data=value;text=data.decode('utf-8');dialog=QDialog(self);dialog.setWindowTitle(name);dialog.resize(700,450);v=QVBoxLayout(dialog);edit=QPlainTextEdit();edit.setReadOnly(True);edit.setPlainText(text);v.addWidget(edit);dialog.exec()
  except (ValueError,OSError,RuntimeError,zipfile.BadZipFile,tarfile.TarError) as e:QMessageBox.warning(self,'Preview',str(e))
 def extract(self):
  try:
   value=self.read_member(16*1024**2)
   if value is None:return
   name,data=value;folder=QFileDialog.getExistingDirectory(self,'Extract file into folder',str(Path.home()))
   if not folder:return
   # Flatten the member name, reject platform path separators, and never overwrite.
   filename=name.replace('\\','/').split('/')[-1]
   if filename in ('','.','..'):raise ValueError('Unsupported entry name.')
   path=Path(folder)/filename
   with path.open('xb') as f:
    try:f.write(data)
    except BaseException:f.close();path.unlink(missing_ok=True);raise
   self.status.setText('Extracted '+str(path))
  except (ValueError,OSError,RuntimeError,zipfile.BadZipFile,tarfile.TarError) as e:QMessageBox.warning(self,'Extract',str(e))
 def shutdown(self):
  if self.archive:self.archive.close();self.archive=None
