#!/bin/bash
set -euo pipefail
kit=$(cd -- "$(dirname -- "$0")" && pwd)
work=${1:-"$kit/output/build"}
mkdir -p "$work"
work=$(cd -- "$work" && pwd)
cd "$work"
python3 "$kit/tools/check-installer.py"
python3 "$kit/tools/check-host.py"
if [ -n "$(ls -A "$work")" ]; then
 echo 'Choose an empty build directory. Existing build files have been preserved.' >&2; exit 1
fi
# Ignore host defaults and pin every parent mirror as well as the normal mirrors.
# This prevents Ubuntu live-build from bootstrapping trixie from Ubuntu mirrors.
lb config --ignore-system-defaults --mode debian \
 --distribution trixie --parent-distribution trixie \
 --architectures amd64 --binary-images iso-hybrid \
 --archive-areas 'main contrib non-free non-free-firmware' \
 --parent-archive-areas 'main contrib non-free non-free-firmware' \
 --mirror-bootstrap https://deb.debian.org/debian \
 --mirror-chroot https://deb.debian.org/debian \
 --mirror-binary https://deb.debian.org/debian \
 --parent-mirror-bootstrap https://deb.debian.org/debian \
 --parent-mirror-chroot https://deb.debian.org/debian \
 --parent-mirror-binary https://deb.debian.org/debian \
 --mirror-chroot-security https://security.debian.org/debian-security \
 --mirror-binary-security https://security.debian.org/debian-security \
 --parent-mirror-chroot-security https://security.debian.org/debian-security \
 --parent-mirror-binary-security https://security.debian.org/debian-security \
 --security true --updates true --debian-installer none \
 --bootloaders 'syslinux grub-efi' --uefi-secure-boot disable \
 --firmware-chroot true --firmware-binary true \
 --iso-application MacaqueSTEP --iso-volume MACAQUESTEP_023 \
 --iso-publisher 'Made by Drew' \
 --bootappend-live 'boot=live components username=macaque-live hostname=macaquestep-live user-default-groups=audio,cdrom,dip,video,plugdev,netdev,sudo'
cp -a "$kit/config/." config/
mkdir -p config/packages.chroot
python3 "$kit/desktop/build_deb.py" --output "$work/config/packages.chroot/macaquestep-preview_0.23_all.deb"
# Capture diagnostics, and keep lb's failure status through tee.
lb build 2>&1 | tee build.log
image="$work/live-image-amd64.hybrid.iso"
if [ ! -s "$image" ]; then echo 'Build returned without the expected ISO; inspect build.log.' >&2; exit 1; fi
sha256sum "$image" > "$image.sha256"
printf '\nBuilt: %s\nChecksum: %s.sha256\nNext: boot and install to a disposable VM.\n' "$image" "$image"
