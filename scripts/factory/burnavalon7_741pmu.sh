#! /bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true; do
	make reflash_ulink2 pmu="pmu741"
echo;
read -p "Press any key to burn next"
done
