-- Final Type-Safe Version
create or replace function match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  p_document_id text default null
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
    -- Cast both to text for a safe comparison regardless of underlying column type (bigint, uuid, etc)
    and (p_document_id is null or documents."documentId"::text = p_document_id)
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
