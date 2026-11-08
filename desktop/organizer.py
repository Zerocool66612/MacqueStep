from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import *

class Notes(QWidget):
 def __init__(self,store):
  super().__init__();self.store=store;self.active=None;self.loading=False;self.dirty=False
  root=QVBoxLayout(self);bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Search notes…');bar.addWidget(self.search,1)
  for name,fn in [('New',self.new),('Delete',self.delete),('Export',self.export)]:b=QPushButton(name);b.clicked.connect(fn);bar.addWidget(b)
  root.addLayout(bar);split=QSplitter();self.items=QListWidget();split.addWidget(self.items);right=QWidget();v=QVBoxLayout(right);self.title=QLineEdit();self.title.setPlaceholderText('Note title');self.body=QPlainTextEdit();v.addWidget(self.title);v.addWidget(self.body);split.addWidget(right);split.setStretchFactor(1,1);root.addWidget(split,1);self.status=QLabel('Notes save automatically');root.addWidget(self.status)
  self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(450);self.timer.timeout.connect(self.flush)
  self.title.textEdited.connect(self.changed);self.body.textChanged.connect(self.changed);self.items.currentItemChanged.connect(self.select);self.search.textChanged.connect(self.filter)
  self.refresh()
  if self.items.count():self.items.setCurrentRow(0)
  else:self.new()
 def changed(self,*_):
  if not self.loading and self.active is not None:self.dirty=True;self.status.setText('Saving…');self.timer.start()
 def flush(self):
  if self.active is None or not self.dirty:return True
  try:self.store.save_note(self.active,self.title.text().strip() or 'Untitled note',self.body.toPlainText())
  except Exception as e:self.status.setText('Save failed: '+str(e));return False
  self.dirty=False;self.status.setText('Saved automatically')
  for i in range(self.items.count()):
   item=self.items.item(i)
   if item.data(Qt.UserRole)[0]==self.active:
    item.setText(self.title.text().strip() or 'Untitled note');item.setData(Qt.UserRole,(self.active,self.body.toPlainText()));break
  return True
 def refresh(self):
  self.items.blockSignals(True);self.items.clear()
  for n,title,body in self.store.notes():item=QListWidgetItem(title);item.setData(Qt.UserRole,(n,body));self.items.addItem(item)
  self.items.blockSignals(False);self.filter(self.search.text())
 def filter(self,s):
  for i in range(self.items.count()):
   item=self.items.item(i);item.setHidden(s.lower() not in (item.text()+' '+item.data(Qt.UserRole)[1]).lower())
 def select(self,current,previous):
  if not self.flush():
   self.items.blockSignals(True);self.items.setCurrentItem(previous);self.items.blockSignals(False);return
  if current is None:return
  self.loading=True;self.active=current.data(Qt.UserRole)[0]
  row=next((row for row in self.store.notes() if row[0]==self.active),None)
  if row:self.title.setText(row[1]);self.body.setPlainText(row[2])
  self.loading=False
 def new(self):
  if not self.flush():return
  n=self.store.add_note();self.search.clear();self.refresh();self.items.setCurrentRow(0)
 def delete(self):
  if self.active is None:return
  if QMessageBox.question(self,'Delete note','Delete this note permanently?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)!=QMessageBox.Yes:return
  self.timer.stop();self.store.delete_note(self.active);self.active=None;self.dirty=False;self.refresh()
  if self.items.count():self.items.setCurrentRow(0)
  else:self.new()
 def export(self):
  if not self.flush():return
  p=QFileDialog.getSaveFileName(self,'Export note',str(Path.home()/'note.txt'),'Text (*.txt)')[0]
  if p:
   try:
    from PySide6.QtCore import QSaveFile,QIODevice
    f=QSaveFile(p);data=(self.title.text()+'\n\n'+self.body.toPlainText()).encode()
    if not f.open(QIODevice.WriteOnly) or f.write(data)!=len(data) or not f.commit():raise OSError(f.errorString())
   except OSError as e:QMessageBox.warning(self,'Export',str(e))

class Tasks(QWidget):
 def __init__(self,store):
  super().__init__();self.store=store;v=QVBoxLayout(self);row=QHBoxLayout();self.entry=QLineEdit();self.entry.setPlaceholderText('Add a task…');add=QPushButton('Add');row.addWidget(self.entry,1);row.addWidget(add);v.addLayout(row);self.items=QListWidget();v.addWidget(self.items);self.status=QLabel();v.addWidget(self.status);clear=QPushButton('Clear completed');v.addWidget(clear)
  self.entry.returnPressed.connect(self.add);add.clicked.connect(self.add);self.items.itemChanged.connect(self.change);clear.clicked.connect(self.clear);self.refresh()
 def refresh(self):
  self.items.blockSignals(True);self.items.clear();rows=self.store.tasks()
  for n,title,done in rows:
   item=QListWidgetItem(title);item.setData(Qt.UserRole,n);item.setFlags(item.flags()|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Checked if done else Qt.Unchecked);self.items.addItem(item)
  self.items.blockSignals(False);self.status.setText(f'{sum(not row[2] for row in rows)} remaining • {len(rows)} total')
 def add(self):
  if self.entry.text().strip():self.store.add_task(self.entry.text().strip());self.entry.clear();self.refresh()
 def change(self,item):self.store.set_task(item.data(Qt.UserRole),item.checkState()==Qt.Checked);self.refresh()
 def clear(self):self.store.clear_done();self.refresh()
