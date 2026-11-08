# 0.23 validation

All 15 desktop/integration test scripts pass after updating the tests for the intentionally changed menu/dock defaults. Focused final tests cover real header dragging, saved floating coordinates and no reserved left strip; one-column migration and optional wrapping; Installer Center preflight, simulated failure output/exit status and local logging; fullscreen handoff/restoration; root-helper authorization/live guards; and live-fstab restoration during simulated cross-device relocation. The affected desktop and live-menu integration checks were repeated after final process-lifecycle changes.

Calamares 3.3.14-1 and Debian settings 13.0.13-1 were inspected to verify the previous launch wrapper and GUI authorization behavior. Six added QML6 packages were checked against Debian trixie metadata. This does not establish that the user's exact failure is resolved: no real root installer GUI, disk installation, partitioning or installed boot was run here. Installer Center now preserves diagnostics needed to identify remaining failures.

# 0.23 validation

All 14 desktop/integration test scripts passed. After final menu/maximize changes, the affected workstation, app-menu, layout, decoration, session/desktop and dock checks were rerun and passed. New checks cover actual two-pane copying, digest fixtures and cancellation, bounded disk scans, symlink skipping, proc counter fixtures, bookmarks and path copy, recent history, activity bounds, focused-pane menu resolution, pinning and maximize/dock geometry. Qt offscreen renders were inspected. Package content, Python/shell syntax and ZIP integrity are checked during packaging.

Remaining machine tests: a rebuilt 0.23 ISO boot/install, real audio, native Flatpak download/launch, password unlock, suspend/resume and physical hardware support. No UNIX/POSIX certification or full conformance claim.

# Validation record

This kit has not produced an ISO in this environment. The runtime has no effective Linux capabilities, no mount capability (`CAP_SYS_ADMIN`), no live-build installation, and no `/dev/kvm`. Those limitations block the normal chroot image build and VM boot checks here.

Completed:

- Debian trixie live-build 20250505+deb13u1 accepted the complete `lb config` argument set and generated a Debian/trixie/amd64 configuration. For this check, extracted live-build files were relocated in a temporary directory; only the installed VERSION-file lookup was adjusted for relocation. No boot/root filesystem assembly was run.
- Package names checked against Debian trixie amd64 package metadata in the requested archive sections. Actual dependency installation is still a build-stage check.
- Installer transformations checked against the real Debian `calamares-settings-debian` 13.0.13-1 configuration. Debian's job sequence is retained, with one cleanup job inserted between users and displaymanager. Final install confirmation is enabled; branding, session selection and a required internet check are configured. The inherited Debian bootloader helper needs network package access.
- Cleanup tested using fake installation roots. It refuses `/` and escaping symlinks, removes only live autologin and the known temporary sudo rule, preserves unrelated account settings, and delegates temporary-account removal through the target environment.
- Desktop menu integration and full-screen launch smoke checked with Qt's offscreen backend. Existing left-menu regression suite passed.
- Shell/Python syntax, sample POSIX smoke checks, build preflight failure behavior and ZIP integrity checked.

Pending:

- Full `lb build`, root filesystem dependency installation, generated initramfs and bootloader assembly.
- Live BIOS/UEFI boot, display manager autologin, native-window layering and session startup.
- Actual Calamares UI, disk partition/copy, installed account cleanup, bootloader installation and boot without the ISO.
- Physical graphics/Wi-Fi/audio/Bluetooth/battery/suspend support and upgrade testing.
- UNIX/POSIX/SUS requirements mapping and conformance tests. No certification is claimed.

The checks above validate configuration and code behavior, not a working installable image. Use `VM-TEST-CHECKLIST.md` to advance the status once a local image build succeeds.
