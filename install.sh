# #!/bin/bash
# set -a               
# source ./config.ini
# set +a

# MAGENTA=$(tput setaf 5)
# GREEN=$(tput setaf 2)
# RED=$(tput setaf 1)
# DIM=$(tput dim)
# NORMAL=$(tput sgr0)

# function installTool() {
#     echo "installing exiftool"
# }

# function checkExists() {
#     # a=$(dpkg -s $1 | grep "Status: install ok installed")    
#     a=$(which "$1" | grep -o "$1")
    
#     [[  $a && ${a-x} ]] && echo " ${GREEN}✓${NORMAL} $1 ${DIM}already installed${NORMAL}" || installTool $1
# }

# function checkDependencies() {
#     echo "${MAGENTA}Checking dependencies...${NORMAL}"
#     # checkExists "libimage-exiftool-perl"
#     # checkExists "imagemagick"
#     checkExists "exiftool"
#     checkExists "convert"
#     checkExists "Siril"
#     checkExists "darktable"
# }

# function installStacker() {
#     if [ -d "$STACK_HOME" ]; then
#         echo ""
#         echo "stack is already installed!"
#         echo ""
#         echo "${DIM}try:${NORMAL}"
#         echo "stack --uninstall"
#         exit 1
#     fi

#     mkdir $STACK_HOME
#     cp config.ini $STACK_HOME
#     cp uninstall.sh $STACK_HOME

#     cp stack $STACK_HOME
#     cp -r templates $STACK_HOME/templates
#     cp -r masters $STACK_HOME/masters
#     cp -r scripts $STACK_HOME/scripts

#     sudo ln -s $STACK_HOME/stack ~/.local/bin/stack
# }

# checkDependencies
# installStacker && echo "${GREEN}Install Success${NORMAL}" || echo "${RED}Install Failed${NORMAL}"