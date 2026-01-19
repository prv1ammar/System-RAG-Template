@echo off
echo Starting RAG Platform Services...
echo.

REM Start Redis
echo [1/3] Starting Redis...
docker-compose up -d redis
timeout /t 3 /nobreak > nul

REM Install Node dependencies if needed
if not exist "node_modules" (
    echo [2/3] Installing Node.js dependencies...
    call npm install
) else (
    echo [2/3] Node.js dependencies already installed
)

REM Start BullMQ Worker
echo [3/3] Starting BullMQ Worker...
start "BullMQ Worker" cmd /k "npm run worker"

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo Redis: localhost:6379
echo BullMQ Worker: Running in separate window
echo.
echo To start Streamlit: .\venv\Scripts\streamlit run app.py
echo To stop services: run stop-services.bat
echo.
pause
