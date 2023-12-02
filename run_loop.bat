@echo off
:restart_loop
echo [AOS] Starting server.
run.exe

if errorlevel 1 (
echo Exited with 1 or higher, restart server.
goto restart_loop
) else (
echo Exited with 0, stopping.
)

echo Wait for 10 seconds
timeout /t 10
