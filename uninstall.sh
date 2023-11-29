#!/bin/bash
set -a               
source config.ini
set +a

rm -r $STACK_HOME
rm  ~/.local/bin/stack