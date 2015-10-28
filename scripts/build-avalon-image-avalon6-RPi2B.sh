#!/bin/bash
# build openwrt image for avalon6-RPi2B support platform
set -e

# Target
MACHINE=avalon4

# We prefer curl because of wget bugs
which wget > /dev/null && DL_PROG=wget && DL_PARA="-nv -O"
which curl > /dev/null && DL_PROG=curl && DL_PARA="-L -o"

$DL_PROG https://github.com/Canaan-Creative/avalon-extras/raw/master/scripts/build-avalon6-RPi2B-image.sh $DL_PARA build-avalon6-RPi2B-image.sh
chmod 0755 build-avalon6-RPi2B-image.sh
mkdir -p avalon/bin

AVA_MACHINE=$MACHINE AVA_TARGET_BOARD=pi-modelb-v2 ./build-avalon6-RPi2B-image.sh --build        && \
AVA_MACHINE=$MACHINE AVA_TARGET_BOARD=pi-modelb-v2 ./build-avalon6-RPi2B-image.sh                && \
echo "==========================================================="   && \
echo "==================== pi-modelb-v2B DONE ===================="   && \
echo "==========================================================="

rm -rf avalon/[cdlo]* build-avalon6-RPi2B-image.sh
chmod 0755 -R avalon/bin
