#!/bin/bash
set -a               
source $INSTALL_LOCATION/scripts/util/c.sh
set +a

# Functions
function pass(){ echo "${GREEN}✓ [PASS]${NORMAL} $1"; }
function warn(){ echo "${YELLOW}𐄂 [WARN]${NORMAL} $1"; }
function fail(){ echo "${RED}𐄂 [FAIL]${NORMAL} $1"; }

function get_raw_files_in_path(){ echo $(ls $1 | grep "cr2");}
function get_first_image_in_path(){ echo $1/$(ls $1 | grep "cr2" | head -1);}

function verify_exif_values_match(){
  FILES=$(get_raw_files_in_path $(dirname $1))
  EXIF_TAGS=("-s2 -ShootingMode -ExposureMode -ImageSize -LensID -Quality -ISO -FocalLength -Aperture -ShutterSpeed")
  EXIF_CHECK=$(sed "s/:\ /:/g" <<< "$(exiftool $EXIF_TAGS "$1")")
  c=0
  for f in $FILES; do
      t=$(sed "s/:\ /:/g" <<< "$(exiftool $EXIF_TAGS "$(dirname $1)/$f")")
      if [ "$EXIF_CHECK" != "$t" ]; then
        warn Settings Mismatch: $f
        echo ${EXIF_CHECK[@]} ${t[@]} | tr ' ' '\n' | sort | uniq -u | tr '\n' ' '
        echo ''
        c=$((c+1)) 
      fi
  done

  if [ "$c" != 0 ]; then
    warn "$c $1 files mismatched"
  else
    total=$(wc -w <<< "$FILES")
    pass "$total .CR2 files checked"
  fi
}

# Return a chosen exit value
function get_exif_val() {
  FIRST_FRAME="$1/$(ls $1 | grep "cr2" | head -1)"
  v=$(sed "s/:\ /:/g" <<< "$(exiftool -s2 -$2 "$FIRST_FRAME")")
  echo $v
}


#  Helper Variables
LIGHT_FRAME_ISO=$(get_exif_val $LIGHTS_PATH "ISO")
LIGHT_FRAME_APERTURE=$(get_exif_val $LIGHTS_PATH "APERTURE")
FLATS_FRAME_ISO=$(get_exif_val $FLATS_PATH "ISO")
FLATS_FRAME_APERTURE=$(get_exif_val $FLATS_PATH "APERTURE")

# function validate_dark_frames() {
# }

function validate_luminance() {
  dcraw -c -w $(get_first_image_in_path $FLATS_PATH) | pnmtopng > "/tmp/tmp.stack.png";
  lum=$(convert /tmp/tmp.stack.png -format "%[fx:100*mean]" info:)
  FLAT_LUM_VALUE=${lum%.*}
  if [ "$FLAT_LUM_VALUE" -ge 35 ] && [ "$FLAT_LUM_VALUE" -le 70 ]; then
    pass "Luminance good! ($FLAT_LUM_VALUE)"
  fi
}

function verifyDarks() {
  # - Same temperature
  # - Lens cap on
  # - Same exposure time as Lights
  echo ""
}

function verifyLights() {
  # - Same temperature
  # - Lens cap on
  # - Same exposure time as Lights
  echo ""
}

function verifyFlats() {
  # Verify flats have same ISO and Aperture as Lights
  if [ $LIGHT_FRAME_ISO != $FLATS_FRAME_ISO ]; then
    fail "Flat frame ISO's do not match Lights Expected: $LIGHT_FRAME_ISO, but received $FLATS_FRAME_ISO"
  else
    pass "ISO matches lights"
  fi

  if [ $LIGHT_FRAME_APERTURE != $FLATS_FRAME_APERTURE ]; then
    fail "Flat frame apertures's do not match Lights Expected: $LIGHT_FRAME_APERTURE, but received $FLATS_FRAME_APERTURE"
  else
    pass "Aperture matches lights"
  fi
  
  validate_luminance
}

function verifyFilesMatchSettings() {
  NAME=$(basename $1)
  echo ">> ${MAGENTA}Checking $NAME frames...${NORMAL}"
  FILES=$(get_raw_files_in_path $1)
  FIRST_FRAME=$(get_first_image_in_path $1)
  verify_exif_values_match $FIRST_FRAME

  if [ $NAME == $(basename $DARKS_PATH) ];then
    verifyDarks
  fi

  if [ $NAME == $(basename $LIGHTS_PATH) ];then
    verifyLights
  fi

  if [ $NAME == $(basename $FLATS_PATH) ];then
    verifyFlats
  fi
}

verifyFilesMatchSettings $LIGHTS_PATH
verifyFilesMatchSettings $DARKS_PATH
verifyFilesMatchSettings $FLATS_PATH



# ./$STACK_HOME/scripts/preprocess.sh -i 100 -d $dir -c $CONFIG_DIR
# ./$STACK_HOME/scripts/post-remove-green.sh -d $dir/stacked/ -f stacked-lights.fit -c $CONFIG_DIR &&
# ./$STACK_HOME/scripts/post-preview-autostretch.sh -d $dir/stacked/ -f nogreen-stacked-lights.fit -c $CONFIG_DIR


# INSTALL_LOCATION=~/.local/share
# STACK_HOME=$INSTALL_LOCATION/stack
# CONFIG_DIR=$STACK_HOME/config.ini
# DEFAULT_MASTER_BIASES=$INSTALL_LOCATION/stack/masters