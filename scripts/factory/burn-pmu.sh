#!/bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true; do
	make reflash_ulink2 PMU=$1
echo;
if [ "$2" != "" ];then
break
fi
read -p "Press any key to burn next"
done
