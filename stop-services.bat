@echo off
echo Stopping RAG Platform Services...
echo.

echo [1/2] Stopping BullMQ Worker...
taskkill /FI "WINDOWTITLE eq BullMQ Worker*" /F 2>nul

echo [2/2] Stopping Redis...
docker-compose down

echo.
echo All services stopped.
pause
