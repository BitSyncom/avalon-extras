#!/bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true;do
	./burn-pmu.sh mcu $1;
	./burn-mm.sh MM761 $1;
echo;
read -p "Press any key to burn next"
done
	
