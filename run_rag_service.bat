@echo off
set PYTHONPATH=%PYTHONPATH%;.

if not exist .env (
    echo [ERREUR] Le fichier .env est introuvable.
    echo Veuillez copier .env.example vers .env et y ajouter votre OPENAI_API_KEY.
    pause
    exit /b
)

if exist .venv\Scripts\uvicorn.exe (
    echo Activation de l'environnement virtuel...
    .venv\Scripts\uvicorn.exe rag_service.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo Utilisation de uvicorn global...
    uvicorn rag_service.main:app --host 0.0.0.0 --port 8000 --reload
)
