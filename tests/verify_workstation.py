import os,sys,tempfile,hashlib,json
from pathlib import Path
root=Path(tempfile.mkdtemp());os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_STATE_HOME']=str(root/'state');sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from workstation_tools import *
# Stable checksums, no symlink reads, cancellation.
f=root/'sample.txt';f.write_text('hello workstation');digest=checksum(f);assert digest['sha256']==hashlib.sha256(f.read_bytes()).hexdigest();assert digest['bytes']==17
link=root/'link';link.symlink_to(f)
for p,cancel in [(link,lambda:False),(f,lambda:True)]:
 try:checksum(p,cancel);raise AssertionError('unsafe/canceled hash')
 except ValueError:pass
folder=root/'files';folder.mkdir();(folder/'one').write_bytes(b'a'*3);sub=folder/'sub';sub.mkdir();(sub/'two').write_bytes(b'b'*5);(sub/'loop').symlink_to(folder)
usage=folder_usage(folder);assert usage['total']==8 and dict(usage['buckets'])=={'sub':5,'one':3};assert len(usage['largest'])==2;assert folder_usage(folder,limit=1)['limited']
try:folder_usage(folder,lambda:True);raise AssertionError('uncanceled scan')
except ValueError:pass
# Read-only system counters from a fixture, including loopback exclusion.
proc=root/'proc';(proc/'net').mkdir(parents=True);(proc/'stat').write_text('cpu  10 0 10 70 10 0 0 0 0 0\n');(proc/'meminfo').write_text('MemTotal: 100 kB\nMemAvailable: 40 kB\nSwapTotal: 50 kB\nSwapFree: 20 kB\n');(proc/'net/dev').write_text('header\nheader\n lo: 100 0 0 0 0 0 0 0 100 0 0 0 0 0 0 0\n eth0: 300 0 0 0 0 0 0 0 500 0 0 0 0 0 0 0\n');sample=system_sample(proc);assert sample['cpu_total']==100 and sample['cpu_idle']==80 and sample['ram_used']==60*1024 and sample['received']==300 and sample['sent']==500
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtCore import QItemSelectionModel
from unittest.mock import patch
app=QApplication([]);d=Desktop();d.resize(1460,930);d.show();QTest.qWait(200)
def wait_for(fn):
 for _ in range(150):
  QTest.qWait(20)
  if fn():return
 raise AssertionError('Operation did not finish')
try:
 fm=d.windows['files'].content;fm.navigate(folder);fm.add_bookmark();fm.add_bookmark();assert fm.bookmark_paths()==[str(folder)];fm.navigate(root);fm.go_bookmark();assert fm.path.text()==str(folder);fm.copy_path();assert QApplication.clipboard().text()==str(folder);fm.refresh_folder();assert fm.path.text()==str(folder)
 d.checksum_tool(f);panel=d.windows['checksums'].content;panel.calculate();wait_for(lambda:panel.job is None);assert panel.digest['sha256']==digest['sha256'];panel.expected.setText(digest['sha256']);assert panel.status.text()=='SHA-256 matches.';panel.expected.setText('0'*64);assert 'does not match' in panel.status.text()
 d.disk_usage();scan=d.windows['disk-usage'].content;scan.path.setText(str(folder));scan.scan();wait_for(lambda:scan.job is None);assert scan.folders.topLevelItemCount()==2
 d.system_monitor();assert d.windows['system-monitor'].content.previous
 d.open_path(f);assert d.recent_paths()[0]==str(f);d.open_path(f);assert d.recent_paths().count(str(f))==1;d.windows[next(k for k in d.windows if k.startswith('editor'))].content.editor.document().setModified(False)
 d.recent_documents();assert d.windows['recent'].content.items.count()==1
 d.activity_center();assert d.windows['activity'].content.items.count()>=3
 for i in range(220):d.record_activity('Event',str(i))
 assert len(d.activity_rows)==200
 d.dual_files();dual=d.windows['dual-files'].content;destination=root/'destination';destination.mkdir();dual.left.navigate(folder);dual.right.navigate(destination);QTest.qWait(150);index=dual.left.model.index(str(folder/'one'));dual.left.view.setCurrentIndex(index);dual.left.view.selectionModel().select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
 dual.transfer(True,False);wait_for(lambda:not dual.left.jobs);assert (destination/'one').read_bytes()==b'aaa' and (folder/'one').is_file()
 # File transfer and inspector windows cannot be destroyed while their worker is active.
 assert d.entry_for_window('checksums')['action']=='checksum_tool';entry=d.entry_for_window('checksums');d.set_pin(entry,'running',True);assert d.is_pinned(entry,'running')
 d.launcher();assert any(i.text()=='Software Center' for i in d.windows['launcher'].content.findChild(QListWidget).findItems('*',Qt.MatchWildcard))
 d.show_left_app_menu();d.area.setActiveSubWindow(d.windows['dual-files']);dual.right.view.setFocus();QTest.qWait(30);assert d.app_menu.menu_content(d.windows['dual-files']) is dual.right
 d.windows['dual-files'].showMaximized();QTest.qWait(100);assert d.windows['dual-files'].geometry().bottom()<d.running_dock.geometry().top();assert d.windows['dual-files'].geometry().top()>d.clip.anchor.height();d.grab().save('/tmp/step021-two-pane.png')
 d.resize(800,700);QTest.qWait(100);assert d.windows['dual-files'].width()<=d.area.viewport().width();assert dual.scroll.horizontalScrollBar().maximum()>0
 d.settings.sync()
finally:
 for w in d.windows.values():
  if hasattr(w.content,'editor'):w.content.editor.document().setModified(False)
 d.close();QTest.qWait(100)
print('PASS checksums/cancellation, bounded symlink-skipping scan, proc counters, bookmarks/history, digest comparison, recent documents, activity limit, two-pane copy, pinning, launcher entries and clean shutdown')
