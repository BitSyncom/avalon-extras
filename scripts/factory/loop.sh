#!/bin/bash
while true; do
	bash -c "$*";
	read -p "Press any key to burn next"
done
