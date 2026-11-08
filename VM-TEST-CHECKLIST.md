# VM acceptance checks — not yet completed

Use disposable VM disks, starting with BIOS, then a separate UEFI VM. Keep the ISO checksum and build.log with the results.

1. Live boot reaches the MacaqueSTEP session. The left menu and matching dock squares show. No unrelated host desktop is required.
2. Open Terminal, Files, Editor and Preferences. Try all themes and window decorations. Check minimize/reopen, close with unsaved changes, workspace switching, Clip, pins and drag/drop.
3. Start Firefox and a native rescue xterm. Confirm external windows can appear above the full-screen desktop and accept input. Check keyboard focus when returning to internal windows.
4. Confirm NetworkManager connects, DNS resolves, PipeWire plays a sound, and installer authorization prompts appear. VM devices cannot establish laptop Wi-Fi/GPU/battery compatibility.
5. Left menu → Tools → Install MacaqueSTEP. Connect the live session to the internet first; this version uses online Debian bootloader package setup. Check branded welcome, keyboard, locale, users, disk selection and final confirmation. Cancel before installation once to ensure the live session still works.
6. Start again and install onto the new blank VM disk. Check filesystem copy, user creation, bootloader and initramfs phases. Save the Calamares log if anything fails. Do not use host disk passthrough.
7. Shut down, detach the ISO, and boot only the virtual disk. Confirm the installed user's credentials work. The music welcome must play for its full duration once, without Skip/mute/Escape controls, then Setup Assistant must open. Let it finish, log out and log in again, and reboot; it must not replay. The live ISO must never show it. The temporary `macaque-live` account and its passwordless sudo rule must be absent.
8. Verify `/etc/macaquestep-installed`, `getent passwd macaque-live`, `sudo -l`, `findmnt /`, `lsblk -f` and the APT sources. Confirm the selected partition layout and intended swap behavior; no fixed swap size has been imposed by this kit.
9. Reboot and test persistence of desktop settings, files, notes and pins. Test login/logout, sound, networking and package updates. Ensure the installed disk cannot launch the live-only installer command.
10. Repeat with UEFI, documenting EFI system partition and GRUB behavior. Secure Boot is outside this build's claimed support.
11. Run `sh tools/posix-smoke.sh` in the installed system and keep its report. Passing it is only a smoke check, not standards conformance.
12. Only after successful VM installation consider a separate physical-machine test. Record GPU, wired/wireless networking, audio, battery, suspend/resume and boot results.

Record PASS/FAIL and evidence for every item. Do not label a build installation-ready based solely on successful ISO assembly.

13. Test Software Center with a small Flatpak: enable Flathub explicitly, search, install, launch, remove and inspect updates. Verify external-window focus above the desktop.
14. Confirm the X11 locker asks for the installed account password. Test Lock first, then lock-before-suspend and authentication after wake. If lock readiness cannot be confirmed, suspend must not occur.
15. Test personal-folder backups/recovery and preference recovery with expendable files. Existing files must remain unchanged.
16. Test text-size/high-contrast controls and reduced-motion welcome behavior on a fresh disposable account.

17. Test Two-Pane Files with expendable files: copy/move each direction, collision rejection, cancellation and busy-window close protection. Verify menu actions target the focused pane.
18. Bookmark folders, restart and check persistence. Exercise Ctrl+L, Ctrl+D, F5, Alt+Left/Right and Copy Path.
19. Compare a known file digest with `sha256sum`; test a mismatch and canceled hashing.
20. Scan a disposable folder with Disk Usage, cancel a scan and check partial-limit labeling. System Monitor should update without altering system state.
21. Clear Recent Documents and Activity Center; confirm the source files remain intact. Maximize a window and ensure the Clip header and bottom dock do not cover its controls.

22. Confirm the side dock starts as exactly one column on fresh and upgraded accounts. Verify all icons are reachable by scrolling; optional extra-column mode remains selectable.
23. Drag the application menu by its title to several desktop locations. Restart and resize; position should persist or be clamped into view. No strip of desktop space should remain reserved for it.
24. Click the direct live-menu Install entry. Ensure Installer Center and Calamares are visible above the desktop. Test cancellation and an authorization failure; retain diagnostics. Fullscreen should restore when Installer Center closes.
25. Complete a real installation using this rebuilt 0.23 image, reboot without media and verify boot/login. Live updates applied to an older ISO do not change the original squashfs copied to disk.
