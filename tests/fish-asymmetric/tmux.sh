#!/bin/sh
set -eu

exe="python3.5 ../../router.pyc"
exe="python3 ../../router.py"


for i in $(seq 1 6) ; do
    tmux split-pane -v $exe --addr "127.0.1.$i" --update-period 5 --startup-commands "$i.txt" &
    tmux select-layout even-horizontal
done
