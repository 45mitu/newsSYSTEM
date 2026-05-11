@echo off
cd /d "d:\mituki\projects\ニュース自動配信システム"
if not exist logs mkdir logs
set LOGFILE=logs\daily_%date:~0,4%%date:~5,2%%date:~8,2%.log
echo [%date% %time%] Starting >> %LOGFILE%
python -m src.main >> %LOGFILE% 2>&1
echo [%date% %time%] Done (exit %errorlevel%) >> %LOGFILE%
