#!/bin/bash
set -a               
source $STACK_HOME/scripts/util/c.sh
set +a

# Functions
function pass(){ echo "${GREEN}✓ [PASS]${NORMAL} $1"; }
function warn(){ echo "${YELLOW}𐄂 [WARN]${NORMAL} $1"; }
function fail(){ echo "${RED}𐄂 [FAIL]${NORMAL} $1"; }

# Convert RAW to JPG
function rawtojpeg() {
  darktable-cli $1 $2 > /dev/null 2>&1
}

# Returns all .cr2 files in given path
function get_raw_files_in_path(){ echo $(ls $1 | grep "cr2");}

# Returns first .cr2 file in path
function get_first_image_in_path(){ echo $1/$(ls $1 | grep "cr2" | head -1);}

# Grabs the first (head) file in given directory
# and extracts the relevant exif tags. It then
# iterates over all other sibling files and compares
# them; ensuring they match.
# verify_exif_values_match $file
function verify_exif_values_match(){
  FILES=$(get_raw_files_in_path $(dirname $1))
  EXIF_TAGS=("-s2 -ShootingMode -ExposureMode -ImageSize -LensID -Quality -ISO -FocalLength -Aperture -ShutterSpeed")
  EXIF_CHECK=$(sed "s/:\ /:/g" <<< "$(exiftool $EXIF_TAGS "$1")")

  c=0
  for f in $FILES; do
      t=$(sed "s/:\ /:/g" <<< "$(exiftool $EXIF_TAGS "$(dirname $1)/$f")")
      echo ${EXIF_CHECK[@]} > /tmp/stacklisttwo
      echo "" > /tmp/stacklistone
      comp1="$(comm -23 <(sort /tmp/stacklistone) <(sort /tmp/stacklisttwo))"
      comp2="$(comm -23 <(sort /tmp/stacklistone) <(sort /tmp/stacklisttwo))"
      echo "${comp1+x}"
      echo "${comp2+x}"
      if [ -z $comp1 ] || [ -z $comp2 ]; then
        warn "Settings Mismatch: $f"
        # echo ${EXIF_CHECK[@]} ${t[@]} | tr ' ' '\n' | sort | uniq -u | tr '\n' ' '
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

# Return a chosen exif value from first file in given directory
# get_exif_val_from_first_file $path $tag
function get_exif_val_from_first_file() {
  FIRST_FRAME="$1/$(ls $1 | grep "cr2" | head -1)"
  v=$(sed "s/:\ /:/g" <<< "$(exiftool -s2 -$2 "$FIRST_FRAME")")
  echo $v
}


#  Helper Variables
LIGHT_FRAME_ISO=$(get_exif_val_from_first_file $LIGHTS_PATH "iso")
LIGHT_FRAME_APERTURE=$(get_exif_val_from_first_file $LIGHTS_PATH "aperture")
LIGHT_FRAME_BULB_DURATION=$(get_exif_val_from_first_file $LIGHTS_PATH "BulbDuration")
LIGHT_FRAME_SHUTTERSPEED=$(get_exif_val_from_first_file $LIGHTS_PATH "ShutterSpeedValue")

function assertSameExposureAsLight() {
  _BULB_DURATION=$(get_exif_val_from_first_file $1 "BulbDuration")
  _SHUTTERSPEED=$(get_exif_val_from_first_file $1 "ShutterSpeedValue")

  if [[ "$_BULB_DURATION" == "$LIGHT_FRAME_BULB_DURATION" ]] && [[ "$_SHUTTERSPEED" == "$LIGHT_FRAME_SHUTTERSPEED" ]];then
    pass "Exposures match"
  fi
}

# Ensures all images in a given directory fall within
# a minimum and maximum luminance value
# validate_luminance $PATH $MIN $MAX
function validate_luminance() {
  dir=$1; min=$2; max=$3;
  tmp_file="/tmp/tmp.stack.jpg"
  rm $tmp_file
  src_img="$(get_first_image_in_path $dir)"
  rawtojpeg $src_img $tmp_file
  lum=$(convert $tmp_file -format "%[fx:100*mean]" info:)
  lum_val=${lum%.*}
  if [ "$lum_val" -ge $min ] && [ "$lum_val" -le $max ]; then
    pass "Luminance ($lum_val)"
  else
    warn "Luminance ($lum_val)"
  fi
}

function verifyDarks() {
  temp=$(get_exif_val_from_first_file $DARKS_PATH 'AmbientTemperature')
  warn "TODO: Confirm ambient temperature"
  assertSameExposureAsLight $DARKS_PATH
  validate_luminance $DARKS_PATH 0 0
}

function verifyFlats() {
  FLATS_FRAME_ISO=$(get_exif_val_from_first_file $FLATS_PATH "ISO")
  FLATS_FRAME_APERTURE=$(get_exif_val_from_first_file $FLATS_PATH "APERTURE")

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
  
  validate_luminance $FLATS_PATH 40 60
}

function verify() {
  NAME=$(basename $1)
  echo ">> ${MAGENTA}Checking $NAME frames...${NORMAL}"
  FILES=$(get_raw_files_in_path $1)
  FIRST_FRAME=$(get_first_image_in_path $1)
  verify_exif_values_match $FIRST_FRAME

  if [ $NAME == $(basename $DARKS_PATH) ];then
    verifyDarks
  fi

  if [ $NAME == $(basename $FLATS_PATH) ];then
    verifyFlats
  fi
}

# 
# 
# 
# verify $LIGHTS_PATH

if [ -z ${NO_DARKS+x} ]; then verify $DARKS_PATH; else pass "Skipping darks verification"; fi
if [ -z ${NO_FLATS+x} ]; then verify $FLATS_PATH; else pass "Skipping flats verification"; fi
