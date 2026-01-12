# System RAG Platform Documentation

Bienvenue dans la documentation complète du projet **System RAG Platform**. Ce projet est une solution complète pour la création, la gestion et le déploiement de systèmes de génération augmentée par récupération (RAG).

## 🌟 Vue d'ensemble

Le projet se divise en deux composants principaux :
1.  **Chatbot Configuration Platform (UI)** : Une application Streamlit pour configurer graphiquement des agents RAG basés sur Supabase.
2.  **Portable RAG Service (API)** : Un service backend robuste (FastAPI) permettant de gérer plusieurs bots indépendants avec une isolation stricte des données via `bot_id`.

---

## 🏗️ Architecture du Projet

```text
System-RAG-Template/
├── app.py                  # Point d'entrée de la plateforme UI (Streamlit)
├── rag_service/           # Nouveau service RAG portable (Backend-first)
│   ├── main.py            # API FastAPI
│   ├── service.py         # Orchestration
│   ├── rag_engine.py      # Pipeline LangChain & ChromaDB
│   ├── database.py        # Stockage JSON des configurations
│   └── models.py          # Modèles Pydantic (Schémas JSON)
├── agent_FAQ/             # Logique des agents pour la plateforme UI
├── custom_chatbot/        # Dossier de sortie pour les chatbots générés par l'UI
├── utils/                 # Utilitaires (LLMs, détection de langue)
└── run_rag_service.bat    # Script de lancement rapide du backend
```

---

## 🚀 1. Portable RAG Service (Le Backend)

Ce service est conçu pour être intégré dans des systèmes externes. Il permet de transformer un pipeline LangChain en un service JSON réutilisable.

### Caractéristiques Clés
- **Isolation par BOT_ID** : Chaque bot a son propre corpus de documents. Aucune fuite de données entre les bots.
- **Support Multi-format** : PDF, DOCX, XLSX, TXT.
- **Exportation JSON** : Exportez la configuration complète d'un bot et les métadonnées de ses documents.
- **Sans dépendance UI** : Conçu pour être consommé par n'importe quel frontend ou service tiers.

### Endpoints API Principaux
- `POST /bots` : Créer un nouvel assistant avec ses propres règles.
- `POST /bots/{bot_id}/ingest` : Charger et indexer un document pour un bot spécifique.
- `POST /bots/{bot_id}/ask` : Poser une question au bot. Réponse garantie au format JSON strict.
- `GET /bots/{bot_id}/export` : Exporter l'état et la configuration du bot.

---

## 🤖 2. Chatbot Configuration Platform (L'Interface)

Une interface intuitive pour générer des instances de chatbots personnalisées.

### Fonctionnement
1. **Configuration** : Connectez votre base de données Supabase et configurez vos clés OpenAI.
2. **Personnalisation** : Définissez le prompt système et le modèle à utiliser.
3. **Génération** : Créez un package complet prêt à l'emploi (situé dans `custom_chatbot/`).
4. **Test** : Interface de chat intégrée pour valider le comportement de l'agent immédiatement.

---

## 🛠️ Installation et Démarrage

### Prérequis
- Python 3.9+
- Clé API OpenAI

### Installation
1.  **Dépendances** :
    ```bash
    pip install -r requirements.txt
    pip install -r rag_service/requirements.txt
    ```

2.  **Configuration (CRUCIAL)** :
    Le service a besoin d'une clé OpenAI pour fonctionner.
    - Copiez le fichier `.env.example` en `.env` :
      ```powershell
      copy .env.example .env
      ```
    - Ouvrez le fichier `.env` et remplacez `your_sk_key_here` par votre véritable clé OpenAI.

### Lancement
- **Lancer l'interface UI** :
  ```bash
  streamlit run app.py
  ```
- **Lancer le service Backend RAG** :
  ```bash
  .\run_rag_service.bat
  ```

---

## 🔐 Sécurité et Gouvernance

- **Isolation Stricte** : Le `bot_id` est utilisé comme filtre de métadonnées obligatoire dans toutes les recherches vectorielles.
- **Contrôle du Scope** : L'IA est instruite via le prompt système pour ne répondre qu'en utilisant le contexte fourni.
- **Confidentialité** : Les documents sont stockés localement (pour le service portable) ou dans votre instance Supabase (pour la plateforme UI).

---

## 📤 Format de Réponse Standard (JSON)

Toutes les réponses du service RAG suivent ce format :
```json
{
  "bot_id": "uuid",
  "answer": "La réponse en langage naturel",
  "sources": [
    {
      "document_id": "...",
      "page": 1
    }
  ],
  "confidence": "high | medium | low"
}
```

---

## ⚡ Architecture Asynchrone (BullMQ)

Pour garantir la performance et la scalabilité, les tâches lourdes sont déportées vers des workers **BullMQ** (Node.js + Redis).

### 🛠️ Travaux en arrière-plan
Les opérations suivantes ne bloquent plus l'API et retournent un `job_id` immédiatement :

1.  **Ingestion de Documents** : Découpage (chunking) et génération d'embeddings.
2.  **Suppression Massive (`DELETE_BOT`)** : Nettoyage complet de la base vectorielle et des métadonnées d'un bot.
3.  **Ré-indexation (`RE_EMBED_BOT`)** : Mise à jour globale des vecteurs (utile lors d'un changement de modèle LLM).

### 🚦 API Endpoints Asynchrones
- `POST /bots/{bot_id}/ingest` : Lance l'ingestion asynchrone.
- `DELETE /bots/{bot_id}` : Lance la suppression complète en arrière-plan.
- `POST /bots/{bot_id}/reindex` : Relance le calcul des embeddings pour tout le bot.

### 🧩 Composants BullMQ
- **Broker** : Redis (port 6379).
- **Producers** : FastAPI (Python) injectant des jobs structurés dans Redis.
- **Workers** : Flotte Node.js/TypeScript située dans `/worker_fleet`.

---

## 📄 Licence
Ce projet est développé à des fins de déploiement de systèmes RAG avancés et modulaires.
