#!/bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true; do
	make reflash_ulink2 PMU=$1
echo;
for i in $*;do
if [ $i = noloop ];then
break
fi
done
read -p "Press any key to burn next"
done
