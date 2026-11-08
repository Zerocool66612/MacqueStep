# MacaqueSTEP 0.23 — installer access and movable menus

**Made by Drew**

This release addresses the reported installer access problem and changes the dock/menu behavior requested after 0.21.

## Changes

- **One-column side dock by default.** The 0.23 first launch switches the old automatic-column setting off once, including existing accounts. Your selected icon size stays unchanged; the dock scrolls when icons exceed the available height. Preferences → “Allow extra dock columns (fit without scrolling)” remains an explicit optional choice and is respected on later launches.
- **Movable application menu.** With the horizontal bar off, drag the dark title at the top of File/Edit/View to move the whole menu anywhere within the desktop. It remembers the position, survives workspace/theme changes, and is clamped into view on smaller displays. It no longer reserves a fixed left dock strip. Right-click the panel for Center or Reset Position.
- **Visible Installer Center.** A direct “Install MacaqueSTEP…” entry appears in the live app menu, with desktop-menu and Preferences access too. It checks live media and required components, launches Calamares with authorization, shows output and exit status, and allows copying/saving diagnostics. It does not treat a canceled Calamares window as proof of a completed installation.
- **Native installer visibility.** Launching from the desktop temporarily leaves fullscreen so native installer windows can appear above it. Fullscreen returns when Installer Center closes. Ending the desktop session is blocked while Installer Center is open.
- **Installer launch reliability.** Adds the Qt 6 QML runtime components used by the installer and a software Qt Quick rendering path. A live-only root helper discovers the supported image locations, retains Calamares' actual return code and restores the temporary live-fstab workaround even on launch failures. Cross-filesystem moves between the live root and `/run` are handled. It does not choose a disk or bypass the final installer confirmation.

These repair likely launch/visibility failure paths and expose the original error; the exact installation failure reported by Drew was not reproduced here. Successful disk installation still needs a live VM/hardware test.

## Recommended: rebuild the ISO

From this newly extracted folder:

```bash
sudo bash build-iso.sh
```

Boot the new ISO, click **Install MacaqueSTEP… → Start graphical disk installer**, and proceed in Calamares. An internet connection is still required for the current Debian bootloader setup. If it fails, choose **Copy diagnostic text** in Installer Center and retain the output. The launch log is `~/.local/state/macaquestep/installer-launch.log`.

## Repair a currently running older live session

Download the accompanying package in the live session and run:

```bash
sudo apt install ./macaquestep-preview_0.23_all.deb
```

The package includes Installer Center, its live-only helper and authorization policy, and the QML dependency declarations. If you are still running the old fullscreen desktop, press **F11** to leave fullscreen, then run:

```bash
macaquestep-install
```

This lets you inspect or test the installer without rebuilding immediately. Dock/menu changes take effect after restarting the desktop session. Live-session package changes are temporary, and Calamares still copies the original older ISO filesystem: installing from that old image does not automatically put 0.23 onto the disk. Use the rebuilt ISO for a complete 0.23 installation, or apply the desktop update again after installing the older image.

## Validation

Local tests cover the one-column migration/optional wrapping; actual header dragging, position save/clamping/restart; real menu Save/Edit actions; Installer Center preflight and a simulated child failure with captured logs; fullscreen handoff; duplicate/live guards; and helper return-code/fstab restoration with a simulated cross-device move. Prior desktop, service, dock, welcome and workstation checks also pass. No real target disk or root Calamares GUI was exercised here.

# MacaqueSTEP 0.23 — workstation tools update

**Made by Drew**

## New in this release

- **Two-Pane Files:** independent folder browsing, explicit copy/move between panes, no overwrite of existing destinations, focused-pane File/Edit/Go menu routing, and transfer-aware close protection.
- **Folder bookmarks:** saved bookmarks, Ctrl+D, Ctrl+L, Alt+Left/Right, F5 and Copy Path. File action buttons wrap into two rows for smaller windows. Bookmarks participate in organizer preference backups; recent history does not.
- **Recent Documents:** up to 50 files opened through MacaqueSTEP, open/show enclosing folder, and a clear-history action that never deletes files. Paths are stored in your account's preferences; missing items are marked.
- **Disk Usage:** read-only folder totals and the 100 largest files, cancellation, inaccessible-item counts and a 100,000-entry bound. Symlinks/special files are skipped. Sizes are logical bytes, not allocated storage or deduplicated hard-link usage.
- **System Monitor:** CPU, memory, swap and network sampling from Linux /proc, with pause and links to audio/brightness/battery controls. It does not terminate processes or change system settings.
- **File Checksums:** local SHA-256/SHA-512 calculation, cancellation, expected-SHA-256 comparison and copy-digest. No uploads. Hashing rejects symlinks/special files and detects changes to the opened file while reading.
- **Activity Center:** the latest 200 built-in operation events for the current session, including transfers, Trash actions, scans and service results. Clearable and not persisted. This is not a system-wide notification daemon.
- **Window polish:** maximized windows leave room for the Clip header and bottom dock. All new tools can be launched from Tools/Applications, pinned to docks and included in desktop layouts. The Applications launcher also now includes the 0.20 service tools.
- **Reliability:** active file transfers block closing their containing file window; canceled scans return without publishing partial success. Native network/installer launch errors are detected correctly with Qt's detached-process return values.

The first-login music welcome, Setup Assistant, software installation tools, accessibility, theme icons, window decorations and existing docks remain included.

## Update the desktop without rebuilding

Close the older preview and install the accompanying desktop package on a supported Debian/Ubuntu system:

```bash
sudo apt install ./macaquestep-preview_0.23_all.deb
macaquestep-preview --left-menu
```

This updates the desktop application and retains notes, tasks, pins and preferences. It does not replace the kernel, bootloader or login-session configuration. Existing 0.20 native installations already have this release's required system integration; older systems may lack the optional Flatpak or locker services.

## Rebuild the ISO

Extract the full kit into a new directory and run `sudo bash build-iso.sh`. The result still requires a VM boot/install test; no new prebuilt ISO is provided. See the build requirements below and `VM-TEST-CHECKLIST.md`.

## Verification

The workstation tests exercise digest results, cancellation, bounded scans, symlink exclusion, /proc parsing, bookmarks, two-pane copies, recent-history deduplication, activity limits, focused-pane menus, dock pinning and maximize geometry. Prior desktop/service/welcome regression suites also passed. Physical audio, Flatpak downloads, lock/unlock, suspend/resume and a new ISO boot remain machine tests.

# MacaqueSTEP 0.23 — Classic 0.36 feature parity

**Made by Drew**

This brings the latest Classic feature set to MacaqueSTEP while preserving the Window Maker desktop, themes, decorations, docks, Clip, pins and menus.

- **Welcome with original music:** 15 seconds, no Skip/mute controls and no Escape, Enter, Space or window-close dismissal. It completes automatically. The system audio device/volume still determines whether sound is audible; the welcome does not force-unmute your speakers.
- **First installed login only:** never in the live ISO, never on later logins. The existing per-account/per-installation receipt is retained across upgrades. A new installation gets a new ID. Animation crashes do not block desktop startup.
- **Setup Assistant:** automatically follows a new first-login welcome and remains under Tools. Theme, window decorations, dock side, desktop sounds, network connection editor and system time-zone controls, plus links to the essentials. Each system change uses existing account/polkit permissions.
- **Software Center:** enable Flathub, search its applications, inspect installed apps and updates, install, launch, remove and update user Flatpaks. Downloads/changes require explicit UI actions. Native apps run as separate Openbox-managed windows.
- **Lock & Sleep:** X11 LightDM/light-locker integration. Suspend is requested only after both the locker and logind report the lock. Failure to confirm prevents suspend. Lid policy stays with logind. Real password unlock and resume need machine testing.
- **Personal Backup & Recovery:** visible home subfolders, up to 250 MB / 10,000 files; excludes symlinks and hidden files. Recovery creates a new folder and preserves existing files. Appearance/accessibility recovery uses a strict allowlist and saves prior settings before applying. Existing organizer/database backups remain separate.
- **Accessibility:** interface text size, high contrast/focus outlines and reduced motion. Reduced motion shows a still welcome card for the entire intro duration; it does not shorten the welcome. Native app accessibility is managed by those apps.

Open the new tools from **left menu → Tools**, the desktop's Applications menu, Preferences, or the command palette. They can be pinned to docks and saved in desktop layouts like other built-in tools.

## Build this update

Extract into its own new folder. From `MacaqueSTEP-0.23-OS-kit` run:

```bash
sudo bash build-iso.sh
```

For hosts with older Ubuntu live-build that rejects the image options, install the tested Debian build tool first:

```bash
wget -O live-build-debian.deb https://deb.debian.org/debian/pool/main/l/live-build/live-build_20250505+deb13u1_all.deb
sudo apt install ./live-build-debian.deb
```

This is a source/build kit, not a new prebuilt ISO. Drew confirmed the 0.18 live desktop boots. The 0.23 ISO and installation flow still require VM testing. First-login behavior must be checked after installing to a disposable VM disk, removing the ISO, then booting that disk.

## Components and validation

The feature scope was ported from Macaque Classic 0.36. Its original synthesized welcome composition is reused; no Apple music or footage is included. The session remains X11/Openbox; Wayland support was not introduced by this port.

Tests cover welcome guards and dismissal rejection, mock lock failure/no-suspend behavior, Flatpak argument validation, personal backup/recovery, preference filtering, setup/UI integration, and the previous desktop regression suites. These checks do not establish successful real downloads, password unlock, physical audio or suspend/resume.

# MacaqueSTEP 0.23 — experimental OS build kit

**Made by Drew**

This integrates the MacaqueSTEP 0.23 desktop with Debian GNU/Linux 13 (trixie), a Linux kernel, an X11 login session, networking/audio services, firmware packages and Calamares disk installation. The result of a successful build is a live/installer ISO. **This download is the source/build kit, not an ISO. No boot or disk-install test has been completed here.**

MacaqueSTEP remains a Unix-like Linux distribution project. UNIX certification and full POSIX/SUS conformance are not established. The display stack in this kit is X11/Openbox; Wayland integration is future work. The desktop still manages internal application windows rather than acting as the native system window manager. External applications use Openbox decorations.

## Build

Recommended: a dedicated **Debian 13 amd64 VM**, 4+ CPU cores, 8 GB RAM and 20–30 GB free space, with internet access. Building needs root and mount privileges. Ordinary restricted containers will fail preflight. Ubuntu hosts with compatible live-build may work, but are not validated; all Debian and parent mirrors are explicitly pinned to avoid the earlier Ubuntu/trixie mirror mismatch.

From the extracted `MacaqueSTEP-0.23-OS-kit` directory:

```bash
sudo apt update
sudo apt install live-build debootstrap debian-archive-keyring xorriso squashfs-tools \
  mtools dosfstools grub-pc-bin grub-efi-amd64-bin isolinux syslinux-common \
  python3 python3-yaml dpkg-dev
sudo bash build-iso.sh
```

Expected output:

```
output/build/live-image-amd64.hybrid.iso
output/build/live-image-amd64.hybrid.iso.sha256
output/build/build.log
```

The builder stops on failures, preserves the log and refuses a nonempty output directory. To retry without deleting diagnostic files, choose a new directory, for example `sudo bash build-iso.sh "$PWD/output/build-2"`. Do not edit the build host's `/etc/os-release` or mount host disk partitions into the build tree.

## What is configured

- A live account `macaque-live`, the default MacaqueSTEP session, plus Openbox as a recovery session. Debian live-config supplies the temporary live account; it is not the installed account. Treat the live session as passwordless and temporary.
- LightDM login, full-screen MacaqueSTEP, Openbox for external native windows, a policy authorization agent, NetworkManager, PipeWire, battery services, Bluetooth tools, Firefox and a rescue terminal.
- Calamares from Debian, using its maintained filesystem copy / user / bootloader / initramfs sequence. Branding says MacaqueSTEP. Final installation confirmation remains enabled. **This first kit requires an active internet connection during installation** because Debian's bootloader setup installs the firmware-appropriate GRUB package. The installer checks for connectivity. Offline installation is not implemented.
- **Left menu → Tools → Install MacaqueSTEP…**, also available in Preferences and the native application menu, only from live media.
- Cleanup of live autologin and the temporary account on the installation target before configuring the installed user's login. Usernames/passwords/partitioning are chosen in Calamares. No automatic disk selection or unattended erasure.
- BIOS and UEFI image configuration. Secure Boot is disabled for this experimental build; signed boot support has not been validated.
- Original Light/Dark/Classic themes, independent window decorations, Clip, docks, pins, menus, sounds and desktop features retained.

The release information is `/usr/share/macaquestep/release`. The Debian ID/version fields are retained for package compatibility. No new package repository is provided; system updates come from Debian, while desktop updates still require our packages/builds.

## First VM test

Install QEMU and firmware on the machine with a graphical display:

```bash
sudo apt install qemu-system-x86 qemu-utils ovmf
bash test-vm.sh output/build/live-image-amd64.hybrid.iso test-bios.qcow2 bios
# Separately test UEFI with a new disk:
bash test-vm.sh output/build/live-image-amd64.hybrid.iso test-uefi.qcow2 uefi
```

Each command creates a new sparse 40 GB virtual disk. The helper refuses existing files and `/dev/` paths. It uses hardware acceleration when accessible, otherwise software emulation. It does not expose host disks to the guest. Inside the VM, test the live desktop, launch the installer, select only the VM disk, install, shut down, remove the ISO and boot the installed disk. See `VM-TEST-CHECKLIST.md` for the full acceptance checks.

If the desktop fails, select **Openbox** at the login screen. Use the Openbox right-click menu to open xterm. Logs: `~/.local/state/macaquestep/session.log`, `~/.cache/calamares/session.log`, and the system journal.

## Validation status

Completed here: Python and shell syntax, package names against Debian trixie metadata, generated live-build configuration, Calamares configuration transformations, target-only cleanup unit checks, desktop integration smoke tests, and archive integrity. Full ISO assembly, BIOS/UEFI boot, actual graphical installation, hardware support and post-install boot are pending. See `VALIDATION.md` for recorded details.

## Sources and components

- Debian Live manual: https://live-team.pages.debian.net/live-manual/html/live-manual.en.html
- Debian live-build options: https://manpages.debian.org/trixie/live-build/lb_config.1.en.html
- Debian Calamares configuration: https://salsa.debian.org/live-team/calamares-settings-debian
- Calamares configuration: https://calamares.codeberg.page/docs/deploy-configuration/

Debian and third-party packages retain their licenses. Firmware availability does not guarantee every device works. Original desktop code/assets are included under `desktop/`; no new project-wide license is declared by this kit.
