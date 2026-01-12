@echo off
echo [1/3] Installation des dependances du Worker...
cd worker_fleet
call npm install
if %errorlevel% neq 0 (
    echo [ERREUR] L'installation de npm a echoue.
    pause
    exit /b %errorlevel%
)

echo [2/3] Verification de Redis...
powershell -Command "Test-NetConnection -ComputerName localhost -Port 6379"
if %errorlevel% neq 0 (
    echo [ATTENTION] Redis ne semble pas tourner sur localhost:6379.
    echo Assurez-vous de lancer Redis avant de demarrer le worker.
)

echo [3/3] Demarrage du Worker en mode developpement...
npm start
pause
