@echo off
title Modern Educational Complex - SMS Online Internet Portal
color 0A
echo ======================================================================
echo    MODERN EDUCATIONAL COMPLEX - SCHOOL MANAGEMENT SYSTEM (SMS)
echo           PUBLIC ONLINE INTERNET TUNNEL LAUNCHER
echo ======================================================================
echo.
echo Launching web server with secure online tunnel for remote access...
echo.
python run_web.py --port 8000 --public
pause
