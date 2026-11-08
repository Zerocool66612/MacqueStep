"""Verify theme routing, slider response, Window Maker behaviors, and install lifecycle."""
import os,sys,tempfile,json,subprocess
from pathlib import Path
from unittest.mock import patch
sandbox=tempfile.TemporaryDirectory(prefix='step-release-');base=Path(sandbox.name)
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_DATA_HOME']=str(base/'data');os.environ['XDG_CONFIG_HOME']=str(base/'config')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop import *
from PySide6.QtTest import QTest
from PySide6.QtGui import QMouseEvent,QWheelEvent
from PySide6.QtCore import QPointF,QPoint
from PySide6.QtSvg import QSvgRenderer
from foundation import ASSETS
from drawers import launch_entry
import install_user
app=QApplication([]);d=Desktop();d.show();QTest.qWait(300)
try:
 # Every app asset has an original valid Classic counterpart; modern icons are reused for both modern themes.
 assets=list(ASSETS.glob('*.svg'));assert len(assets)==26
 for asset in assets:assert QSvgRenderer(str(ASSETS/'classic'/asset.name)).isValid()
 d.apply_theme('Dark');dark=d.side_widgets[1].icon().cacheKey();d.apply_theme('Light');assert d.side_widgets[1].icon().cacheKey()==dark
 d.apply_theme('Classic');assert d.side_widgets[1].icon().cacheKey()!=dark;assert d.clip.anchor.icon().cacheKey()==icon('clip').cacheKey()
 d.apply_theme('Dark');assert d.side_widgets[1].icon().cacheKey()==dark
 # Real Preferences slider drives sizes up and down with no-scroll fitting enabled.
 d.preferences();slider=d.windows['preferences'].content.findChild(QSlider,'dockSizeSlider');assert slider
 d.settings.setValue('dock_fit',True)
 for size in (24,68,38,56):
  slider.setValue(size);QTest.qWait(40);assert d.effective_dock_size==size;assert all(b.width()==size for b in d.side_widgets);assert d.dock_scroll.verticalScrollBar().maximum()==0;assert all(b.width()==size for b in d.running_dock.buttons.values())
 d.drawer_shelf();assert all(b.width()==56 and b.iconSize().width()==42 for b in d.windows['drawer-shelf'].content.buttons)
 # Hide application operates on the group, without minimizing or destroying documents.
 a=d.editor();b=d.editor();keys=[k for k,w in d.windows.items() if k.startswith('editor-')];assert len(keys)==2
 d.hide_application(keys[0]);assert all(d.windows[k].property('app_hidden') and not d.windows[k].isVisible() and not d.windows[k].isMinimized() for k in keys)
 d.switch_workspace(1);d.switch_workspace(0);assert all(not d.windows[k].isVisible() for k in keys)
 launch_entry(d,{'name':'Editor','action':'editor'});assert len([k for k in d.windows if k.startswith('editor-')])==2;assert all(not d.windows[k].property('app_hidden') for k in keys)
 d.hide_others(keys[0]);assert d.windows['files'].property('app_hidden');assert d.windows[keys[0]].isVisible();d.show_all_applications();assert not d.windows['files'].property('app_hidden')
 # Modifier double-click supports axes and restores exact original geometry.
 key=keys[0];w=d.windows[key];w.setGeometry(180,90,400,300);original=QRect(w.geometry())
 def double(mod):
  event=QMouseEvent(QEvent.MouseButtonDblClick,QPointF(15,10),QPointF(15,10),Qt.LeftButton,Qt.LeftButton,mod);d.titlebar_double_click(key,event)
 double(Qt.ControlModifier);assert w.y()==0 and w.height()==d.work_rect().height() and w.width()==400;double(Qt.ShiftModifier);assert w.geometry()==original
 double(Qt.ShiftModifier);assert w.x()==0 and w.width()==d.work_rect().width() and w.height()==300;double(Qt.ControlModifier);assert w.geometry()==original
 # Wheel shading is scoped to title bars.
 wheel=QWheelEvent(QPointF(15,10),QPointF(15,10),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False);QApplication.sendEvent(w.titlebar,wheel);assert w.property('shaded');d.set_shaded(key,False)
 # Optional double-click launch suppresses the first release and runs once on double click.
 d.settings.setValue('dock_double_click',True);index=next(i for i,e in enumerate(d.side_launchers) if e['action']=='calculator');button=d.side_widgets[index]
 QTest.mouseClick(button,Qt.LeftButton);assert 'calculator' not in d.windows
 QTest.mouseDClick(button,Qt.LeftButton);assert 'calculator' in d.windows;d.settings.setValue('dock_double_click',False)
 # Group hiding is captured in session layouts, then restored.
 d.hide_application(key);saved=d.capture_layout();assert next(row for row in saved['windows'] if row['key']==key)['hidden'];d.show_all_applications();d.apply_layout(saved);assert d.windows[key].property('app_hidden');d.show_all_applications();d.close();QTest.qWait(50)
 # Install and upgrade activate independent releases; uninstall preserves unrelated data.
 prefix=base/'installed';wrapper=base/'bin/macaquestep-preview';entry=base/'menus/macaquestep-preview.desktop'
 def paths(_):return prefix,wrapper,entry
 with patch.object(install_user,'paths',paths):
  install_user.install(prefix,system_python=True);first=(prefix/'current').resolve();assert wrapper.is_file() and entry.is_file();recovery=wrapper.with_name('macaquestep-classic-menus');recovery_entry=entry.with_name('macaquestep-classic-menus.desktop');assert recovery.is_file() and recovery_entry.is_file()
  env=dict(os.environ);env['XDG_DATA_HOME']=str(base/'installed-test-data');env['XDG_CONFIG_HOME']=str(base/'installed-test-config')
  subprocess.run([str(wrapper),'--smoke-test'],check=True,timeout=20,env=env);subprocess.run([str(recovery),'--smoke-test'],check=True,timeout=20,env=env)
  install_user.install(prefix,system_python=True);second=(prefix/'current').resolve();assert first!=second and first.exists();unrelated=prefix/'keep-me.txt';unrelated.write_text('unrelated')
  install_user.uninstall(prefix);assert not wrapper.exists() and not entry.exists() and not recovery.exists() and not recovery_entry.exists();assert unrelated.read_text()=='unrelated';assert not first.exists() and not second.exists()
 print('PASS Classic assets/theme switching, actual slider growth/shrinkage, no scrolling, app-group hide/show and session state, modifier maximizing, wheel shading, double-click launch, user install/upgrade/launch/uninstall')
finally:
 for widget in list(app.topLevelWidgets()):
  if isinstance(widget,Desktop) and not widget.exiting:widget.close()
 app.processEvents()
