@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw "%~dp0kr_vpn.py"
) else (
  start "" py -3w "%~dp0kr_vpn.py"
)
