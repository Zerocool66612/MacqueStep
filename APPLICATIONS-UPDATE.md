# MacaqueSTEP 0.23.2 applications update

The Applications launcher (four-square dock icon or Ctrl+Space) now lists built-in tools and installed desktop applications together, including Firefox ESR. Native entries are refreshed whenever the launcher is reopened after closing it. Search and double-click or Enter to launch. Native application windows are managed by Openbox; fullscreen desktop mode is relaxed when launching so those windows can be seen. The running-app dock still tracks internal MacaqueSTEP windows only.

The ISO package list now explicitly includes gio and an icon theme, plus GIMP, Audacity, VLC, Evince, and Engrampa. Firefox ESR was already in the ISO package list. Package installation requires the normal Debian build downloads.

Includes the 0.23.1 Calamares slideshow fix and branding build check. Desktop package version remains 0.23. Build a new ISO from this kit with sudo bash build-iso.sh on the normal build machine, then flash output/build/live-image-amd64.hybrid.iso.

A full ISO build and disk installation are not verified in the preparation environment.
