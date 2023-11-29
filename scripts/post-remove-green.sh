#!/bin/bash

PWD=`pwd`
while getopts ":d:f:c:" opt; do
  case $opt in
    d) _WORKING_DIRECTORY="$OPTARG"
    ;;
    f) WORKING_FILE="$OPTARG"
    ;;
    c) CONFIG="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done

set -a               
source $CONFIG
set +a

# Masters
MASTERS_DIR="$STACK_HOME/masters"
STACKED_LIGHTS_FILE="${WORKING_FILE:=stacked-lights.fit}"

# Working files/directories
WORKING_DIRECTORY="${_WORKING_DIRECTORY:=$PWD}"
CUR_POSTPROCESS_SCRIPT="/tmp/tmp.post-remove-green.ssf"

# # Ensure that all the calibration directories exist
# CALIBRATION_DIRS=( "flats" "lights" "darks" )
# for DIR in "${CALIBRATION_DIRS[@]}"; do :; if [ ! -d "$WORKING_DIRECTORY/$DIR" ]; then
#     echo "$WORKING_DIRECTORY/$DIR does not exist."; exit 1; fi
# done

cat $STACK_HOME/templates/post-remove-green.ssf | sed -e 's/%FILE%/'"$STACKED_LIGHTS_FILE"'/' > $CUR_POSTPROCESS_SCRIPT

Siril -d $WORKING_DIRECTORY -s $CUR_POSTPROCESS_SCRIPT
exit 0