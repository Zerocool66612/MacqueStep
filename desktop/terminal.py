import sys,json,base64
from pathlib import Path
import pyte
from PySide6.QtCore import Qt,QProcess,QTimer,QEvent
from PySide6.QtGui import QFont,QTextCursor
from PySide6.QtWidgets import *
class TerminalView(QPlainTextEdit):
 def __init__(self,terminal):
  super().__init__();self.terminal=terminal;self.setReadOnly(True);self.setFont(QFont('monospace',11));self.setLineWrapMode(QPlainTextEdit.NoWrap)
 def event(self,event):
  if event.type()==QEvent.ShortcutOverride and event.key()==Qt.Key_Escape:event.accept();return True
  return super().event(event)
 def keyPressEvent(self,event):
  key=event.key();mods=event.modifiers()
  if mods & Qt.ControlModifier and mods & Qt.ShiftModifier:
   if key==Qt.Key_C:QApplication.clipboard().setText(self.textCursor().selectedText().replace('\u2029','\n'));return
   if key==Qt.Key_V:self.terminal.write(QApplication.clipboard().text().encode());return
  if mods & Qt.ShiftModifier and key in (Qt.Key_PageUp,Qt.Key_PageDown):
   (self.terminal.screen.prev_page if key==Qt.Key_PageUp else self.terminal.screen.next_page)();self.terminal.pending=True;self.terminal.render();return
  keys={Qt.Key_Return:b'\r',Qt.Key_Enter:b'\r',Qt.Key_Backspace:b'\x7f',Qt.Key_Tab:b'\t',Qt.Key_Escape:b'\x1b',Qt.Key_Up:b'\x1b[A',Qt.Key_Down:b'\x1b[B',Qt.Key_Right:b'\x1b[C',Qt.Key_Left:b'\x1b[D',Qt.Key_Home:b'\x1b[H',Qt.Key_End:b'\x1b[F',Qt.Key_Delete:b'\x1b[3~',Qt.Key_PageUp:b'\x1b[5~',Qt.Key_PageDown:b'\x1b[6~'}
  if mods & Qt.ControlModifier and Qt.Key_A<=key<=Qt.Key_Z:self.terminal.write(bytes([key-Qt.Key_A+1]));return
  if key in keys:self.terminal.write(keys[key]);return
  if event.text():self.terminal.write((b'\x1b' if mods & Qt.AltModifier else b'')+event.text().encode());return
  super().keyPressEvent(event)
 def resizeEvent(self,event):super().resizeEvent(event);self.terminal.resize_screen()
class Terminal(QWidget):
 def __init__(self):
  super().__init__();self.screen=pyte.HistoryScreen(80,24,history=3000);self.stream=pyte.ByteStream(self.screen);self.buffer=b'';self.pending=False;self.status=QLabel('Interactive shell • Ctrl+Shift+C/V: copy/paste • Shift+PageUp/Down: history')
  layout=QVBoxLayout(self);self.view=TerminalView(self);layout.addWidget(self.view,1);layout.addWidget(self.status);self.proc=QProcess(self);self.proc.setProcessChannelMode(QProcess.SeparateChannels);self.proc.readyReadStandardOutput.connect(self.read);self.proc.readyReadStandardError.connect(lambda:self.status.setText(bytes(self.proc.readAllStandardError()).decode(errors='replace')[-300:]));self.proc.finished.connect(lambda *_:self.status.setText('Shell exited — close this window and reopen Terminal to start again.'));self.proc.errorOccurred.connect(lambda *_:self.status.setText(self.proc.errorString()));self.proc.start(sys.executable,[str(Path(__file__).with_name('pty_bridge.py'))]);self.proc.started.connect(self.resize_screen)
  self.refresh=QTimer(self);self.refresh.timeout.connect(self.render);self.refresh.start(35)
 def send(self,value):
  if self.proc.state()==QProcess.Running:self.proc.write((json.dumps(value)+'\n').encode())
 def write(self,data):self.send({'write':base64.b64encode(data).decode()})
 def read(self):
  self.buffer+=bytes(self.proc.readAllStandardOutput())
  while b'\n' in self.buffer:
   line,self.buffer=self.buffer.split(b'\n',1)
   try:message=json.loads(line);self.stream.feed(base64.b64decode(message['data']));self.pending=True
   except (ValueError,KeyError):pass
 def render(self):
  if not self.pending:return
  self.pending=False
  if self.view.textCursor().hasSelection():return
  self.view.setPlainText('\n'.join(self.screen.display));cursor=self.view.textCursor();cursor.movePosition(QTextCursor.Start)
  for _ in range(min(self.screen.cursor.y,self.screen.lines-1)):cursor.movePosition(QTextCursor.Down)
  cursor.movePosition(QTextCursor.Right,QTextCursor.MoveAnchor,self.screen.cursor.x);self.view.setTextCursor(cursor)
 def resize_screen(self):
  if not hasattr(self,'view') or not hasattr(self,'proc'):return
  metrics=self.view.fontMetrics();cols=max(10,min(240,(self.view.viewport().width()-12)//max(1,metrics.horizontalAdvance('M'))));rows=max(2,min(80,(self.view.viewport().height()-10)//max(1,metrics.height())));self.screen.resize(rows,cols);self.send({'resize':[rows,cols]});self.pending=True
 def shutdown(self):
  if self.proc.state()!=QProcess.NotRunning:
   self.send({'close':True});self.proc.closeWriteChannel()
   if not self.proc.waitForFinished(1000):self.proc.terminate();self.proc.waitForFinished(500)
