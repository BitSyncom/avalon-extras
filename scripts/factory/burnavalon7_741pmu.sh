#! /bin/bash
cd /home/factory/Burn_tool_script
while true; do
	make reflash_ulink2 pmu="pmu741"
echo;
read -p "Press any key to burn next"
done
