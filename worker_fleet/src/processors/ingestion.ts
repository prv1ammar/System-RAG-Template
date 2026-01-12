import { OpenAIEmbeddings } from "@langchain/openai";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { SupabaseVectorStore } from "@langchain/community/vectorstores/supabase";
import { createClient } from "@supabase/supabase-js";
import { TextLoader } from "langchain/document_loaders/fs/text";
import { PDFLoader } from "langchain/document_loaders/fs/pdf";
// Note: Depending on file type, different loaders might be needed
import * as fs from 'fs';
import * as path from 'path';

export async function processIngestion(data: {
    bot_id: string,
    file_path: string,
    document_id: string
}) {
    const { bot_id, file_path, document_id } = data;

    if (!fs.existsSync(file_path)) {
        throw new Error(`File not found: ${file_path}`);
    }

    // 1. Initialize LangChain Components
    const embeddings = new OpenAIEmbeddings({
        openAIApiKey: process.env.OPENAI_API_KEY,
        modelName: process.env.EMBEDDING_MODEL || "text-embedding-3-small",
    });

    const supabaseClient = createClient(
        process.env.SUPABASE_URL!,
        process.env.SUPABASE_SERVICE_KEY!
    );

    // 2. Load and Split Document
    let loader;
    const ext = path.extname(file_path).toLowerCase();

    if (ext === '.pdf') {
        loader = new PDFLoader(file_path);
    } else {
        loader = new TextLoader(file_path);
    }

    const rawDocs = await loader.load();

    const textSplitter = new RecursiveCharacterTextSplitter({
        chunkSize: 1000,
        chunkOverlap: 200,
    });

    // Assign metadata to all chunks
    const docs = await textSplitter.splitDocuments(rawDocs);
    const docsWithMetadata = docs.map(doc => ({
        ...doc,
        metadata: {
            ...doc.metadata,
            bot_id: bot_id,
            document_id: document_id,
            ingested_at: new Date().toISOString(),
        }
    }));

    // 3. Generate Embeddings & Store in Supabase
    console.log(`[Ingestion] Generating embeddings for ${docsWithMetadata.length} chunks...`);

    await SupabaseVectorStore.fromDocuments(
        docsWithMetadata,
        embeddings,
        {
            client: supabaseClient,
            tableName: process.env.NAME_TABLE || "documents",
            queryName: process.env.QUERY_NAME || "match_documents",
        }
    );

    // Cleanup: Remote temp file after success
    try {
        fs.unlinkSync(file_path);
        console.log(`[Ingestion] Cleaned up temp file: ${file_path}`);
    } catch (e) {
        console.warn(`[Ingestion] Could not delete temp file: ${e}`);
    }

    return {
        status: 'success',
        chunks: docsWithMetadata.length,
        bot_id,
        document_id
    };
}
