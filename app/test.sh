#!/bin/bash
clear

BASE_DIR="/mnt/linux/Astrophotography_Photos/IC_1805_Heart_Nebula"

ISO=200
DARK_DIR="Dark"
FLAT_DIR="Flat"
LIGHT_DIR="Light"

MASTER_BIAS_FILE="/home/stephen/siril-auto-stacker/masters/Canon_EOS_Rebel_T8i/biases/Canon_EOS_Rebel_T8i_${ISO}_stacked_bias.fit"

function flats {
    poetry run python -m src.convert $BASE_DIR/$FLAT_DIR -fitseq

    poetry run python -m src.calibrate \
        $BASE_DIR/$FLAT_DIR/process/flats.fit \
        -f flats \
        -fitseq \
        -B $MASTER_BIAS_FILE

    poetry run python -m src.stack \
        $BASE_DIR/$FLAT_DIR/process/pp_flats.seq \
        --frame="flats"
}

function darks {
    poetry run python -m src.convert $BASE_DIR/$DARK_DIR
    poetry run python -m src.stack $BASE_DIR/$DARK_DIR/process/darks.seq --frame="darks"
}

function lights {
    poetry run python -m src.convert $BASE_DIR/$LIGHT_DIR -fitseq

    poetry run python -m src.calibrate \
        $BASE_DIR/$LIGHT_DIR/process/lights.fit \
        -f lights \
        -fitseq \
        -F $BASE_DIR/$FLAT_DIR/process/stacked_pp_flats.fit \
        -D $BASE_DIR/$DARK_DIR/process/stacked_darks.fit

    poetry run python -m src.register \
        $BASE_DIR/$LIGHT_DIR/process/pp_lights.seq \
        --maxstars=100

    poetry run python -m src.stack \
        $BASE_DIR/$LIGHT_DIR/process/r_pp_lights.seq \
        --frame="lights"
}

function postprocess {
    poetry run python -m src.postprocess \
        $BASE_DIR/$LIGHT_DIR/process/stacked_r_pp_lights.fit \
        --target="NGC 651"
}

flats
darks 
lights

# postprocess
