# New in 0.23

Single-column default side dock; floating File/Edit/View menu (drag its title); visible Installer Center with logs and native-window fullscreen handoff. See the build-kit README for repair/rebuild instructions and validation limitations.

# MacaqueSTEP 0.23

Adds Two-Pane Files, saved folder bookmarks/navigation shortcuts, Recent Documents, Disk Usage, System Monitor, File Checksums and Activity Center. Tools are in Tools/Applications and can be pinned to docks. See the OS kit README for operation limits and validation.

# New in 0.23

See the build kit README for the Classic 0.36 feature port: original music welcome without dismissal controls, Setup Assistant, Software Center, Lock & Sleep, Personal Backup & Recovery and Accessibility. New tools are in Tools and Preferences. The welcome only runs from an installed login session and completes in 15 seconds.

# MacaqueSTEP 0.17 — Made by Drew

New in this release:
- Independent live-switchable Modern, Traffic lights, Classic Mac, and Window Maker window decorations. Preferences → Window decorations.
- Title-bar height control and optional maximize button; tooltips and accessible control names.
- Title-bar context menu → Center window and Compact / Comfortable / Large sizes. Existing shade, snap, sticky, keep-above, workspaces, hide and running-app controls remain available.
- Graphical **per-user desktop-preview installer**: `sh install-graphical.sh`. Requires PySide6 in the launching interpreter; `run.sh` prepares the preview environment first if needed. The wizard runs the existing managed installer, shows live output, preserves settings and notes, and only reports success after its process exits successfully. It does not partition disks.
- Experimental Debian live-build recipe in `iso/`. **No bootable ISO is delivered or boot-tested.** See `iso/README.md` for requirements and limitations.
- `--fullscreen` launch option for experimental hosted sessions.

The decoration styles affect MacaqueSTEP's internal app windows. External native programs retain their host window manager's decorations.

## Installation

Ubuntu/Debian with compatible PySide6 packages:

```sh
sudo apt install ./macaquestep-preview_0.17_all.deb
macaquestep-preview --left-menu
```

Source preview: `bash run.sh`. Graphical account installer: `sh install-graphical.sh`. Close an older running preview before launching this release.

# MacaqueSTEP 0.16 — persistent left application menu

**Made by Drew.** Keeps the current desktop appearance, matching square docks, workspaces, and existing tools.

## Launch

Close your older preview, extract the ZIP, open a terminal inside `MacaqueSTEP-0.16`, and run:

```sh
bash run.sh
```

First launch downloads PySide6 and pyte into a private `.venv` inside this folder. If necessary on Ubuntu:

```sh
sudo apt install python3-venv libegl1 libopengl0 libxcb-cursor0
```

Run as your normal user. Notes/tasks and desktop preferences carry over. Optional user-menu launcher: run `python3 install_launcher.py` after first launch; remove it with `python3 install_launcher.py --remove`. Keep the folder in place while using the launcher.

## New in 0.16: persistent left app menu

When the horizontal top bar is off, a **persistent vertical application menu** appears on the left, following the supplied GNUstep/GWorkspace-style reference. It stays on screen between workspace changes and follows the active built-in application. Its header names the active app; with no active window it shows MacaqueSTEP.

Rows include **Info, File, Edit, View, Go, Tools, Windows, Services, and Help**, plus direct **Hide, Hide Others, Show All, Print…, and Quit Preview** actions. Submenus open to the right. File/Edit/View/Go/Window/Help reuse the top bar's real command adapters, so Open/Save, clipboard editing, printing, pinning, and other supported app actions work the same way. Unsupported commands remain disabled. Tools lists the desktop applications; Services offers search, screenshots, sound, system controls, backups, and Preferences. Quit Preview uses the normal unsaved-document checks and does not log out the host.

**Preferences → Menu bar layout → Left app menu (no top bar)** selects this layout. Turning off **Show horizontal top bar** has the same result. **Show left app menu when top bar is off** is enabled by default; it can be disabled separately. Choosing Classic app menu bar or Desktop toolbar removes the left panel and restores the horizontal bar. Existing saved layout choices are honored.

To start directly in this layout after closing an older preview:

```sh
/usr/bin/macaquestep-preview --left-menu
```

From an extracted source folder use `bash run-left-menu.sh`. The desktop right-click menu also offers **Use left app menu**. Ctrl+Alt+B toggles the horizontal bar and left-menu layout using the last visible bar style. Ctrl+Alt+M explicitly restores horizontal Classic menus.

The panel reserves its own workspace area so internal windows, the Clip, and running-app tiles do not cover it. Switching layouts, changing workspaces, or resizing repositions the panel and keeps it available. Classic, Light, and Dark styling, existing dock side/fitting choices, and all pins are retained. The layout and enabled setting save automatically and are included in backups.

## Retained menu recovery commands

File, Edit, View, Go, Window and Help are now explicit embedded menu buttons rather than a QMenuBar. They retain the same app commands and cannot be exported as a native global menu bar. The missing-bar report could not be reproduced in offscreen tests; this release removes that integration dependency and adds direct recovery paths.

The 0.16 release honors saved layout choices. The explicit Classic Menus launcher still restores the horizontal menus when requested.

Close the existing preview, install this release, then run:

```sh
/usr/bin/macaquestep-classic-menus
```

The system package adds a separate **MacaqueSTEP 0.15.1 — Classic Menus** menu entry. It passes `--classic-menus` to the installed application, overriding saved Hidden or Toolbar choices. Per-user installation provides the same launcher under `~/.local/bin`. From an extracted source folder, use `bash run-classic-menus.sh`.

While this version is running, **Ctrl+Alt+M**, the desktop right-click command **Show File / Edit Menus**, and the Preferences button **Show File / Edit Menus Now** all restore the menus directly. Ctrl+Alt+B retains its normal hide/restore toggle.

`macaquestep-preview --version` prints the build version. `macaquestep-preview --diagnose` reports the code path, Python interpreter, saved bar state, and menu implementation without starting the desktop. If another preview is already open, the new launcher explains that it must be closed; it never kills an existing process or discards unsaved documents.

## Retained from 0.15: classic application menu bar

The default bar now contains **MacaqueSTEP, File, Edit, View, Go, Window, and Help**, plus the active built-in app name and a clock. Menus update when opened and follow the active internal window. The menu bar uses the selected Classic, Light, or Dark appearance.

- **File:** New text document/note/task/drawing, New Folder in File Viewer, context-specific Open, Save, Save As or Export Note, Close Window, Page Setup, and Print where supported. The editor retains its existing unsaved-change checks and atomic saving.
- **Edit:** Undo/Redo, Cut/Copy/Paste, Delete Selection, Select All, Find, and Find Next where supported. It retains the last focused editing field when the menu takes focus. File Viewer's main view uses file URL clipboard operations; its address/filter fields use text editing. Notes can be saved, exported or deleted through their existing actions. Paint offers Undo, Color, and Clear. Terminal supports selection copying and explicit paste into the PTY, with destructive text-edit commands disabled.
- **View:** menu-bar layout, full screen, workspace overview, Show Desktop, hidden-file visibility in File Viewer, and media playback controls when active.
- **Go:** folder history, enclosing folder, common folders, and workspaces.
- **Window:** minimize, zoom, shade, pin/unpin, hide/show apps, tile/cascade, layout undo, and the open-window list.
- **MacaqueSTEP / Help:** About, Preferences, tools, sessions, sounds, Help, and project status.

Unavailable commands are disabled. Menus control MacaqueSTEP's built-in apps; they do not take over external applications' menu bars. Document contents are never silently discarded by menu commands. New task opens the task-entry field. New Paint drawing uses the existing Clear Drawing command, including its discard confirmation and undo behavior.

Text/document views, Notes, and Paint support Page Setup and printing through Qt's standard dialogs. Print waits for confirmation. Text and drawing output were tested to PDF; physical printer output still requires a check on your machine. The Debian package now includes a dependency on the Qt PrintSupport Python module.

In **Preferences → Menu bar layout**, choose **Classic app menu bar**, **Desktop toolbar**, or **Hidden**. The same choices are in View and the desktop right-click menu. Ctrl+Alt+B hides the bar and restores the last visible layout. On the first 0.15 launch, Classic app menus are selected; later choices persist and are backed up. The old toolbar, Clip, docks, pinning, icon sets, and extra-column fitting remain available.

## Retained from 0.14.1: traditional layout

In Preferences, turn off **Show top bar (off for traditional Window Maker layout)**. The desktop area expands while the Clip and docks remain available. The option saves automatically and is included in backups. Choose Hidden in the layout selector, or turn off the visibility checkbox. The shortcut restores the last visible layout.

Right-click an empty area of the desktop for Applications, Terminal, Preferences, Commands, Workspaces, Windows, and Drawers. Check **Show top bar** in that menu to restore it, or use **Ctrl+Alt+B** to toggle it at any time. The shortcut can be changed in Keyboard Shortcuts. Ctrl+Space (Applications), Ctrl+Alt+P (Commands), and the Clip workspace arrows also keep working without the bar. Preferences stays synchronized when you toggle the bar elsewhere.

This option controls MacaqueSTEP's own top bar. Host desktop panels and the outer application title bar are separate. F11 continues to toggle full screen.

## Retained from 0.14: Pin and Unpin

Right-click an app in **Applications**, a side-dock launcher, a Clip launcher, a Drawer Shelf icon, a running-app tile, or an internal window title bar. Choose **Pin to side dock** or **Pin to running-app dock**. Already pinned apps offer **Unpin from…** instead. The two destinations are independent, so an app can be pinned in both places. Pinning copies a reusable launcher and does not remove its source launcher or launch an app.

The bottom dock now combines **persistent pins and running apps**. Pins remain visible after their last window closes, with a small gold marker and a tooltip showing whether the app is running. Click a closed app's pin to launch it; while running, the pin represents its existing windows. Multiple windows have a count badge and a window chooser. Even when per-window task grouping is selected, a pinned app uses one tile for its matching windows.

**Unpin never closes an application.** An unpinned app that is still running retains an ordinary running tile, subject to the selected workspace filter. A closed app's unpinned tile disappears. Pins themselves stay visible across workspace changes, including current-workspace-only task mode, so clicking a pin can activate a window on another workspace.

**Dropping a launcher onto the bottom dock now pins it without launching it.** Its source remains in place. Dragging from the bottom dock can still copy/pin a launcher into the side dock, Clip, or drawer. Repeated Pin actions do not create duplicates in that destination. Explicit custom-command launchers can also be pinned; MacaqueSTEP cannot track their external host windows and treats them as launchers.

Pins save automatically and are included in preference backups. The existing multiple-column fitting behavior, Classic/Light/Dark icons, and tile-size slider remain unchanged.

## Retained from 0.13

**Separate Classic icon theme:** Classic uses 26 original workstation-style pixel icons with beveled square tiles. Light and Dark retain the existing modern assets. Switching Appearance updates the side dock, running dock, Clip, drawer shelf, and About logo without restarting. These are original MacaqueSTEP assets, not a copy of Window Maker's distributed artwork.

**Dock slider fixed:** Dock tile size now ranges from 24 to 68 pixels and changes the actual side-dock size. With fitting enabled, additional columns preserve the selected size instead of silently capping it. The matching running dock, Clip launchers, and drawer shelf update too. Very large Clip collections may still reduce their own size to fit their available area. Turn fitting off for one column with scrolling. Modern dock button padding was reduced so small icons have usable drawing space.

**Closer Window Maker behavior:** title-bar and running-tile menus now offer Hide application, Hide other applications, Show application, Show application here, and Show all applications. Hiding retains the app's windows and unsaved content; it is distinct from minimizing. Launching a hidden app through a pinned icon restores its existing windows. Title-bar wheel-up shades and wheel-down unshades. Ctrl-double-click maximizes height, Shift-double-click maximizes width, and Ctrl+Shift-double-click expands both axes; another modified double-click restores the prior geometry. Preferences offers optional double-click launching for dock icons. Single-click remains the default. These behaviors apply to internal windows. See WINDOW-MAKER-BEHAVIOR.md for the official guide and remaining differences.

## Install on an existing Linux desktop

Close any older preview first. Choose one installation method.

### Debian package

On Debian/Ubuntu with PySide6 packages version 6.8 or newer available (including Debian 13), install the supplied package from its download directory:

```sh
sudo apt install ./macaquestep-preview_0.16_all.deb
```

Open **MacaqueSTEP Preview** in your applications menu, or run `macaquestep-preview`. APT installs the distro runtime dependencies. Upgrade by installing a newer package. Remove the app with `sudo apt remove macaquestep-preview`; Notes, Tasks, and user preferences stay in your account. The package does not run pip or change your login session.

### Per-user installation

Extract this source ZIP, enter its folder, then run:

```sh
bash install.sh
```

Run as your normal user. Python venv support and internet access are needed on first install. The installer copies the app into a managed user directory and installs its private Python dependencies. It creates a menu entry and `~/.local/bin/macaquestep-preview`. The downloaded source folder can then be removed. On an upgrade, preparation completes before switching the active release; earlier installed release folders are retained until uninstall. If the current Python already has supported dependencies, `bash install.sh --use-system-python` reuses it instead.

To uninstall this per-user installation, use the source folder's `bash install.sh --uninstall`, or run `python3 ~/.local/share/macaquestep-preview/current/install_user.py --uninstall` (adjust for a custom XDG_DATA_HOME). It removes only managed app releases and launchers, and keeps organizer data and preferences. Uninstall the user version before switching to the Debian package so a user menu entry does not shadow the system entry.

Both methods install the **desktop preview application on your existing OS**. Bootable media, an OS installer, external window management, and a real login-session/compositor integration remain future work. The Debian package was built, inspected, extracted, and launched with the available runtime; APT dependency installation on the target computer still needs verification. User install, upgrade, launch, and uninstall were tested in isolated directories.

## Retained from 0.12: Clip and movable launcher icons

The **paperclip at the top left** is the workspace Clip. Each of the four workspaces has its own saved launchers. Use the arrows to switch workspaces, click the paperclip to collapse/expand its icons, or right-click it to add a built-in launcher and rename the workspace. The Clip starts empty so it does not rearrange your existing launchers.

**Drag launcher icons between the side dock, Clip, and Drawer Shelf.** A normal drag moves a pinned launcher; hold Ctrl while dropping to copy it. Drop onto an existing icon to insert before it; drop into the dock's empty space to append. Icons can be reordered within each dock. These are MacaqueSTEP's own launcher icons, not arbitrary icons from your host desktop. File/URL drops from other applications are not accepted.

**Drawer Shelf** presents the existing launcher drawers as draggable icon tiles. Open it from the side dock, Applications, Commands, Settings, or Preferences. Choose the target drawer in its selector before dropping. The top-bar Drawers menu remains available for quick launching; use the graphical Shelf for dragging. Customize drawers still manages drawer names and explicit host commands. Commands moved between docks keep their arguments and are not executed by the move.

The **bottom dock shows running internal applications and persistent pins**. Drag a running tile to another dock to pin a reusable launcher; the running tile remains while its windows are open. Drop a launcher onto the bottom dock to pin it; click its tile to launch or activate that app. This does not move a pinned launcher out of its source or transfer its live window to another workspace. A pinned document-app launcher opens the app's normal start/open interface rather than remembering an unsaved document. External app windows remain host-managed.

**No-scroll side dock:** Preferences → Fit side-dock icons without scrolling (enabled by default). It uses extra columns when one column cannot fit, preserving the selected 24–68 pixel tile size. Resizing updates the layout. Running tiles follow the effective size when matching is enabled. Turn fitting off to retain the preferred icon size and scroll normally. Dock position still supports Right and Left. Clip visibility is also configurable in Preferences.

Right-click a side icon to remove it or move it to the active Clip. Right-click a Clip icon to remove it, copy it to the side, or move it to another workspace Clip. Preferences offers Restore default side-dock launchers if you want the original set back. Moving or removing a launcher never closes its application. The side launcher order, Clip contents/collapse state, and fitting/visibility settings persist and are included in backups. Limit: 100 launchers per dock/Clip/drawer.

## Retained from 0.11

**Command Palette:** click Commands in the top bar or press Ctrl+Alt+P. Search applications, open windows across all workspaces, workspace names, and layout actions. Press Enter to run the selected result.

**Desktop Sessions:** open it through Applications, Settings, Drawers customization, or Ctrl+Alt+L. Save up to 20 named layouts containing window positions, workspace names, and minimized/maximized/shaded/sticky/keep-above states. Load a saved layout without closing other windows. Optional opening of missing tools supports Files, Notes, Tasks, Calculator, Clock, Help, Search, Settings, Sounds, and About. Documents, media, terminal processes, and external commands are never reopened by a layout. Existing document windows can be arranged, but their contents are not saved in a session. Choose a saved layout in On startup to restore it on subsequent launches; Default startup turns this off. Notes/Tasks retain their normal independent storage.

**Layout undo and Show Desktop:** tiling and cascading now arrange only visible, non-minimized windows on the current workspace, including sticky windows. Ctrl+Alt+Z undoes the last tile, cascade, or session load. It restores positions and states of available windows; it does not close newly opened tools. Ctrl+Alt+H minimizes the currently visible windows and restores that group on the next press, preserving windows that were already minimized.

**Keyboard Shortcuts:** change desktop-level shortcuts through Settings or Applications. Clear disables an action. Apply saves the full configuration; conflicting key combinations are rejected. Restore defaults fills the editor, then Apply saves. Application-local and host desktop shortcuts are separate; the host may reserve a combination. Help lists defaults; the Shortcuts panel shows current values.

**Unix Readiness Inventory:** read-only host details, reported sysconf values, and presence of a sample of command-line utilities, with JSON export. These are preliminary observations, not behavioral conformance tests, a complete requirements audit, or certification. The proposed full-OS engineering target is POSIX.1-2024 / Single UNIX Specification Version 5. Full standards conformance remains unverified. See UNIX-ROADMAP.md.

Sessions, startup selection, and desktop shortcut settings are included in preference backups. Existing themes, docks, retro sounds, Window Maker-style controls, and Made by Drew attribution remain.

## Window and workspace controls

- **Window shading:** double-click a title bar to roll a window into its title bar; repeat to restore its size. Preferences can change double-click to Maximize. Snapping and maximizing unshade automatically.
- **Sticky windows:** right-click a title bar or running-dock tile and select Show on all workspaces. Switching workspaces keeps that window visible. Moving it to a specific workspace clears this option.
- **Keep above:** keep selected windows above ordinary internal windows.
- **Focus follows mouse:** optional pointer focus, with a separate raise-on-focus switch in Preferences.
- **Named workspaces:** right-click one of the four workspace buttons to rename it. Menus and Overview use the saved names.
- **Per-app rules:** open Window Rules to save an app's starting workspace, sticky, keep-above, and shaded state. Save and apply updates its open windows as well.
- **Launcher drawers:** the Drawers menu and matching side-dock tile contain customizable groups. Add, rename, or remove drawers; add built-in tools or explicitly configured host commands; reorder entries. Host commands use argument parsing without a shell.

These settings persist and are included in preference backups. The rules and window actions control MacaqueSTEP's internal windows. Host commands open external programs under your account; those windows remain managed by your host desktop.

**Shortcuts:** Ctrl+Alt+S shades the active window; Ctrl+Alt+D opens drawer customization; Ctrl+Alt+PageUp/PageDown cycles workspaces. Right-click a window title bar for the complete window menu.

## Retro desktop sounds

Twelve original synthesized effects are included: startup chime, open, close, minimize, restore, menu, click, workspace switch, alert, error, Trash, and completion. They are new workstation-inspired tones, not recordings copied from another operating system.

Open **Sound Effects** through Applications, Settings Hub, Preferences, or About MacaqueSTEP. Controls include enable/mute, effects volume, startup/window/menu/alert categories, a sound list, Preview, and Stop. Effects default to 30% application volume. These controls do not change the host's master volume.

Opening the initial windows does not produce an opening-sound burst. Window close sounds play only when a window actually closes. Canceled unsaved-document closes stay silent. Shutdown suppresses close-sound storms. Effects are short and repeated UI events are throttled.

Sound playback requires a functioning host audio device and Qt Multimedia backend. Sound Effects reports unavailable output/backend failures. The included WAV files can also be played directly from `assets/sounds`. Recreate them with `python3 make_sounds.py`.

## About and settings

About MacaqueSTEP is now an About This Mac-style overview with four tabs:

- **Overview:** MacaqueSTEP version, Made by Drew credit, reported processor, thread count, memory, architecture, host OS, and computer name.
- **Displays:** display name, reported resolution, logical size, scale, and refresh rate.
- **Storage:** mounted-volume capacity, available space, access mode, and an Open Location action.
- **Support:** Help, System Report, Backups, and Project Status.

Settings, System Report, and Sound Effects buttons are available at the bottom. Hardware details are read from the computer running the preview.

The new **Settings Hub** organizes the available appearance, dock/window, sound, display-information, storage, network/Bluetooth/battery, backup, installed-app, and reporting tools. This supplies common categories and links; it does not implement every macOS preference. Display information is read-only. Host volume, brightness, network, and Bluetooth controls remain dependent on detected tools and permissions.

## Retained functionality

Individual square pinned/running docks; grouping, minimize/restore, workspace activation; four workspaces; snapping and overview; interactive PTY terminal; file search; installed-host-app discovery; multi-file/folder copy and same-filesystem move; cancellation; rename and Trash; editor; persistent Notes/Tasks; backup/restore; Paint; archive browsing; image/media players; calculator; clock/timer; system controls/report; screenshots; and Help.

F11 full screen; Escape windowed (passed to Terminal while focused). Ctrl+Space Applications. Ctrl+Alt+1–4 workspace. Ctrl+Alt+O Overview. Ctrl+Alt+T Terminal. Ctrl+Alt+W windows. Ctrl+Alt+F search. Ctrl+Alt+Shift+arrow snaps a window. Text Editor uses Ctrl+S/O/F. Terminal uses Ctrl+Shift+C/V clipboard, Shift+PageUp/Down scrollback, and normal Ctrl+C interrupt.

## Data and operating-system status

Notes/tasks use `$XDG_DATA_HOME/MacaqueSTEP/preview/organizer.sqlite3`, normally `~/.local/share/MacaqueSTEP/preview/organizer.sqlite3`. Qt stores desktop preferences, including sound settings. Backups include Notes/Tasks and saved desktop preferences. Restore occurs on the next launch and retains a recovery database. Close earlier preview versions before restoring.

This is still a desktop preview on the host OS. The docks manage internal MacaqueSTEP windows. External-window session/compositor integration, a validated FreeBSD port, bootable installer, signed updates, and target-hardware testing remain unfinished; Project Status tracks them.

Commands and file operations affect your actual host account. Copies refuse overwrites; moves are restricted to one filesystem. Advanced terminal applications may differ from a full terminal emulator, and detached processes can survive shell closure. Paint has a 16-megapixel limit/eight undo states. Archive Viewer limits archives to 256 MB/10,000 entries, previews to 1 MB, and selected-file extraction to 16 MB. Media depends on host codecs/devices.

## Validation

`python3 tests/verify_side_menu.py` checks automatic display when the top bar is off, persistent geometry, active-app labels, a real File → Save popup, editing/undo, hide/show actions, workspace and theme changes, layout restoration, preferences, backups, and restart persistence.

`python3 tests/verify_menu_recovery.py` checks explicit menu-button visibility in Classic/Light/Dark at 850- and 1450-pixel widths, actual popup opening, keyboard/Preferences/desktop recovery, forced command-line recovery, version diagnostics, and retention of unrelated dock preferences.

`python3 tests/verify_app_menu.py` exercises actual editor Open/Save and undo/clipboard operations, focused-field routing, Notes and File Viewer commands, Terminal paste, Paint save/undo, text/drawing PDF printing, canceled closes, stale actions, disabled commands, all three layouts, backups and restart persistence.

`python3 tests/verify_layout.py` checks top-bar visibility, expanded desktop space, menu and shortcut recovery, saved preferences, restart persistence, backup restoration, and retained docks.

Run `python3 tests/verify_desktop.py` using an interpreter with the requirements installed (or `.venv/bin/python tests/verify_desktop.py` after first launch). It isolates test preferences and organizer data in temporary directories. Checks cover saved state and startup restoration, malformed-layout rejection, missing-tool restrictions, layout undo, workspace-only tiling/cascading, Show Desktop, shortcut conflicts/remapping, command search and execution, settings links, inventory export, backup round-trip, square dock tiles, shading/snapping, creator credit, and retained sound assets. Also run `python3 tests/verify_docks.py` for Clip isolation, fitting at small window sizes and 100 launchers, manual scrolling, Qt drop and drag initiation, move/copy/reorder, drawer transfers, running-app pinning, malformed-payload rejection, persistence and backup coverage. Also run `python3 tests/verify_pins.py` for pin/unpin menus, closed/running lifecycle, duplicate prevention, grouped windows, workspace scope, drag-to-pin, command launchers, backups, and restart persistence. Run `python3 tests/verify_release.py` for Classic asset/theme switching, real slider resizing, application hiding, modifier maximizing, wheel shading, double-click launching, and the user installation lifecycle. All eight suites passed with offscreen Qt. Real pointer drag/drop still needs confirmation on your desktop/compositor. The updated interface was rendered and inspected. Audible playback and real hardware/session integration still require testing on your computer.

## Source and assets

New in 0.15: `app_menu.py` and `tests/verify_app_menu.py`, plus explicit editor menu adapters and the layout selector.

New in 0.14: `pinning.py` and `tests/verify_pins.py`, with persistent-pin support in `running_dock.py`.

Retained from 0.13: `wmaker_behavior.py`, `assets/classic`, `install_user.py`, `install.sh`, and `build_deb.py`. All twelve original PCM WAV effects are included under `assets/sounds`. Existing apps retain their modules. Python 3.10+, PySide6, pyte, and a Unix PTY-capable host are required.
