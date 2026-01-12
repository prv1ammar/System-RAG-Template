import { Worker, Job } from 'bullmq';
import IORedis from 'ioredis';
import * as dotenv from 'dotenv';
import { processIngestion } from './processors/ingestion';
import { processDeletion } from './processors/deletion';
import { processReEmbedding } from './processors/re_embed';

dotenv.config({ path: '../.env' });

const REDIS_HOST = process.env.REDIS_HOST || 'localhost';
const REDIS_PORT = parseInt(process.env.REDIS_PORT || '6379');

const connection = new IORedis({
    host: REDIS_HOST,
    port: REDIS_PORT,
    maxRetriesPerRequest: null,
});

console.log(`🚀 Worker starting... Connecting to Redis at ${REDIS_HOST}:${REDIS_PORT}`);

const worker = new Worker(
    'rag-tasks',
    async (job: Job) => {
        console.log(`[Job ${job.id}] Processing ${job.name} for bot ${job.data.bot_id}`);

        try {
            switch (job.name) {
                case 'INGEST_DOCUMENT':
                    return await processIngestion(job.data);
                case 'DELETE_BOT':
                    return await processDeletion(job.data);
                case 'RE_EMBED_BOT':
                    return await processReEmbedding(job.data);
                default:
                    throw new Error(`Unsupported job type: ${job.name}`);
            }
        } catch (error) {
            console.error(`[Job ${job.id}] Failed:`, error);
            throw error;
        }
    },
    {
        connection,
        concurrency: 5 // Process 5 jobs in parallel
    }
);

worker.on('completed', (job) => {
    console.log(`[Job ${job.id}] Completed successfully`);
});

worker.on('failed', (job, err) => {
    console.error(`[Job ${job?.id}] Failed with error: ${err.message}`);
});
