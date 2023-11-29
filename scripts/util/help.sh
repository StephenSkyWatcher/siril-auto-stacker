#!/bin/bash
set -a               
source $INSTALL_LOCATION/scripts/util/c.sh
set +a

printf '%s\n%+s\n%s\n\n' \
"${GREEN}${DIM}-----------------------------------${NORMAL}" \
" 📷 ${YELLOW}☆ ✯   ${GREEN}${UNDERLINE}Siril Auto Stack${NO_UNDERLINE} ${YELLOW} ✯ ☆${NORMAL}  📷" \
"${GREEN}${DIM}-----------------------------------${NORMAL}"


useage () {
cat <<-ENDOFMESSAGE

${DIM}ie.  ${NORMAL} stack ~/pictures/andromeda/

    -h, --help              Shows this help menu

    --master-biases-dir     [default]
                            $(pwd)/masters/
                            
                            Directory to find bias masters.
                            
                            Must follow naming convention:
                            bias-[iso]-master.fit
                            ie. bias-100.master.fit

    -B, --master-bias       Master bias file
    -D, --master-dark       Master dark file
    -F, --master-flat       Master flat file

    -b, --biases            Location to find for bias frames
    -d, --darks             Location to find for dark frames
    -f, --flats             Location to find for flat frames

    -p, --process-dir       Location for processed files
    -o, --out               Location for finals stacked fits files

    -g, --remove-green      Remove green noise from final stack

    -n, --no-verify         Skips the file verification process

[Dependencies]

    libimage-exiftool-perl
    imagemagick

ENDOFMESSAGE
}

description () {
cat <<-ENDOFMESSAGE

Stacks a directory of lights, flats and darks and provides 
you with a sample JPG as well as final stacked versions

ENDOFMESSAGE
}

longdescription () {
cat <<-ENDOFMESSAGE

ENDOFMESSAGE
}


printf "%s\n" "${BLUE}➔ DESCRIPTION${NORMAL}"
description;
printf "%s\n" "${BLUE}➔ USEAGE${NORMAL} ${DIM}stack [opt]...${NORMAL}"
useage;