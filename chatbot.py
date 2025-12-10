#!/usr/bin/env python3
"""
Sherlock Holmes RAG Chatbot
Ask questions about the complete Sherlock Holmes canon!
"""

import os                                           # Environment variables
from typing import List                             # Type hints
from dotenv import load_dotenv                      # Load .env file
from langchain_community.embeddings import HuggingFaceEmbeddings  # Embeddings
from langchain_community.vectorstores import Chroma              # Vector DB
import anthropic                                    # Direct Anthropic SDK


# Load environment variables
load_dotenv()


def load_vector_store(persist_directory: str) -> Chroma:
    """
    Load the existing vector store.
    
    Args:
        persist_directory: Path to ChromaDB
        
    Returns:
        Loaded Chroma vector store
    """
    print("📚 Loading Sherlock Holmes knowledge base...")
    
    # Create embeddings (same model as indexing)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load vector store
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="sherlock_holmes"
    )
    
    print("   ✅ Knowledge base loaded (5,039 chunks)")
    
    return vectorstore


def generate_query_variations(query: str, api_key: str) -> List[str]:
    """
    Generate query variations to improve retrieval coverage.
    
    Args:
        query: Original user question
        api_key: Anthropic API key
        
    Returns:
        List of query variations (including original)
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Given this question about Sherlock Holmes stories:
"{query}"

Generate 2 alternative ways to search for this information. Focus on:
- Different phrasings
- Key terms and concepts
- Related story elements

Return ONLY the 2 alternative queries, one per line, no numbering or explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )
    
    variations = message.content[0].text.strip().split('\n')
    variations = [v.strip() for v in variations if v.strip()]
    
    # Return original + variations
    return [query] + variations[:2]


def retrieve_context(vectorstore: Chroma, query: str, k: int = 5) -> tuple:
    """
    Retrieve relevant context for a query using MULTI-QUERY + KEYWORD FALLBACK.
    
    Args:
        vectorstore: ChromaDB vector store
        query: User's question
        k: Number of chunks to retrieve per query
        
    Returns:
        (context_text, source_info)
    """
    # Generate query variations
    api_key = os.getenv("ANTHROPIC_API_KEY")
    query_variations = generate_query_variations(query, api_key)
    
    print(f"\n🔍 Multi-Query Retrieval:")
    print(f"   Original: {query}")
    print(f"   Variations:")
    for i, var in enumerate(query_variations[1:], 1):
        print(f"      {i}. {var}")
    
    # Retrieve with each query variation
    all_results = []
    seen_content = set()  # Avoid duplicates
    
    for q in query_variations:
        results = vectorstore.similarity_search(q, k=8)  # 8 chunks per query variation
        
        for doc in results:
            # Use first 100 chars as unique identifier
            content_id = doc.page_content[:100]
            
            if content_id not in seen_content:
                seen_content.add(content_id)
                all_results.append(doc)
    
    # KEYWORD FALLBACK: Extract key terms and search literally
    query_lower = query.lower()
    keywords = []
    
    # Extract potential keywords from query
    if 'moustache' in query_lower or 'mustache' in query_lower:
        keywords.append('moustache')  # Search for British spelling (in the text)
    if 'watson' in query_lower:
        keywords.append('watson')
        
        # Detect wound/injury queries and add anatomical terms
        if any(word in query_lower for word in ['wound', 'injury', 'injured', 'shot', 'hurt']):
            keywords.extend(['shoulder', 'jezail', 'leg', 'bullet', 'struck'])
            print(f"   🔍 Detected wound query - adding anatomical terms")
    if 'red circle' in query_lower:
        keywords.append('red circle')
    if 'red-headed league' in query_lower or 'red headed league' in query_lower:
        keywords.append('red-headed league')
    if 'tobacco' in query_lower:
        keywords.append('tobacco')
    if 'shoulder' in query_lower or 'wound' in query_lower:
        # For wound questions, search for anatomical terms
        if 'watson' in query_lower:
            keywords.extend(['shoulder', 'jezail'])
    
    # If we have keywords, do literal text search
    if len(keywords) >= 1:  # Trigger if we have ANY keywords
        print(f"   🔑 Keyword fallback: searching for {keywords}")
        
        # Get ALL documents and filter by keywords
        collection = vectorstore._collection
        all_docs = collection.get(include=['documents', 'metadatas'])
        
        keyword_matches = 0
        
        for i, (doc_text, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
            doc_text_lower = doc_text.lower()
            
            # Check if ALL keywords appear in document
            if all(keyword.lower() in doc_text_lower for keyword in keywords):
                content_id = doc_text[:100]
                
                if content_id not in seen_content:
                    seen_content.add(content_id)
                    
                    # Create Document object
                    from langchain.docstore.document import Document
                    doc = Document(page_content=doc_text, metadata=metadata)
                    all_results.insert(0, doc)  # Add to FRONT (high priority!)
                    keyword_matches += 1
                    
                    title = metadata.get('title', 'Unknown')
                    print(f"      ✅ Keyword match #{keyword_matches}: {title}")
                    
                    # Limit keyword matches to avoid flooding
                    if keyword_matches >= 5:
                        break
        
        if keyword_matches == 0:
            print(f"      ⚠️  No exact keyword matches found")
    
    print(f"   📚 Retrieved {len(all_results)} unique chunks\n")
    
    # Combine chunks into context (take top results)
    context_parts = []
    sources = []
    
    for i, doc in enumerate(all_results[:15], 1):  # Limit to 15 best chunks
        title = doc.metadata.get('title', 'Unknown Story')
        content = doc.page_content
        
        context_parts.append(f"[Source {i} - {title}]\n{content}")
        
        # Track unique sources
        if title not in sources:
            sources.append(title)
    
    context_text = "\n\n".join(context_parts)
    
    return context_text, sources


def generate_answer(query: str, context: str, sources: List[str]) -> str:
    """
    Generate answer using Claude with retrieved context.
    
    Args:
        query: User's question
        context: Retrieved context from stories
        sources: List of source story titles
        
    Returns:
        Claude's answer
    """
    # Initialize Anthropic client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    
    # Create prompt
    system_prompt = """You are an expert on Sherlock Holmes stories by Arthur Conan Doyle. 
Answer questions based on the provided context from the actual stories.

Guidelines:
- Answer directly and conversationally
- Reference specific stories when relevant
- If the context doesn't contain the answer, say so honestly
- Be engaging and show knowledge of the Holmes canon
- Keep answers concise (2-4 paragraphs max)"""

    user_prompt = f"""Context from Sherlock Holmes stories:

{context}

Question: {query}

Answer based on the context above:"""

    # Generate response
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        temperature=0.5,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return message.content[0].text


def format_sources(sources: List[str]) -> str:
    """Format source list for display."""
    if not sources:
        return ""
    
    source_text = "\n📚 Sources:\n"
    for i, source in enumerate(sources, 1):
        source_text += f"   {i}. {source}\n"
    
    return source_text


def chat_loop(vectorstore: Chroma):
    """
    Interactive chat loop.
    
    Args:
        vectorstore: ChromaDB vector store
    """
    print("\n" + "=" * 70)
    print("🔍 SHERLOCKRAG - Ask me anything about Sherlock Holmes!")
    print("=" * 70)
    print("\nExamples:")
    print("  • What is Sherlock Holmes's address?")
    print("  • Tell me about The Hound of the Baskervilles")
    print("  • Who is Professor Moriarty?")
    print("  • What is Holmes's relationship with Watson?")
    print("\nType 'quit' or 'exit' to stop")
    print("=" * 70 + "\n")
    
    while True:
        # Get user question
        query = input("❓ Your question: ").strip()
        
        if not query:
            continue
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Elementary, my dear Watson! Goodbye!")
            break
        
        print("\n🔍 Searching the canon...")
        
        try:
            # Retrieve context (multi-query will generate variations)
            context, sources = retrieve_context(vectorstore, query, k=5)
            
            print(f"   Found relevant passages from {len(sources)} stories")
            print("\n💭 Generating answer...\n")
            
            # Generate answer
            answer = generate_answer(query, context, sources)
            
            # Display answer
            print("📖 Answer:")
            print("-" * 70)
            print(answer)
            print("-" * 70)
            
            # Display sources
            print(format_sources(sources))
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")


def demo_mode(vectorstore: Chroma):
    """
    Demo mode with pre-set questions (no API key needed for viewing).
    
    Args:
        vectorstore: ChromaDB vector store
    """
    print("\n" + "=" * 70)
    print("🔍 SHERLOCKRAG - DEMO MODE (Retrieval Only)")
    print("=" * 70)
    print("\nShowing retrieval results for sample questions...")
    print("(Set ANTHROPIC_API_KEY to enable full answers)\n")
    
    demo_questions = [
        "What is Sherlock Holmes's address?",
        "Who is Professor Moriarty?",
        "Tell me about The Hound of the Baskervilles"
    ]
    
    for i, query in enumerate(demo_questions, 1):
        print(f"\n📝 Question {i}: {query}")
        print("-" * 70)
        
        context, sources = retrieve_context(vectorstore, query, k=3)
        
        print(f"✅ Found relevant passages from: {', '.join(sources)}")
        
        # Show first chunk preview
        results = vectorstore.similarity_search(query, k=1)
        if results:
            preview = results[0].page_content[:200].replace('\n', ' ')
            print(f"\n📖 Preview: \"{preview}...\"")
        
        print()


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("🔍 SHERLOCKRAG")
    print("=" * 70)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("\n⚠️  No ANTHROPIC_API_KEY found in environment")
        print("   Running in DEMO MODE (retrieval only)\n")
        print("   To enable full chatbot:")
        print("   1. Create .env file in SherlockRAG folder")
        print("   2. Add: ANTHROPIC_API_KEY=your-key-here")
        print("   3. Run again\n")
    
    # Load vector store
    persist_directory = "data/chroma_db"
    
    if not os.path.exists(persist_directory):
        print(f"\n❌ Error: Vector store not found at {persist_directory}")
        print("   Please run build_index.py first!")
        return
    
    vectorstore = load_vector_store(persist_directory)
    
    # Run appropriate mode
    if api_key:
        chat_loop(vectorstore)
    else:
        demo_mode(vectorstore)


if __name__ == "__main__":
    main()