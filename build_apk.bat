@echo off
set "JAVA_HOME=D:\Downloads\Android studio\jbr"
set "PATH=%JAVA_HOME%\bin;%PATH%"
cd /d D:\GitHub\chris\android
call gradlew.bat assembleDebug
echo Build complete!
pause
