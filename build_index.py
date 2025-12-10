#!/usr/bin/env python3
"""
Build Sherlock Holmes RAG Index
Chunks stories, creates embeddings, stores in ChromaDB
"""

import os                                      # File operations
import json                                    # Load metadata
from typing import List, Dict                  # Type hints
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Smart chunking
from langchain_community.embeddings import HuggingFaceEmbeddings    # Create embeddings
from langchain_community.vectorstores import Chroma                 # Vector database
from langchain.docstore.document import Document                    # Document structure


def load_stories(stories_dir: str, metadata_file: str) -> List[Document]:
    """
    Load all stories and create LangChain Documents with metadata.
    
    Args:
        stories_dir: Directory containing story text files
        metadata_file: JSON file with story metadata
        
    Returns:
        List of Document objects
    """
    print("📚 Loading Sherlock Holmes stories...")
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        stories_metadata = json.load(f)
    
    documents = []
    
    for story_meta in stories_metadata:
        filename = story_meta['filename']
        filepath = os.path.join(stories_dir, filename)
        
        # Read story text
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Create Document with metadata
            doc = Document(
                page_content=text,
                metadata={
                    'title': story_meta['title'],
                    'filename': filename,
                    'year': story_meta['year'],
                    'type': story_meta['type'],
                    'collection': story_meta['collection'],
                    'word_count': story_meta['word_count'],
                    'story_id': story_meta['id']
                }
            )
            
            documents.append(doc)
            
        except Exception as e:
            print(f"   ⚠️  Error loading {filename}: {e}")
    
    print(f"   ✅ Loaded {len(documents)} stories")
    return documents


def chunk_documents(documents: List[Document], 
                    chunk_size: int = 1000, 
                    chunk_overlap: int = 200) -> List[Document]:
    """
    Split documents into smaller chunks for better retrieval.
    
    Args:
        documents: List of story documents
        chunk_size: Target size of each chunk (characters)
        chunk_overlap: Overlap between chunks (for context)
        
    Returns:
        List of chunked documents
    """
    print(f"\n✂️  Chunking stories...")
    print(f"   Chunk size: {chunk_size} characters")
    print(f"   Overlap: {chunk_overlap} characters")
    
    # Create text splitter optimized for narrative text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n\n",      # Story/chapter breaks
            "\n\n",        # Paragraph breaks  
            "\n",          # Line breaks
            ". ",          # Sentences
            " ",           # Words
            ""             # Characters (fallback)
        ],
        length_function=len,
    )
    
    # Split each document and preserve metadata
    all_chunks = []
    
    for doc in documents:
        chunks = text_splitter.split_documents([doc])
        
        # Add chunk index to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_index'] = i
            chunk.metadata['total_chunks'] = len(chunks)
        
        all_chunks.extend(chunks)
    
    print(f"   ✅ Created {len(all_chunks)} chunks from {len(documents)} stories")
    print(f"   📊 Avg {len(all_chunks) // len(documents)} chunks per story")
    
    return all_chunks


def create_embeddings() -> HuggingFaceEmbeddings:
    """
    Create embedding model (converts text to vectors for semantic search).
    
    Returns:
        HuggingFace embeddings model
    """
    print(f"\n🧠 Loading embedding model...")
    print(f"   Model: all-MiniLM-L6-v2 (384 dimensions)")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},  # Use CPU (faster setup, works everywhere)
        encode_kwargs={'normalize_embeddings': True}  # Better similarity scores
    )
    
    print(f"   ✅ Embedding model loaded")
    
    return embeddings


def build_vector_store(chunks: List[Document], 
                       embeddings: HuggingFaceEmbeddings,
                       persist_directory: str) -> Chroma:
    """
    Create ChromaDB vector store from chunks.
    
    Args:
        chunks: List of document chunks
        embeddings: Embedding model
        persist_directory: Where to save the database
        
    Returns:
        Chroma vector store
    """
    print(f"\n💾 Building vector database...")
    print(f"   Location: {persist_directory}")
    print(f"   This will take 2-3 minutes...")
    
    # Create or load vector store
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="sherlock_holmes"
    )
    
    print(f"   ✅ Vector database created!")
    print(f"   📊 {len(chunks)} chunks indexed")
    
    return vectorstore


def test_retrieval(vectorstore: Chroma, test_queries: List[str], k: int = 3):
    """
    Test the retrieval system with sample queries.
    
    Args:
        vectorstore: ChromaDB vector store
        test_queries: List of test questions
        k: Number of results to retrieve
    """
    print(f"\n🔍 Testing retrieval with sample queries...")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: \"{query}\"")
        
        # Retrieve relevant chunks
        results = vectorstore.similarity_search(query, k=k)
        
        print(f"   Found {len(results)} relevant chunks:\n")
        
        for j, doc in enumerate(results, 1):
            title = doc.metadata.get('title', 'Unknown')
            chunk_idx = doc.metadata.get('chunk_index', '?')
            total_chunks = doc.metadata.get('total_chunks', '?')
            
            # Show first 150 characters of content
            preview = doc.page_content[:150].replace('\n', ' ')
            
            print(f"   {j}. {title} (chunk {chunk_idx}/{total_chunks})")
            print(f"      \"{preview}...\"")
        
        print()
    
    print("=" * 70)


def print_statistics(vectorstore: Chroma):
    """Print database statistics."""
    print(f"\n📊 Index Statistics:")
    print("=" * 70)
    
    # Get collection
    collection = vectorstore._collection
    count = collection.count()
    
    print(f"   Total chunks indexed: {count}")
    print(f"   Embedding dimensions: 384")
    print(f"   Database: ChromaDB (persistent)")
    print(f"   Search: Semantic similarity (cosine)")
    
    print("=" * 70)


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("🔍 SHERLOCK HOLMES RAG - INDEX BUILDER")
    print("=" * 70)
    
    # Paths
    stories_dir = "data/processed/stories"
    metadata_file = "data/processed/stories_metadata.json"
    persist_directory = "data/chroma_db"
    
    # Check inputs exist
    if not os.path.exists(stories_dir):
        print(f"\n❌ Error: Stories directory not found: {stories_dir}")
        return
    
    if not os.path.exists(metadata_file):
        print(f"\n❌ Error: Metadata file not found: {metadata_file}")
        return
    
    # Step 1: Load stories
    documents = load_stories(stories_dir, metadata_file)
    
    if not documents:
        print("\n❌ No documents loaded!")
        return
    
    # Step 2: Chunk documents
    chunks = chunk_documents(documents, chunk_size=1000, chunk_overlap=200)
    
    # Step 3: Create embeddings
    embeddings = create_embeddings()
    
    # Step 4: Build vector store
    vectorstore = build_vector_store(chunks, embeddings, persist_directory)
    
    # Step 5: Test retrieval
    test_queries = [
        "What is Sherlock Holmes's address?",
        "Who is Dr. Watson?",
        "Tell me about the Hound of the Baskervilles"
    ]
    
    test_retrieval(vectorstore, test_queries, k=3)
    
    # Print statistics
    print_statistics(vectorstore)
    
    print(f"\n🎉 SUCCESS!")
    print(f"   📁 Index saved to: {persist_directory}")
    print(f"   🔜 Next: Run chatbot.py to query the system!")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()