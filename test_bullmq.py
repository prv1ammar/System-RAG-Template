from queue_manager import get_queue_client
import time

def test_bullmq_integration():
    """Test BullMQ integration"""
    print("Testing BullMQ Integration...")
    print("=" * 50)
    
    # Test Redis connection
    print("\n1. Testing Redis connection...")
    client = get_queue_client()
    
    if client.test_connection():
        print("   ✅ Redis connection successful")
    else:
        print("   ❌ Redis connection failed")
        print("   Make sure Redis is running: docker-compose up -d")
        return
    
    # Enqueue a test job
    print("\n2. Enqueuing test bot generation job...")
    test_config = {
        'PROJECT_NAME': 'test_bot',
        'SUPABASE_URL': 'https://example.supabase.co',
        'NAME_TABLE': 'documents'
    }
    
    job_id = client.enqueue_bot_generation('test-bot-123', test_config)
    print(f"   ✅ Job enqueued: {job_id}")
    
    # Check job status
    print("\n3. Checking job status...")
    time.sleep(2)  # Wait for worker to pick up job
    
    status = client.get_job_status(job_id)
    if status:
        print(f"   ✅ Job found in queue")
        print(f"   - Name: {status.get('name')}")
        print(f"   - Progress: {status.get('progress', 0)}%")
    else:
        print(f"   ⚠️  Job not found (may have completed)")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNext steps:")
    print("1. Check the BullMQ Worker window for processing logs")
    print("2. Check Supabase job_status table for results")
    print("3. Use Redis CLI to inspect queues: docker exec -it rag-platform-redis redis-cli")

if __name__ == "__main__":
    test_bullmq_integration()
