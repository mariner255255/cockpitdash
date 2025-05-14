@echo off
echo Running task manager backup script at %date% %time%
bash "C:\Users\me\new-datadash\docs\task-manger\backup.sh"
if %ERRORLEVEL% EQU 0 (
  echo Backup completed successfully
) else (
  echo Backup failed with error code %ERRORLEVEL%
)
pause
