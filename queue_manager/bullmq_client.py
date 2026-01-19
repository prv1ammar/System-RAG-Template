import redis
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class BullMQClient:
    """Python client for enqueuing jobs to BullMQ"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
    def enqueue_bot_generation(self, bot_id: str, config: Dict[str, Any]) -> str:
        """
        Enqueue a bot generation job
        
        Args:
            bot_id: Unique bot identifier
            config: Bot configuration dictionary
            
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        queue_name = 'bull:bot-generation'
        
        job_data = {
            'id': job_id,
            'name': 'generate-bot',
            'data': {
                'botID': bot_id,
                'config': config
            },
            'opts': {
                'attempts': 3,
                'backoff': {
                    'type': 'exponential',
                    'delay': 2000
                },
                'removeOnComplete': False,
                'removeOnFail': False
            },
            'timestamp': int(datetime.now().timestamp() * 1000),
            'delay': 0,
            'priority': 0
        }
        
        # Add job to queue
        self.redis_client.zadd(f'{queue_name}:wait', {job_id: int(datetime.now().timestamp() * 1000)})
        self.redis_client.hset(f'{queue_name}:{job_id}', mapping={
            'data': json.dumps(job_data['data']),
            'opts': json.dumps(job_data['opts']),
            'name': job_data['name'],
            'timestamp': job_data['timestamp']
        })
        
        # Publish event
        self.redis_client.publish(f'{queue_name}:added', job_id)
        
        return job_id
    
    def enqueue_bot_test(self, bot_id: str, questions: list) -> str:
        """
        Enqueue a bot testing job
        
        Args:
            bot_id: Bot identifier to test
            questions: List of test questions
            
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        queue_name = 'bull:bot-test'
        
        job_data = {
            'id': job_id,
            'name': 'test-bot',
            'data': {
                'botID': bot_id,
                'questions': questions
            },
            'opts': {
                'attempts': 2,
                'removeOnComplete': True
            },
            'timestamp': int(datetime.now().timestamp() * 1000)
        }
        
        self.redis_client.zadd(f'{queue_name}:wait', {job_id: int(datetime.now().timestamp() * 1000)})
        self.redis_client.hset(f'{queue_name}:{job_id}', mapping={
            'data': json.dumps(job_data['data']),
            'opts': json.dumps(job_data['opts']),
            'name': job_data['name'],
            'timestamp': job_data['timestamp']
        })
        
        self.redis_client.publish(f'{queue_name}:added', job_id)
        
        return job_id
    
    def get_job_status(self, job_id: str, queue_name: str = 'bot-generation') -> Optional[Dict]:
        """
        Get the status of a job
        
        Args:
            job_id: Job identifier
            queue_name: Queue name (without 'bull:' prefix)
            
        Returns:
            Job status dictionary or None
        """
        full_queue = f'bull:{queue_name}'
        job_data = self.redis_client.hgetall(f'{full_queue}:{job_id}')
        
        if not job_data:
            return None
            
        return {
            'id': job_id,
            'name': job_data.get('name'),
            'data': json.loads(job_data.get('data', '{}')),
            'progress': job_data.get('progress', 0),
            'returnvalue': job_data.get('returnvalue')
        }
    
    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            return self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            return False

# Singleton instance
_client = None

def get_queue_client():
    """Get or create BullMQ client instance"""
    global _client
    if _client is None:
        _client = BullMQClient()
    return _client
