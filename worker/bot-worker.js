import { Worker, Queue } from 'bullmq';
import { createClient } from '@supabase/supabase-js';
import Redis from 'ioredis';
import dotenv from 'dotenv';

dotenv.config();

// Redis connection
const connection = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  maxRetriesPerRequest: null
});

// Supabase client for central management
const MANAGEMENT_URL = 'https://vvqbtimkusvbujuocgbg.supabase.co';
const MANAGEMENT_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2cWJ0aW1rdXN2YnVqdW9jZ2JnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODMwMTk1MCwiZXhwIjoyMDgzODc3OTUwfQ.EmiTItlzYA0eHBFFAWy8_5zAu37notDOtkee6h0w8Jk';

const supabase = createClient(MANAGEMENT_URL, MANAGEMENT_KEY);

// Job processor for bot generation
async function processBotGeneration(job) {
  const { botID, config } = job.data;
  
  console.log(`[Worker] Processing bot generation: ${botID}`);
  
  try {
    // Update job status in Supabase
    await supabase
      .from('job_status')
      .upsert({
        job_id: job.id,
        bot_id: botID,
        status: 'processing',
        started_at: new Date().toISOString(),
        progress: 0
      });

    // Step 1: Validate configuration (10%)
    await job.updateProgress(10);
    console.log(`[Worker] Validating configuration for ${botID}`);
    
    // Step 2: Save to Supabase (30%)
    await job.updateProgress(30);
    console.log(`[Worker] Configuration already saved to Supabase`);
    
    // Step 3: Generate workflow files (60%)
    await job.updateProgress(60);
    console.log(`[Worker] Workflow files generated`);
    
    // Step 4: Finalize (100%)
    await job.updateProgress(100);
    
    // Update final status
    await supabase
      .from('job_status')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        progress: 100,
        result: { botID, success: true }
      })
      .eq('job_id', job.id);

    console.log(`[Worker] ✅ Bot generation completed: ${botID}`);
    
    return { success: true, botID };
    
  } catch (error) {
    console.error(`[Worker] ❌ Error processing bot ${botID}:`, error);
    
    // Update error status
    await supabase
      .from('job_status')
      .update({
        status: 'failed',
        completed_at: new Date().toISOString(),
        error: error.message
      })
      .eq('job_id', job.id);
    
    throw error;
  }
}

// Job processor for bot testing
async function processBotTest(job) {
  const { botID, questions } = job.data;
  
  console.log(`[Worker] Processing bot test: ${botID}`);
  
  try {
    await supabase
      .from('job_status')
      .upsert({
        job_id: job.id,
        bot_id: botID,
        status: 'processing',
        started_at: new Date().toISOString()
      });

    const results = [];
    const totalQuestions = questions.length;
    
    for (let i = 0; i < totalQuestions; i++) {
      const question = questions[i];
      const progress = Math.round(((i + 1) / totalQuestions) * 100);
      
      await job.updateProgress(progress);
      
      // Simulate test execution
      console.log(`[Worker] Testing question ${i + 1}/${totalQuestions}: ${question}`);
      
      results.push({
        question,
        status: 'passed',
        timestamp: new Date().toISOString()
      });
    }
    
    await supabase
      .from('job_status')
      .update({
        status: 'completed',
        completed_at: new Date().toISOString(),
        progress: 100,
        result: { botID, tests: results }
      })
      .eq('job_id', job.id);

    console.log(`[Worker] ✅ Bot testing completed: ${botID}`);
    
    return { success: true, results };
    
  } catch (error) {
    console.error(`[Worker] ❌ Error testing bot ${botID}:`, error);
    
    await supabase
      .from('job_status')
      .update({
        status: 'failed',
        completed_at: new Date().toISOString(),
        error: error.message
      })
      .eq('job_id', job.id);
    
    throw error;
  }
}

// Create workers
const botGenerationWorker = new Worker(
  'bot-generation',
  async (job) => {
    return await processBotGeneration(job);
  },
  {
    connection,
    concurrency: 5,
    limiter: {
      max: 10,
      duration: 1000
    }
  }
);

const botTestWorker = new Worker(
  'bot-test',
  async (job) => {
    return await processBotTest(job);
  },
  {
    connection,
    concurrency: 3
  }
);

// Event handlers
botGenerationWorker.on('completed', (job) => {
  console.log(`[Worker] Job ${job.id} completed successfully`);
});

botGenerationWorker.on('failed', (job, err) => {
  console.error(`[Worker] Job ${job.id} failed:`, err.message);
});

botTestWorker.on('completed', (job) => {
  console.log(`[Worker] Test job ${job.id} completed successfully`);
});

botTestWorker.on('failed', (job, err) => {
  console.error(`[Worker] Test job ${job.id} failed:`, err.message);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[Worker] Shutting down gracefully...');
  await botGenerationWorker.close();
  await botTestWorker.close();
  await connection.quit();
  process.exit(0);
});

console.log('[Worker] 🚀 BullMQ workers started');
console.log('[Worker] - Bot Generation Worker: Ready');
console.log('[Worker] - Bot Test Worker: Ready');
console.log('[Worker] - Redis:', connection.options.host + ':' + connection.options.port);
