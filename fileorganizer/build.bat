@echo off
REM build.bat - builds FileOrganizer.exe locally on Windows
REM Run this from Command Prompt inside the fileorganizer folder.

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Building exe...
pyinstaller file_organizer.spec --noconfirm

echo.
echo Done. Find it at dist\FileOrganizer.exe
pause
