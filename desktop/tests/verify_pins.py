"""Check pin lifecycle, menu toggles, deduplication, scope, and backup persistence."""
import os,sys,tempfile,json
from pathlib import Path
sandbox=tempfile.TemporaryDirectory(prefix='step-pins-');root=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(root/'data');os.environ['XDG_CONFIG_HOME']=str(root/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from pinning import pin_group
from backup_app import create_backup,validate_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.show();QTest.qWait(300)
calculator={'name':'Calculator','action':'calculator'};editor={'name':'Text Editor','action':'editor'}
def flush():QTest.qWait(40)
try:
 # Pin a closed app: icon is visible without launching it, and duplicate pins are ignored.
 assert d.set_pin(calculator,'running');flush();group=pin_group(calculator);assert group in d.running_dock.buttons and 'calculator' not in d.windows
 assert d.running_dock.buttons[group].property('pinnedApp');assert d.running_dock.buttons[group].property('windowCount')==0
 assert 'not running' in d.running_dock.buttons[group].toolTip()
 assert d.set_pin(calculator,'running');assert len(d.bottom_pins())==1
 # Menu launches closed pins. The same tile becomes the app's running indicator.
 menu=d.running_dock.context_menu(group);next(a for a in menu.actions() if a.text()=='Launch application').trigger();flush();assert 'calculator' in d.windows
 assert d.running_dock.groups()[group]==['calculator'] and 'calculator' not in d.running_dock.buttons
 d.windows['calculator'].close();flush();assert group in d.running_dock.buttons and d.running_dock.buttons[group].property('windowCount')==0
 d.running_dock.activate_group(group);flush();assert 'calculator' in d.windows
 # Unpinning a running app leaves its windows alive and returns its ordinary task tile.
 d.set_pin(calculator,'running',False);flush();assert 'calculator' in d.windows and group not in d.running_dock.buttons and 'calculator' in d.running_dock.buttons
 d.set_pin(calculator,'running');flush();menu=d.running_dock.context_menu(group)
 labels=[action.text() for action in menu.actions()];assert labels.count('Unpin from running-app dock')==1
 next(a for a in menu.actions() if a.text()=='Unpin from running-app dock').trigger();flush();assert not d.is_pinned(calculator,'running') and 'calculator' in d.windows
 # Side pin/unpin affects launchers only, not a running app.
 d.set_pin(calculator,'side',False);assert not d.is_pinned(calculator,'side') and 'calculator' in d.windows
 menu=QMenu();d.pin_menu(menu,calculator);next(a for a in menu.actions() if a.text()=='Pin to side dock').trigger();assert d.is_pinned(calculator,'side')
 count=len(d.side_launchers);d.set_pin(calculator,'side');assert len(d.side_launchers)==count
 # Grouping pins coalesces matching document windows, even with task grouping disabled.
 d.editor();d.editor();keys=[k for k in d.windows if k.startswith('editor-')];assert len(keys)==2
 d.settings.setValue('running_group',False);d.set_pin(editor,'running');flush();eg=pin_group(editor);assert d.running_dock.groups()[eg]==keys
 assert d.running_dock.buttons[eg].property('windowCount')==2
 d.move_running(keys[0],2);d.switch_workspace(1);d.settings.setValue('running_current_only',True);d.running_dock.signature=None;d.queue_running_refresh();flush();assert eg in d.running_dock.buttons
 assert set(d.running_dock.groups()[eg])==set(keys)
 d.set_pin(editor,'running',False);flush();assert not d.running_dock.buttons.get(eg)
 d.switch_workspace(0);d.settings.setValue('running_current_only',False)
 # Pinning commands never executes them; closed pins can be dragged to another dock.
 command={'name':'Custom command','command':'example "one argument"'};assert d.set_pin(command,'running');flush();cg=pin_group(command);payload=d.running_drag(cg);assert payload['entry']['command']==command['command']
 assert d.transfer_launcher(payload,{'type':'clip','workspace':0},True);assert d.clip_entries()[0]['command']==command['command']
 # Dropping onto the bottom pins and keeps the source location intact, without launching.
 d.windows['calculator'].close();flush();before=len(d.side_launchers);assert d.transfer_launcher({'entry':calculator,'source':{'type':'catalog'}},{'type':'running'});flush();assert d.is_pinned(calculator,'running') and 'calculator' not in d.windows and len(d.side_launchers)==before
 # Menus on a title bar expose both destinations and all app launcher callbacks resolve.
 w=d.windows['files'];menu=QMenu();d.wm_actions(menu,'files');assert any(a.text()=='Pin to running-app dock' for a in menu.actions())
 assert d.entry_for_callback(d.calculator)['action']=='calculator';assert d.entry_for_callback(d.command_palette)['action']=='command_palette'
 # Saved pins round-trip through backups and survive a fresh Desktop instance.
 pins=d.bottom_pins();backup=root/'backup.zip';create_backup(d.store,d.settings,backup);_,prefs=validate_backup(backup);assert json.loads(prefs['running_pins_v14'])==pins
 schedule_restore(backup);restored=QSettings(str(root/'restored.ini'),QSettings.IniFormat);assert apply_pending_restore(restored);assert json.loads(restored.value('running_pins_v14'))==pins
 for k in keys:d.windows[k].content.editor.document().setModified(False)
 d.settings.sync();d.close();flush();d2=Desktop();d2.show();QTest.qWait(300);assert d2.bottom_pins()==pins;assert group in d2.running_dock.buttons and cg in d2.running_dock.buttons
 d2.set_pin(calculator,'running',False);flush();assert group not in d2.running_dock.buttons and 'calculator' not in d2.windows
 d2.close();flush()
 print('PASS closed/running pin lifecycle, no-close unpin, pin menus, duplicate prevention, per-window grouping, workspace scope, command preservation, drag-to-pin, backups, restart persistence, shutdown')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
