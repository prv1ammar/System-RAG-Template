# Guide de Test : Architecture BullMQ

Ce document explique comment démarrer et tester votre nouvelle infrastructure de workers asynchrones.

## 1. Pré-requis
- **Redis** : Doit être lancé sur `localhost:6379`.
- **Node.js** : Pour la flotte de workers.
- **Python** : Pour l'API FastAPI.

## 2. Démarrage des Composants

### A. Démarrer Redis
Si vous n'avez pas Redis, vous pouvez utiliser Docker :
```bash
docker run -d -p 6379:6379 redis:alpine
```
Ou lancez votre instance locale.

### B. Installer et Démarrer le Worker
Ouvrez une nouvelle console :
```powershell
cd worker_fleet
npm install
npm start
```

### C. Démarrer l'API RAG
Assurez-vous que le serveur FastAPI est lancé :
```powershell
.\run_rag_service.bat
```

## 3. Scénarios de Test

### Test 1 : Ingestion Asynchrone
Envoyez un fichier PDF ou TXT :
```bash
curl -X 'POST' 'http://localhost:8000/bots/VOTRE_BOT_ID/ingest' -F 'file=@chemin/mon_doc.pdf'
```
**Attendu** : 
- L'API répond immédiatement : `{"status": "queued", "job_id": "...", ...}`.
- Dans la console du **Worker**, vous verrez les logs : `[Job ...] Processing INGEST_DOCUMENT...`.

### Test 2 : Suppression Massive
```bash
curl -X 'DELETE' 'http://localhost:8000/bots/VOTRE_BOT_ID'
```
**Attendu** :
- Le worker nettoie Supabase en arrière-plan.
- Log worker : `[Job ...] Processing DELETE_BOT... Successfully deleted bot and X chunks.`

### Test 3 : Ré-indexation
```bash
curl -X 'POST' 'http://localhost:8000/bots/VOTRE_BOT_ID/reindex'
```
**Attendu** :
- Le worker parcourt tous les documents et regénère les vecteurs.

## 4. Troubleshooting
- **Erreur Connection Redis** : Vérifiez que Redis écoute bien sur le port 6379.
- **Erreur API Key** : Vérifiez le fichier `.env` à la racine pour Supabase et OpenAI.
