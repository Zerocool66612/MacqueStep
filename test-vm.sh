#!/bin/bash
# Creates a new test disk only; never uses a host disk device.
set -euo pipefail
if [ "$#" -lt 2 ]; then echo 'Usage: bash test-vm.sh image.iso new-test-disk.qcow2 [bios|uefi]'; exit 1; fi
image=$(realpath -- "$1");disk=$2;mode=${3:-bios}
[ -f "$image" ] || { echo 'ISO not found' >&2; exit 1; }
case "$disk" in /dev/*) echo 'A host disk device is not a test disk file.' >&2; exit 1;; esac
[ ! -e "$disk" ] || { echo 'Choose a new disk filename; existing file preserved.' >&2; exit 1; }
for tool in qemu-system-x86_64 qemu-img; do command -v "$tool" >/dev/null || { echo "Missing: $tool"; exit 1; }; done
args=()
case "$mode" in
 bios) ;;
 uefi)
  code=/usr/share/OVMF/OVMF_CODE_4M.fd;vars=/usr/share/OVMF/OVMF_VARS_4M.fd
  [ -r "$code" ] && [ -r "$vars" ] || { echo 'Install ovmf with 4M firmware files.'; exit 1; }
  [ ! -e "$disk.vars.fd" ] || { echo 'Existing firmware state preserved; choose a new disk filename.'; exit 1; }
  cp -- "$vars" "$disk.vars.fd"
  args+=(-drive "if=pflash,format=raw,readonly=on,file=$code" -drive "if=pflash,format=raw,file=$disk.vars.fd")
  ;;
 *) echo 'Use bios or uefi'; exit 1;;
esac
qemu-img create -f qcow2 "$disk" 40G
accel=tcg
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then accel=kvm; fi
exec qemu-system-x86_64 -accel "$accel" -m 4096 -smp 2 \
 -device virtio-vga -display gtk \
 -drive "file=$disk,format=qcow2,if=virtio" -cdrom "$image" -boot once=d \
 -nic user,model=virtio-net-pci "${args[@]}"
