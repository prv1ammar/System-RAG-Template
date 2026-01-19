# BullMQ Integration Guide

## Overview
The platform now uses BullMQ for asynchronous job processing, enabling non-blocking bot generation and testing.

## Architecture
```
Streamlit App (Python) → Redis Queue → BullMQ Worker (Node.js) → Supabase
```

## Prerequisites
1. **Docker Desktop** - For running Redis
2. **Node.js** (v18+) - For BullMQ worker
3. **Python 3.10+** - Already installed

## Quick Start

### 1. Start Services
```bash
# Windows
start-services.bat

# Manual (if script fails)
docker-compose up -d
npm install
npm run worker
```

### 2. Verify Services
- Redis: `docker ps` (should show redis container)
- Worker: Check the BullMQ Worker window for "🚀 BullMQ workers started"

### 3. Run Streamlit
```bash
.\venv\Scripts\streamlit run app.py
```

## Job Types

### Bot Generation (`bot-generation` queue)
- **Input**: Bot ID, configuration
- **Output**: Generated bot files, workflow JSON
- **Progress**: 0% → 10% → 30% → 60% → 100%
- **Retry**: 3 attempts with exponential backoff

### Bot Testing (`bot-test` queue)
- **Input**: Bot ID, test questions
- **Output**: Test results
- **Progress**: Per-question progress
- **Retry**: 2 attempts

## Monitoring

### Check Job Status (Python)
```python
from queue_manager import get_queue_client

client = get_queue_client()
status = client.get_job_status(job_id, 'bot-generation')
print(status)
```

### Redis CLI
```bash
docker exec -it rag-platform-redis redis-cli

# List queues
KEYS bull:*

# Check queue length
ZCARD bull:bot-generation:wait

# View job
HGETALL bull:bot-generation:<job-id>
```

## Configuration

### Environment Variables
Add to `.env`:
```
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Worker Configuration
Edit `worker/bot-worker.js`:
- `concurrency`: Number of parallel jobs
- `limiter`: Rate limiting settings

## Troubleshooting

### Redis Connection Failed
```bash
# Check if Redis is running
docker ps

# Restart Redis
docker-compose restart redis
```

### Worker Not Processing Jobs
```bash
# Check worker logs
# Look for "🚀 BullMQ workers started"

# Restart worker
npm run worker
```

### Job Stuck in Queue
```bash
# Check job status in Supabase
SELECT * FROM job_status WHERE job_id = '<job-id>';

# Manually remove stuck job
docker exec -it rag-platform-redis redis-cli
DEL bull:bot-generation:<job-id>
```

## Production Deployment

### Multiple Workers
```bash
# Terminal 1
npm run worker

# Terminal 2
npm run worker

# Terminal 3
npm run worker
```

### PM2 (Process Manager)
```bash
npm install -g pm2
pm2 start worker/bot-worker.js --name rag-worker -i 3
pm2 save
pm2 startup
```

## Benefits
- ✅ Non-blocking UI (async processing)
- ✅ Automatic retry on failure
- ✅ Progress tracking
- ✅ Horizontal scaling (multiple workers)
- ✅ Job history and monitoring
- ✅ Rate limiting and concurrency control
