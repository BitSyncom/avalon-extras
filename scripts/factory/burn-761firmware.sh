#!/bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true;do
<<<<<<< HEAD
	./burn-pmu.sh mcu noloop;
	./burn-mm.sh MM761 noloop;
=======
	./burn-pmu.sh mcu $1;
	./burn-mm.sh MM761 $1;
>>>>>>> 41d7058b7f8fecde1d45e4562a769344bb066e16
echo;
read -p "Press any key to burn next"
done
	
