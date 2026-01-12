import { createClient } from "@supabase/supabase-js";
import { OpenAIEmbeddings } from "@langchain/openai";

export async function processReEmbedding(data: { bot_id: string }) {
    const { bot_id } = data;

    console.log(`[Re-Embedding] Starting re-index for bot: ${bot_id}`);

    const supabaseClient = createClient(
        process.env.SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_KEY!
    );

    const tableName = process.env.NAME_TABLE || "documents";

    // 1. Fetch all documents (text only) for this bot
    const { data: documents, error: fetchError } = await supabaseClient
        .from(tableName)
        .select('id, content, page_content, text')
        .eq('bot_id', bot_id);

    if (fetchError) throw new Error(`Fetch failed: ${fetchError.message}`);
    if (!documents || documents.length === 0) {
        return { status: 'success', message: 'No documents found to re-embed.' };
    }

    const embeddings = new OpenAIEmbeddings({
        openAIApiKey: process.env.OPENAI_API_KEY,
        modelName: process.env.EMBEDDING_MODEL || "text-embedding-3-small",
    });

    console.log(`[Re-Embedding] Generating new vectors for ${documents.length} chunks...`);

    // 2. Process in batches to avoid API limits
    for (const doc of documents) {
        const text = doc.content || doc.page_content || doc.text;
        if (!text) continue;

        const [newVector] = await embeddings.embedDocuments([text]);

        const { error: updateError } = await supabaseClient
            .from(tableName)
            .update({ embedding: newVector })
            .eq('id', doc.id);

        if (updateError) console.error(`Failed to update doc ${doc.id}: ${updateError.message}`);
    }

    console.log(`[Re-Embedding] Completed for bot ${bot_id}`);

    return {
        status: 'success',
        bot_id,
        processed_chunks: documents.length
    };
}
