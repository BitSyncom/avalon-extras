#! /bin/bash
cd ~/Burn_tool_script
while true; do 
        make isedir=/home/factory/Xilinx/14.6/ISE_DS reflash_2;
echo;
read -p "Press any key to burn next"
done
