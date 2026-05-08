@echo off
REM MongoDB Windows 版下载脚本
REM 下载 MongoDB 7.0 Community Server for Windows

setlocal enabledelayedexpansion

set MONGODB_VERSION=7.0.15
set MONGODB_URL=https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-%MONGODB_VERSION%.zip
set DOWNLOAD_DIR=%~dp0..\mongodb
set MONGODB_ZIP=%DOWNLOAD_DIR%\mongodb.zip

echo ============================================================
echo MongoDB %MONGODB_VERSION% Windows 下载脚本
echo ============================================================

REM 创建目录
if not exist "%DOWNLOAD_DIR%" (
    echo 创建目录: %DOWNLOAD_DIR%
    mkdir "%DOWNLOAD_DIR%"
)

REM 检查是否已下载
if exist "%DOWNLOAD_DIR%\bin\mongod.exe" (
    echo MongoDB 已存在: %DOWNLOAD_DIR%\bin\mongod.exe
    goto :test
)

echo.
echo [1] 下载 MongoDB %MONGODB_VERSION%...
echo     URL: %MONGODB_URL%
echo.

REM 使用 PowerShell 下载
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%MONGODB_URL%' -OutFile '%MONGODB_ZIP%' -UseBasicParsing}"

if %errorlevel% neq 0 (
    echo 下载失败! 请手动下载:
    echo   %MONGODB_URL%
    exit /b 1
)

echo 下载完成!

echo.
echo [2] 解压 MongoDB...

REM 使用 PowerShell 解压
powershell -Command "& {Expand-Archive -Path '%MONGODB_ZIP%' -DestinationPath '%DOWNLOAD_DIR%' -Force}"

if %errorlevel% neq 0 (
    echo 解压失败!
    exit /b 1
)

REM 移动文件到正确位置
for /d %%i in ("%DOWNLOAD_DIR%\mongodb-*") do (
    echo 移动 %%i\bin 到 %DOWNLOAD_DIR%\bin
    xcopy "%%i\bin\*" "%DOWNLOAD_DIR%\bin\" /E /I /Y
    rmdir "%%i" /s /q
)

REM 删除 zip 文件
del "%MONGODB_ZIP%"

echo 解压完成!

:test
echo.
echo [3] 验证安装...
"%DOWNLOAD_DIR%\bin\mongod.exe" --version

if %errorlevel% neq 0 (
    echo 验证失败!
    exit /b 1
)

echo.
echo ============================================================
echo MongoDB 安装完成!
echo ============================================================
echo.
echo 启动命令:
echo   %DOWNLOAD_DIR%\bin\mongod --dbpath "%~dp0..\mongodb_data"
echo.
echo 或使用:
echo   scripts\start_mongodb.bat
echo.
