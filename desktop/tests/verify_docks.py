"""Dock model and Qt drag/drop checks, with isolated preferences and data."""
import os,sys,tempfile,json
from pathlib import Path
sandbox=tempfile.TemporaryDirectory(prefix='macaquestep-docks-')
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=sandbox.name+'/data';os.environ['XDG_CONFIG_HOME']=sandbox.name+'/config'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QMimeData,QPointF,QPoint
from PySide6.QtGui import QDragEnterEvent,QDropEvent,QMouseEvent,QDrag
import dock_workspace as docks
from dock_workspace import MIME,valid_entry
from drawers import load_drawers,INTERNAL,launch_entry
from backup_app import create_backup,validate_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.show();QTest.qWait(350)
def source(index):return {'entry':dict(d.side_launchers[index]),'source':{'type':'side','index':index}}
def drop(payload,widget,ctrl=False):
 mime=QMimeData();mime.setData(MIME,json.dumps({**payload,'token':d._dock_token}).encode());mods=Qt.ControlModifier if ctrl else Qt.NoModifier
 enter=QDragEnterEvent(QPoint(5,5),Qt.CopyAction|Qt.MoveAction,mime,Qt.LeftButton,mods);QApplication.sendEvent(widget,enter);assert enter.isAccepted()
 event=QDropEvent(QPointF(5,5),Qt.CopyAction|Qt.MoveAction,mime,Qt.LeftButton,mods);QApplication.sendEvent(widget,event);assert event.isAccepted()
try:
 for action in INTERNAL:
  method={'clock':'clock_app','paint':'paint_app','search':'search_files'}.get(action,action);assert callable(getattr(d,method,None)),action
 calls=[];paint=d.paint_app;search=d.search_files;d.paint_app=lambda:calls.append('paint');d.search_files=lambda:calls.append('search');launch_entry(d,{'name':'Paint','action':'paint'});launch_entry(d,{'name':'Search','action':'search'});assert calls==['paint','search'];d.paint_app=paint;d.search_files=search
 assert len(d.side_launchers)==22 and any(e['action']=='screenshot' for e in d.side_launchers)
 assert all(not b.icon().isNull() for b in d.side_widgets)
 # Additional columns remain available when explicitly requested.
 d.settings.setValue('dock_fit',True)
 # All launchers remain reachable with fitting, including at minimum desktop height.
 for width,height,count in [(1450,950,22),(850,600,22),(1100,600,100)]:
  entries=[{**d._dock_defaults[i%22],'id':'test:'+str(i)} for i in range(count)];d.write_location({'type':'side'},entries);d.resize(width,height);d.refresh_docks();QTest.qWait(90)
  assert d.dock_scroll.verticalScrollBar().maximum()==0,(height,count,d.dock_scroll.verticalScrollBar().maximum())
  assert all(b.isVisible() for b in d.side_widgets);assert 24<=d.effective_dock_size<=68
  assert d.side_widgets[-1].geometry().bottom()<d.dock_scroll.viewport().height()
  assert all(b.width()==b.height()==d.effective_dock_size for b in d.running_dock.buttons.values())
 d.restore_side_launchers();d.resize(1450,950);QTest.qWait(50)
 d.settings.setValue('dock_fit',False);d.settings.setValue('dock_size',68);d.fit_side_dock();QTest.qWait(30);assert d.dock_scroll.verticalScrollBar().maximum()>0
 d.settings.setValue('dock_fit',True);d.fit_side_dock();QTest.qWait(30);assert d.dock_scroll.verticalScrollBar().maximum()==0
 # A genuine Qt drop moves a side launcher into the active Clip.
 before=len(d.side_launchers);payload=source(3);drop(payload,d.clip.anchor);assert len(d.side_launchers)==before-1 and d.clip_entries()[0]['action']=='editor';assert len(d.clip.buttons)==1
 d.switch_workspace(1);assert not d.clip_entries() and not d.clip.buttons
 d.switch_workspace(0);assert len(d.clip.buttons)==1
 d.clip.toggle();assert not d.clip.grid_widget.isVisible();d.clip.toggle();assert d.clip.grid_widget.isVisible()
 # Ctrl-drop copies; same-dock drag reorders; stale sources are rejected.
 payload=source(0);drop(payload,d.clip.anchor,True);assert len(d.side_launchers)==before-1 and len(d.clip_entries())==2;assert d.clip_entries()[1]['id']!=payload['entry']['id']
 first=d.side_launchers[0]['id'];assert d.transfer_launcher(source(0),{'type':'side'});assert d.side_launchers[-1]['id']==first
 unchanged=list(d.side_launchers);assert not d.transfer_launcher({'entry':unchanged[0],'source':{'type':'side','index':999}},{'type':'clip','workspace':0});assert unchanged==d.side_launchers
 # Drawers have draggable icon shelves; transfers preserve custom command arguments without executing.
 d.drawer_shelf();shelf=d.windows['drawer-shelf'].content;assert len(shelf.buttons)==3
 payload={'entry':d.clip_entries()[0],'source':{'type':'clip','workspace':0,'index':0}};assert d.transfer_launcher(payload,{'type':'drawer','drawer':0});assert len(load_drawers(d.settings)[0]['entries'])==4
 command={'name':'Explicit command','command':'example "one argument"'};assert d.transfer_launcher({'entry':command,'source':{'type':'catalog'}},{'type':'clip','workspace':1},True);assert d.clip_entries(1)[0]['command']==command['command']
 drawer_entry=load_drawers(d.settings)[0]['entries'][-1];assert d.transfer_launcher({'entry':drawer_entry,'source':{'type':'drawer','drawer':0,'index':3}},{'type':'side'});assert len(load_drawers(d.settings)[0]['entries'])==3
 # Running tiles pin copies. Dropping onto the task dock now pins without launching.
 d.calculator();QTest.qWait(30);payload=d.running_drag('calculator');assert payload and payload['source']['type']=='running';assert d.transfer_launcher(payload,{'type':'clip','workspace':0});assert 'calculator' in d.windows
 called=[];launch=docks.launch_entry;docks.launch_entry=lambda desktop,entry:called.append(entry);original=list(d.side_launchers)
 drop(source(0),d.running_dock.panel);assert not called and d.side_launchers==original and d.is_pinned(original[0],'running');docks.launch_entry=launch
 # Exercise press + threshold drag through the installed source event filter and QDrag MIME.
 original_exec=QDrag.exec;seen=[]
 def simulated_drag(drag,*args):
  payload=d.dock_events.payload(drag.mimeData());assert payload and d._dock_dragging;seen.append(payload);assert d.transfer_launcher(payload,{'type':'clip','workspace':2});return Qt.MoveAction
 QDrag.exec=simulated_drag
 button=d.side_widgets[0];QTest.mousePress(button,Qt.LeftButton,pos=QPoint(5,5));move=QMouseEvent(QEvent.MouseMove,QPointF(35,35),QPointF(button.mapToGlobal(QPoint(35,35))),Qt.NoButton,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(button,move);QDrag.exec=original_exec;assert seen and not d._dock_dragging and d.clip_entries(2)
 # Process-local MIME validation rejects external, oversized and malformed launchers.
 assert valid_entry({'name':'Bad','action':[]}) is None
 for raw in (b'{}',json.dumps({'token':'other','entry':{'name':'Files','action':'files'},'source':{'type':'catalog'}}).encode(),b'x'*13000):
  mime=QMimeData();mime.setData(MIME,raw);assert d.dock_events.payload(mime) is None
 # Backups include Clip contents and fit preferences.
 backup=Path(sandbox.name)/'backup.zip';create_backup(d.store,d.settings,backup);_,prefs=validate_backup(backup);assert 'clip_launchers_0' in prefs and 'dock_launchers_v12' in prefs and prefs['dock_fit'] is True
 schedule_restore(backup);restored=QSettings(str(Path(sandbox.name)/'restored.ini'),QSettings.IniFormat);assert apply_pending_restore(restored);assert restored.value('clip_launchers_0')==d.settings.value('clip_launchers_0')
 side=list(d.side_launchers);clip=d.clip_entries(1);d.settings.sync();d.close();QTest.qWait(60);d2=Desktop();d2.show();QTest.qWait(350);assert d2.side_launchers==side and d2.clip_entries(1)==clip;d2.switch_workspace(1);assert len(d2.clip.buttons)==len(clip);d2.close();QTest.qWait(50)
 print('PASS workspace Clip, fit/no-scroll at 22/100 icons and small sizes, manual scrolling, Qt drop and mouse-drag MIME, move/copy/reorder, drawer transfers, running-pin and launch semantics, malformed-input rejection, backup/persistence, shutdown')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
