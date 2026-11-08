"""Isolated smoke and behavioral checks; does not test OS conformance or audio output."""
import os,sys,tempfile,json,wave
from pathlib import Path
sandbox=tempfile.TemporaryDirectory(prefix='macaquestep-tests-')
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=sandbox.name+'/data';os.environ['XDG_CONFIG_HOME']=sandbox.name+'/config'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from session_tools import clean_layout,load_profiles
from command_center import Palette,validate_bindings,sequence
from unix_readiness import inventory,save_report
from backup_app import create_backup,validate_backup,schedule_restore,apply_pending_restore
app=QApplication([]);d=Desktop();d.resize(1450,930);d.show();QTest.qWait(350)
try:
 assert len(d.command_actions)==26
 assert d.command_labels['Esc']=='Return to windowed mode'
 assert all(not action.shortcut().isEmpty() for action in d.command_actions.values())
 # Saved layout restores geometry and independent window states, then undo restores the prior arrangement.
 d.settings.setValue('wm_workspace_names',json.dumps(['Main','Work','Play','Quiet']));d.refresh_workspace_names()
 d.calculator();calc=d.windows['calculator'];calc.setGeometry(230,100,400,420);d.toggle_sticky('calculator');d.toggle_above('calculator');d.set_shaded('calculator',True)
 d.notes();notes=d.windows['notes'];notes.setGeometry(40,140,600,400);d.move_running('notes',2);d.switch_workspace(0)
 d.minimize_running('about');QTest.qWait(30);saved=d.capture_layout();clean_layout(saved)
 d.settings.setValue('session_profiles',json.dumps({'Work':saved}));d.settings.sync();assert 'Work' in load_profiles(d.settings)
 d.set_shaded('calculator',False);calc.move(500,200);d.toggle_sticky('calculator');d.toggle_above('calculator');before=d.capture_layout()
 applied,skipped=d.apply_layout(saved);QTest.qWait(30);assert applied>=4 and not skipped
 assert calc.property('sticky') and calc.property('keep_above') and calc.property('shaded') and calc.height()==38
 assert calc.pos().x()==230 and notes.property('workspace')==2 and not notes.isVisible() and d.windows['about'].isMinimized()
 d.undo_layout();assert not calc.property('shaded') and not calc.property('sticky') and calc.x()==500
 # Invalid layouts fail before mutation; malformed saved profiles are ignored.
 invalid={**saved,'workspace':99}
 try:d.apply_layout(invalid);raise AssertionError('Invalid layout accepted')
 except ValueError:pass
 assert d.workspace==0
 d.settings.setValue('session_profiles',json.dumps({'Work':saved,'Broken':invalid}));assert list(load_profiles(d.settings))==['Work']
 # Missing tools may reopen, but terminal sessions never reopen.
 d.tasks();tasks=d.windows['tasks'];missing=d.capture_layout();tasks.close();d.windows['terminal'].close();QTest.qWait(40)
 applied,skipped=d.apply_layout(missing,open_missing=True);QTest.qWait(30);assert 'tasks' in d.windows and 'terminal' not in d.windows and skipped==1
 # Tile/cascade operate on visible workspace windows; undo restores exact geometry.
 d.switch_workspace(0);d.activate_running('calculator',False);calc.setGeometry(300,160,400,420);rect=QRect(calc.geometry());hidden_rect=QRect(notes.geometry());d.tile_workspace();assert notes.geometry()==hidden_rect;d.undo_layout();assert calc.geometry()==rect
 d.cascade_workspace();d.undo_layout();assert calc.geometry()==rect
 # Maximized/minimized layouts retain normal geometry; unmaximizing clears captured maximized state.
 d.maximize_running('calculator');d.minimize_running('calculator');QTest.qWait(20);maximum=d.capture_layout();row=next(row for row in maximum['windows'] if row['key']=='calculator');assert row['maximized'] and row['minimized'] and row['rect'][2:]==[rect.width(),rect.height()]
 d.activate_running('calculator',False);d.maximize_running('calculator');assert not next(row for row in d.capture_layout()['windows'] if row['key']=='calculator')['maximized']
 # Show Desktop retains preexisting minimization and restores the selected group.
 d.minimize_running('about');QTest.qWait(20);visible=[key for key,w in d.windows.items() if w.isVisible() and not w.isMinimized()]
 d.show_desktop();QTest.qWait(20);assert all(d.windows[key].isMinimized() for key in visible)
 d.show_desktop();QTest.qWait(20);assert all(not d.windows[key].isMinimized() for key in visible);assert d.windows['about'].isMinimized()
 # Shortcut validation is atomic; disabled actions and remapping survive settings save.
 original={k:a.shortcut().toString(QKeySequence.PortableText) for k,a in d.command_actions.items()};conflict=dict(original);conflict['Ctrl+Alt+P']=conflict['Ctrl+Alt+L']
 try:d.set_bindings(conflict);raise AssertionError('Conflicting shortcuts accepted')
 except ValueError:pass
 assert {k:a.shortcut().toString(QKeySequence.PortableText) for k,a in d.command_actions.items()}==original
 changed=dict(original);changed['Ctrl+Alt+P']='Ctrl+Alt+K';changed['Ctrl+Alt+H']='';d.set_bindings(changed);assert d.command_actions['Ctrl+Alt+H'].shortcut().isEmpty();assert json.loads(d.settings.value('keyboard_bindings'))==changed
 d.shortcuts_panel();panel=d.windows['shortcuts'].content;panel.defaults();panel.apply();assert d.command_actions['Ctrl+Alt+H'].shortcut()==sequence('Ctrl+Alt+H')
 # Filtering and executing a command uses the selected result and named workspaces.
 palette=Palette(d);QTest.keyClick(palette.search,Qt.Key_Down);assert palette.items.currentRow()==1;palette.search.setText('switch quiet');assert palette.items.count()==1;palette.run();assert d.workspace==3;d.switch_workspace(0)
 palette=Palette(d);palette.search.setText('window calculator');assert palette.items.count()==1;palette.run();assert d.area.activeSubWindow() is calc
 # Settings links remain intact; previous drawer link was accidentally overwritten by audio entry.
 d.sessions_panel();d.settings_hub();hub=d.windows['settings-hub'].content;assert any(title=='Launcher drawers' for title,_ in hub.entries);assert any(title=='Keyboard Shortcuts' for title,_ in hub.entries)
 d.readiness_panel();report=inventory();assert 'Inventory only' in report['status'] and report['utilities']['sh'];out=Path(sandbox.name)/'inventory.json';save_report(out,report);assert json.loads(out.read_text())==report
 # Preferences backup round-trip includes new settings.
 d.settings.setValue('session_profiles',json.dumps({'Work':saved}));d.settings.setValue('session_startup','Work');d.set_bindings(changed)
 backup=Path(sandbox.name)/'backup.zip';create_backup(d.store,d.settings,backup);_,prefs=validate_backup(backup);assert 'session_profiles' in prefs and 'keyboard_bindings' in prefs
 schedule_restore(backup)
 from PySide6.QtCore import QSettings
 restored=QSettings(str(Path(sandbox.name)/'restore.ini'),QSettings.IniFormat);assert apply_pending_restore(restored);assert restored.value('session_startup')=='Work';assert 'Work' in load_profiles(restored)
 # Existing UI behavior and assets stay available.
 assert any(label.text()=='Made by Drew' for label in d.windows['about'].content.findChildren(QLabel))
 assert len(list((Path(__file__).resolve().parents[1]/'assets/sounds').glob('*.wav')))==13
 d.switch_workspace(0);d.set_shaded('calculator',True);d.snap_window('calculator','Left');assert not calc.property('shaded')
 for tile in d.running_dock.buttons.values():assert tile.width()==tile.height()
 d.settings.setValue('session_startup','');d.settings.setValue('session_profiles','{}');d.settings.setValue('keyboard_bindings','{}');d.close();QTest.qWait(60)
 # Startup restores saved data-only layout, including a missing supported tool.
 settings=QSettings('MacaqueSTEP','DesktopPreview');settings.setValue('session_profiles',json.dumps({'Work':saved}));settings.setValue('session_startup','Work');settings.sync()
 d2=Desktop();d2.show();QTest.qWait(350);assert 'calculator' in d2.windows and d2.windows['calculator'].property('shaded');assert d2.workspace_names()[2]=='Play';d2.settings.setValue('session_startup','');d2.close();QTest.qWait(60)
 print('PASS sessions/undo/startup, state restoration, missing-tool restrictions, workspace-only arrangement, show desktop, shortcuts/conflict rejection, palette, settings links, host inventory/export, backup round-trip, docks/shading/credit/assets, clean shutdown')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
