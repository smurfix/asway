#!/bin/bash

# This script runs the tests with the "sway" window manager instead of i3.
# 
# Some liberties had to be taken.
#

# Sway will take over your display. This is probably not what you want when
# running these tests.
if ! test -v WAYLAND_DISPLAY ; then
	echo "Not running under Wayland. Aborting."
	exit 1
fi

unset $(export | sed -ne 's/^declare -x //' -e 's/=.*//p' | grep -E -v '^(HOME|LOGNAME|PATH|USER|WAYLAND_DISPLAY|XDG_RUNTIME_DIR|USE_SWAY)$')
export PYTHONPATH=.:../sniffio:../anyio/src:../trio:../pytest-trio
export LC_ALL=C.utf-8
export SWAYSOCK="$XDG_RUNTIME_DIR/sway.test.$$"
export USE_SWAY=1
trap 'rm -f $SWAYSOCK' EXIT

set -e
if test $# -gt 0 ; then
	pytest -sxvv "$@"
else
	pytest -sxv test
fi
