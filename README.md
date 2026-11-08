# MacaqueSTEP 0.23

Made by Drew. A NeXT / Window Maker inspired Linux desktop, based on Debian 13.

This experimental build kit produces a live ISO with a graphical Calamares disk installer.

## Changes

- Direct Applications and Wi-Fi & Network buttons in the movable desktop menu.
- Network connection chooser opens without typing commands; saved connection editor, adapter status, and copyable diagnostics.
- Unified searchable launcher for built-in tools, native desktop applications, and exported Flatpak entries; refresh button.
- Firefox ESR, GIMP, Audacity, VLC, Evince, and Engrampa in the ISO package list.
- Required Calamares slideshow branding and validation both before building and inside the image configuration hook.
- Single-column right dock default, floating menu, existing themes, and first-installed-login welcome retained.

## Build

See BUILD-GUIDE.md for dependencies and host requirements. On your normal Debian-capable build machine, from this folder:

```bash
sudo bash build-iso.sh
```

Flash output/build/live-image-amd64.hybrid.iso using your image writer. Internet is currently required by the installer.

## Validation and limits

Focused UI tests cover native app listing/launch, refresh, network access, missing-utility behavior, and fullscreen handoff. Installer tests cover branding resources, target cleanup, launcher diagnostics, and configuration ordering. Full ISO builds, hardware Wi-Fi, and disk installation have not been verified here. Firmware inclusion cannot guarantee support for every adapter.

X11 / Openbox manages external windows. The running dock tracks internal desktop windows only. This is Unix-like Linux; no UNIX certification or complete POSIX compliance is claimed.

## Source

```bash
git clone https://github.com/Zerocool66612/MacqueStep.git
```

Build output, ISOs, package binaries, personal settings, and logs are excluded from Git.
