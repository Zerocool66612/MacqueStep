from pathlib import Path
from PySide6.QtCore import Qt,QPoint,QRect,QSaveFile,QIODevice
from PySide6.QtGui import QImage,QPainter,QPen,QColor,QImageReader
from PySide6.QtWidgets import *
class Canvas(QWidget):
 def __init__(self):
  super().__init__();self.image=QImage(1200,800,QImage.Format_ARGB32);self.image.fill(Qt.white);self.setFixedSize(self.image.size());self.color=QColor('#168b82');self.width=5;self.tool='Brush';self.undo_stack=[];self.dirty=False;self.start=None;self.last=None;self.end=None
 def snapshot(self):self.undo_stack.append(self.image.copy());self.undo_stack=self.undo_stack[-8:]
 def paintEvent(self,event):
  p=QPainter(self);p.drawImage(0,0,self.image)
  if self.start is not None and self.tool in ('Line','Rectangle','Ellipse'):self.shape(p,self.start,self.end or self.start)
 def shape(self,p,start,end):
  p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(self.color,self.width,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));rect=QRect(start,end).normalized()
  if self.tool=='Line':p.drawLine(start,end)
  elif self.tool=='Rectangle':p.drawRect(rect)
  elif self.tool=='Ellipse':p.drawEllipse(rect)
 def stroke(self,a,b):
  p=QPainter(self.image);p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(QColor('white') if self.tool=='Eraser' else self.color,self.width,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.drawLine(a,b);p.end();self.update()
 def mousePressEvent(self,event):
  if event.button()==Qt.LeftButton:self.snapshot();self.start=event.position().toPoint();self.last=self.start;self.end=self.start;self.dirty=True;self.stroke(self.start,self.start) if self.tool in ('Brush','Eraser') else None
 def mouseMoveEvent(self,event):
  if self.start is None:return
  self.end=event.position().toPoint()
  if self.tool in ('Brush','Eraser'):self.stroke(self.last,self.end);self.last=self.end
  else:self.update()
 def mouseReleaseEvent(self,event):
  if self.start is None:return
  if self.tool not in ('Brush','Eraser'):
   p=QPainter(self.image);self.shape(p,self.start,event.position().toPoint());p.end()
  self.start=None;self.update()
 def undo(self):
  if self.undo_stack:self.image=self.undo_stack.pop();self.setFixedSize(self.image.size());self.dirty=True;self.update()
class Paint(QWidget):
 def __init__(self):
  super().__init__();v=QVBoxLayout(self);bar=QHBoxLayout();self.canvas=Canvas();tool=QComboBox();tool.addItems(['Brush','Eraser','Line','Rectangle','Ellipse']);tool.currentTextChanged.connect(lambda s:setattr(self.canvas,'tool',s));bar.addWidget(tool)
  for title,fn in [('Color',self.color),('Undo',self.canvas.undo),('Clear',self.clear),('Open',self.open),('Save PNG',self.save)]:b=QPushButton(title);b.clicked.connect(fn);bar.addWidget(b)
  v.addLayout(bar);row=QHBoxLayout();row.addWidget(QLabel('Brush size'));width=QSlider(Qt.Horizontal);width.setRange(1,50);width.setValue(5);width.valueChanged.connect(lambda n:setattr(self.canvas,'width',n));row.addWidget(width,1);v.addLayout(row);scroll=QScrollArea();scroll.setWidget(self.canvas);v.addWidget(scroll,1);self.status=QLabel('1200 × 800 • Draw on the canvas');v.addWidget(self.status)
 def color(self):
  c=QColorDialog.getColor(self.canvas.color,self)
  if c.isValid():self.canvas.color=c
 def discard(self):return not self.canvas.dirty or QMessageBox.question(self,'Unsaved drawing','Discard unsaved changes?',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes
 def clear(self):
  if self.discard():self.canvas.snapshot();self.canvas.image.fill(Qt.white);self.canvas.dirty=True;self.canvas.update()
 def open(self):
  if not self.discard():return
  name=QFileDialog.getOpenFileName(self,'Open image',str(Path.home()),'Images (*.png *.jpg *.jpeg *.bmp *.webp)')[0]
  if not name:return
  reader=QImageReader(name);reader.setAutoTransform(True);size=reader.size()
  if size.isValid() and size.width()*size.height()>16_000_000:QMessageBox.warning(self,'Image','Choose an image under 16 megapixels.');return
  image=reader.read()
  if image.isNull():QMessageBox.warning(self,'Image',reader.errorString());return
  self.canvas.snapshot();self.canvas.image=image.convertToFormat(QImage.Format_ARGB32);self.canvas.setFixedSize(image.size());self.canvas.dirty=False;self.canvas.update();self.status.setText(Path(name).name)
 def save(self):
  name=QFileDialog.getSaveFileName(self,'Save PNG',str(Path.home()/'drawing.png'),'PNG (*.png)')[0]
  if not name:return False
  if not name.lower().endswith('.png'):name+='.png'
  file=QSaveFile(name)
  if not file.open(QIODevice.WriteOnly) or not self.canvas.image.save(file,'PNG') or not file.commit():QMessageBox.warning(self,'Save',file.errorString());return False
  self.canvas.dirty=False;self.status.setText('Saved '+Path(name).name);return True
