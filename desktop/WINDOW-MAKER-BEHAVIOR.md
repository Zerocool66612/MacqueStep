# Window Maker behavior reference

The official Window Maker documentation is the reference for this project:

- Window behavior: https://www.windowmaker.org/docs/guidedtour/win.html
- Dock: https://www.windowmaker.org/docs/guidedtour/dock.html
- Clip: https://www.windowmaker.org/docs/guidedtour/clip.html
- Preferences: https://www.windowmaker.org/docs/guidedtour/prefs.html
- Workspaces and application hiding: https://www.windowmaker.org/docs/chap3.html

These guides document Window Maker, not a universal specification for an operating system. Some describe older releases. MacaqueSTEP uses them as a behavior reference while retaining its own appearance.

| Area | MacaqueSTEP 0.14 status |
| --- | --- |
| Persistent bottom pins, Pin/Unpin menus | Implemented; unpin preserves running windows |
| Shared pinned Dock and workspace Clip | Implemented for internal app launchers |
| Dragging, reordering and persisting launcher icons | Implemented; Ctrl-drop copies |
| Single/double-click dock launching | Configurable; single-click default |
| Shading by title-bar double-click or wheel | Implemented |
| Modifier double-click for height/width maximizing | Implemented |
| Click focus / focus follows mouse | Configurable |
| App-group hiding, hiding others, show all | Implemented separately from minimization |
| Per-app workspace/sticky/above/shaded rules | Implemented |
| Session layout saving | Implemented, with limited safe tool reopening |
| Distinct per-window miniwindow icons | Not implemented; current bottom dock groups running apps |
| Dock appicon stealing and Clip auto-attraction | Not implemented |
| Real Window Maker dockapps | Not supported in this preview |
| Managing arbitrary external application windows | Not implemented |
| Full Window Maker attributes and key/mouse bindings | Partial |
| Bootable OS, login session and installer | Not implemented; app installation packages now available |

MacaqueSTEP's right-click window menu offers Hide application and Hide others. Show all restores hidden groups without deminimizing windows that were already minimized. Selecting a particular running window can restore that window normally. Existing document contents are retained while hidden; saved session layouts contain window states rather than document bodies.
