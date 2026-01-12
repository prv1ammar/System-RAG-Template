import json
import uuid
import time
import os
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

# Configuration Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Connexion Redis unique
redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def enqueue_rag_job(job_name: str, payload: dict, queue_name: str = "rag-tasks"):
    """
    Injecte un job dans Redis au format BullMQ.
    """
    job_id = str(uuid.uuid4())
    
    # Structure de données attendue par BullMQ
    job_data = {
        "name": job_name,
        "data": payload,
        "opts": {
            "attempts": 3,
            "backoff": {"type": "exponential", "delay": 2000},
            "removeOnComplete": True,
            "removeOnFail": False
        },
        "timestamp": int(time.time() * 1000),
        "stacktrace": [],
        "returnvalue": None,
        "parent": None,
        "progress": 0
    }
    
    # 1. Stocker les données du job
    redis_conn.set(f"bull:{queue_name}:{job_id}", json.dumps(job_data))
    
    # 2. Ajouter l'ID à la liste d'attente (wait list)
    redis_conn.lpush(f"bull:{queue_name}:wait", job_id)
    
    # 3. Signaler via un évènement pour les workers bloqués sur le 'wait'
    redis_conn.publish(f"bull:{queue_name}:id", job_id)
    
    print(f"[Queue] Job {job_id} ({job_name}) enqueued for bot {payload.get('bot_id')}")
    return job_id

def get_job_status(job_id: str, queue_name: str = "rag-tasks"):
    """
    Récupère le statut brut d'un job dans Redis.
    """
    data = redis_conn.get(f"bull:{queue_name}:{job_id}")
    if not data:
        return "not_found"
    return json.loads(data)
