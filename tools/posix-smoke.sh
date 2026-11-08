#!/bin/sh
# Small engineering smoke check; this is NOT POSIX or UNIX conformance testing.
set -eu
printf 'MacaqueSTEP POSIX smoke report — not a conformance verdict\n'
uname -a
getconf _POSIX_VERSION
getconf _XOPEN_VERSION
LC_ALL=C sh -c '
 value=$(printf "%s\n" alpha beta | sed -n "2p")
 test "$value" = beta
 printf "%s\n" 3 1 2 | sort -n | awk "BEGIN {expected=1} {if (\$0 != expected++) exit 1} END {if (NR != 3) exit 1}"
 test "$(printf abc | wc -c | tr -d " ")" -eq 3
'
printf 'PASS sampled shell, pipeline, sed, sort, awk, test and wc behavior.\n'
printf 'Remaining: standards requirement mapping, headers/C interfaces, locales, options, error behavior and full installed-system validation.\n'
