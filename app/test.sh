#!/bin/bash
clear
BASE_DIR="/home/stephen/Pictures/NGC_651"
MASTER_BIAS_FILE="/home/stephen/Pictures/NGC_651/masters/master_bias_200.fit"

function flats {
    poetry run python -m src.convert $BASE_DIR/flats -fitseq

    poetry run python -m src.calibrate \
        $BASE_DIR/flats/process/flats.fit \
        -f flats \
        -fitseq \
        -B $MASTER_BIAS_FILE

    poetry run python -m src.stack \
        $BASE_DIR/flats/process/pp_flats.seq \
        --frame="flats"
}

function darks {
    poetry run python -m src.convert $BASE_DIR/darks -fitseq
    poetry run python -m src.stack $BASE_DIR/darks/process/darks.seq --frame="darks"
}

function lights {
    poetry run python -m src.convert $BASE_DIR/lights -fitseq

    poetry run python -m src.calibrate \
        $BASE_DIR/lights/process/lights.fit \
        -f lights \
        -fitseq \
        -F $BASE_DIR/flats/process/stacked_pp_flats.fit \
        # -D $BASE_DIR/darks/process/stacked_darks.fit

    
    poetry run python -m src.register \
        $BASE_DIR/lights/process/pp_lights.seq \
        --maxstars=100

    poetry run python -m src.stack \
        $BASE_DIR/lights/process/r_pp_lights.seq \
        --frame="lights"

}

function postprocess {
    poetry run python -m src.postprocess \
        $BASE_DIR/lights/process/stacked_r_pp_lights.fit \
        --target="triangulum galaxy" 
}

flats
# darks 
lights

# postprocess