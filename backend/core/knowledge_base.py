import chromadb
import ollama
import os
import datetime

# Separate ChromaDB collection for astrology knowledge
chroma_client = chromadb.PersistentClient(path='data/chroma_db')
knowledge_collection = chroma_client.get_or_create_collection('astro_knowledge')

def embed_text(text):
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']

def chunk_text(text, chunk_size=1000, overlap=200):
    """Chunks text into overlapping parts."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def index_all_knowledge():
    # Global keyword to modify the module-level collection
    global knowledge_collection
    
    # Clear or get collection
    try:
        chroma_client.delete_collection('astro_knowledge')
    except:
        pass
    knowledge_collection = chroma_client.create_collection('astro_knowledge')
    
    knowledge_dir = 'knowledge'
    print(f"-> Starting indexing of all knowledge from '{knowledge_dir}'...")
    
    total_chunks = 0
    for filename in os.listdir(knowledge_dir):
        if not filename.endswith('.txt'):
            continue
            
        filepath = os.path.join(knowledge_dir, filename)
        print(f"   Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
            
            # For small files, we can chunk by paragraph
            if len(text) < 5000:
                chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 10]
            else:
                # For large files like BPHS, use fixed size chunks
                chunks = chunk_text(text)
            
            all_ids = []
            all_embeddings = []
            all_docs = []
            all_metas = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip(): continue
                
                emb = embed_text(chunk)
                all_ids.append(f"kb_{filename}_{i}_{datetime.datetime.now().timestamp()}")
                all_embeddings.append(emb)
                all_docs.append(chunk)
                all_metas.append({'source': filename, 'chunk': i})
                
                # Add in batches of 100 to avoid issues
                if len(all_ids) >= 100:
                    knowledge_collection.add(
                        ids=all_ids,
                        embeddings=all_embeddings,
                        documents=all_docs,
                        metadatas=all_metas
                    )
                    total_chunks += len(all_ids)
                    all_ids, all_embeddings, all_docs, all_metas = [], [], [], []
            
            if all_ids:
                knowledge_collection.add(
                    ids=all_ids,
                    embeddings=all_embeddings,
                    documents=all_docs,
                    metadatas=all_metas
                )
                total_chunks += len(all_ids)
                
    print(f"✅ Successfully indexed {total_chunks} knowledge chunks into 'astro_knowledge' collection.")

def search_knowledge(query, n_results=4):
    """Searches the astrology knowledge base for relevant chunks."""
    query_embedding = embed_text(query)
    results = knowledge_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results['documents'][0] if results['documents'] else []

if __name__ == '__main__':
    index_all_knowledge()
