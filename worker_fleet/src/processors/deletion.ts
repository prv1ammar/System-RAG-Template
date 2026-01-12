import { createClient } from "@supabase/supabase-js";

export async function processDeletion(data: { bot_id: string }) {
    const { bot_id } = data;

    console.log(`[Deletion] Starting mass deletion for bot: ${bot_id}`);

    const supabaseClient = createClient(
        process.env.SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_KEY!
    );

    const tableName = process.env.NAME_TABLE || "documents";

    // 1. Delete all document chunks associated with this bot
    const { error: chunkError, count } = await supabaseClient
        .from(tableName)
        .delete({ count: 'exact' })
        .eq('bot_id', bot_id);

    if (chunkError) {
        throw new Error(`Failed to delete chunks: ${chunkError.message}`);
    }

    // 2. Delete the bot metadata record
    const { error: botError } = await supabaseClient
        .from('bots')
        .delete()
        .eq('id', bot_id);

    if (botError) {
        throw new Error(`Failed to delete bot record: ${botError.message}`);
    }

    console.log(`[Deletion] Successfully deleted bot ${bot_id} and ${count || 0} chunks.`);

    return {
        status: 'success',
        bot_id,
        deleted_chunks: count
    };
}
