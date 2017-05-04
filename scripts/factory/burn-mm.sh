#! /bin/bash
cd /home/factory/Avalon-extras/scripts/factory
while true; do
        make isedir=/home/factory/Xilinx/14.6/ISE_DS reflash PLATFORM=$1
echo;
<<<<<<< HEAD
for i in $*;do
if [ $i = noloop ];then
break	
fi
done
=======
if [ "$2" != "" ];then
break	
fi
>>>>>>> 41d7058b7f8fecde1d45e4562a769344bb066e16
read -p "Press any key to burn next"
done
