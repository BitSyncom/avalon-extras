#! /bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true; do
        makei isedir=/home/factory/Xilinx/14.6/ISE_DS reflash PLATFORM=MM761;
	make reflash_ulink2 PMU=mcu
echo;
read -p "Press any key to burn next"
done
