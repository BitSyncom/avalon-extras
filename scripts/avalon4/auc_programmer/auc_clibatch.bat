@echo off
:startprog
echo %date%_%time%   "��д��ʼ"
C:\Keil_v5\UV4\UV4 -f auc_programmer.uvproj -j0 -O avalon-usb-converter.log
if %ERRORLEVEL% EQU 0 (
	echo "��д��ɣ��������һ��"
) else (
	echo "��дδ�ɹ������飡"
)
REM sleep for 2 seconds
ping -N 2 127.0.0.1 > NUL
goto :startprog