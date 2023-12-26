#!/bin/bash
set -a               
source $STACK_HOME/scripts/util/c.sh
set +a

# PWD=`pwd`
# while getopts ":d:i:b:c:" opt; do
#   case $opt in
#     d) _WORKING_DIRECTORY="$OPTARG"
#     ;;
#     # i) ISO="$OPTARG"
#     # ;;
#     b) _MASTER_BIASES_DIR="$OPTARG"
#     ;;
#     # c) CONFIG="$OPTARG"
#     # ;;
#     \?) echo "Invalid option -$OPTARG" >&2
#     exit 1
#     ;;
#   esac

#   case $OPTARG in
#     -*) echo "Option $opt needs a valid argument"
#     exit 1
#     ;;
#   esac
# done

# set -a               
# source $CONFIG
# set +a

ISO=$(get_exif_val_from_first_file $LIGHTS_PATH "iso")

# Masters
MASTERS_DIR="$STACK_HOME/masters"
MASTER_BIASES_DIR="${_MASTER_BIASES_DIR:-$MASTERS_DIR}"
MASTER_BIAS_FILE=$MASTER_BIASES_DIR/bias-$ISO-master.fit
ESC_MASTER_BIAS_FILE=$(echo "${MASTER_BIAS_FILE}" | sed -e 's/[]$\/.*[\^]/\\&/g' )

# Working files/directories
WORKING_DIRECTORY="${_WORKING_DIRECTORY:=$PWD}"
CUR_PREPROCESS_SCRIPT="/tmp/tmp.stack-preprocess-cur.ssf"

# Ensure that all the calibration directories exist
CALIBRATION_DIRS=( "flats" "lights" "darks" )
for DIR in "${CALIBRATION_DIRS[@]}"; do :; if [ ! -d "$WORKING_DIRECTORY/$DIR" ]; then
    echo "$WORKING_DIRECTORY/$DIR does not exist."; exit 1; fi
done


if test -f "$MASTER_BIAS_FILE"; then
    echo "Working directory: $WORKING_DIRECTORY"
    echo "Master Bias File: $MASTER_BIAS_FILE"
else
    echo "[$1] does not exist"
    exit 1
fi

cat $STACK_HOME/templates/preprocess.ssf | sed -e 's/%MASTER_BIAS_FILE%/'"$ESC_MASTER_BIAS_FILE"'/' > $CUR_PREPROCESS_SCRIPT

Siril -d $WORKING_DIRECTORY -s $CUR_PREPROCESS_SCRIPT
exit 0