@echo off
REM 启动 MongoDB 服务器

set SCRIPT_DIR=%~dp0
set MONGO_BIN=%SCRIPT_DIR%..\mongodb\bin
set MONGO_DATA=%SCRIPT_DIR%..\mongodb_data
set MONGO_LOG=%SCRIPT_DIR%..\mongodb.log

echo ============================================================
echo Starting MongoDB Server
echo ============================================================
echo Data Path: %MONGO_DATA%
echo Log Path: %MONGO_LOG%
echo.

REM 检查数据目录
if not exist "%MONGO_DATA%" (
    echo ERROR: MongoDB data directory not found!
    echo Please copy mongodb_data from Greenhouse_RAG project.
    exit /b 1
)

REM 启动 MongoDB
echo Starting mongod...
"%MONGO_BIN%\mongod" --dbpath "%MONGO_DATA%" --logpath "%MONGO_LOG%" --bind_ip 127.0.0.1 --port 27017

echo MongoDB stopped.
