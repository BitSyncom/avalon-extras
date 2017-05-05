#!/bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true;do
	./burn-pmu.sh mcu noloop;
	./burn-mm.sh MM761 noloop;
echo;
read -p "Press any key to burn next"
done
	
