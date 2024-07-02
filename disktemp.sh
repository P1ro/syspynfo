#!/bin/bash
DRIVEPATH="$1"

##########################################
# This tool use smartctl install         #
#                                        #
# Ubuntu:                                #
#  sudo apt-get install smartmontools    #
# Archilinux:                            #
#  sudo pacman -S smartmontools          #
##########################################

INFO="$(sudo smartctl -a $DRIVEPATH)"
TEMP=$(echo "$INFO" | grep '194 Temp' | awk '{print $10}')
if [[ $TEMP == '' ]]; then
  TEMP=$(echo "$INFO" | grep '190 Airflow' | awk '{print $10}')
fi
if [[ $TEMP == '' ]]; then
  TEMP=$(echo "$INFO" | grep 'Temperature Sensor 1:' | awk '{print $4}')
fi
if [[ $TEMP == '' ]]; then
  TEMP=$(echo "$INFO" | grep 'Current Drive Temperature:' | awk '{print $4}')
fi
if [[ $TEMP == '' ]]; then
  TEMP=$(echo "$INFO" | grep 'Temperature:' | awk '{print $2}')
fi
echo $TEMP
