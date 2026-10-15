#!/bin/sh
# Runs a Craft CLI (or any headless tool) in a bubblewrap sandbox:
# no network, no access to the home directory, only the given work folder is writable.
# Usage: craft-sandbox.sh WORKDIR /path/to/xyz-cli [ARGS...]
#   WORKDIR  folder with copies of the input files; the only place the tool can read and write
#   The tool binary is mounted read-only. Paths inside the sandbox are the same as outside.
# Needs: bubblewrap (Debian: apt install bubblewrap). Stops with an error if it is missing.
set -eu

if [ $# -lt 2 ]; then
  echo "usage: $0 WORKDIR TOOL [ARGS...]" >&2
  exit 2
fi
work=$(realpath "$1"); tool=$(realpath "$2"); shift 2
command -v bwrap >/dev/null || { echo "bubblewrap (bwrap) fehlt" >&2; exit 3; }
[ -d "$work" ] || { echo "WORKDIR fehlt: $work" >&2; exit 2; }
case "$work" in /|/home|/root|"$HOME") echo "WORKDIR zu weit: $work" >&2; exit 2;; esac

# Read-only system folders that exist on this machine (Debian keeps /bin and /lib as symlinks into /usr).
sys=""
for d in /usr /bin /sbin /lib /lib64 /lib32 /etc/fonts /etc/ssl /usr/share/fonts; do
  [ -e "$d" ] && sys="$sys --ro-bind $d $d"
done

# shellcheck disable=SC2086
exec bwrap \
  $sys \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$tool" "$tool" \
  --bind "$work" "$work" \
  --chdir "$work" \
  --setenv HOME "$work/.home" \
  --setenv XDG_CONFIG_HOME "$work/.home/config" \
  --setenv XDG_DATA_HOME "$work/.home/data" \
  --setenv XDG_CACHE_HOME "$work/.home/cache" \
  --unshare-all --die-with-parent --new-session \
  "$tool" "$@"
