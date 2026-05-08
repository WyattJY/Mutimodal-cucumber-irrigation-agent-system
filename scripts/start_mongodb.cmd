@echo off
echo ============================================
echo Starting MongoDB 7.0.15
echo ============================================

set SCRIPT_DIR=%~dp0
set MONGOD=%SCRIPT_DIR%..\mongodb\bin\mongod.exe
set DATA_DIR=%SCRIPT_DIR%..\mongodb_data_fresh

echo Creating data directory...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo Starting mongod...
echo   Data: %DATA_DIR%
echo   Port: 27017
echo.
echo Press Ctrl+C to stop MongoDB
echo.

"%MONGOD%" --dbpath "%DATA_DIR%" --bind_ip 127.0.0.1 --port 27017
