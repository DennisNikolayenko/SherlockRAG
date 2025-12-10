#!/usr/bin/env python3
"""
Promptfoo wrapper for SherlockRAG
Allows Promptfoo to test the RAG system
"""

import sys
import json
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import load_vector_store, retrieve_context, generate_answer

# Load vector store once (cache it)
_vectorstore = None

def get_vectorstore():
    """Load vectorstore once and cache it"""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = load_vector_store("data/chroma_db")
    return _vectorstore


def query_rag(prompt):
    """
    Query the RAG system
    This is what Promptfoo will call
    """
    vectorstore = get_vectorstore()
    context, sources = retrieve_context(vectorstore, prompt)
    answer = generate_answer(prompt, context, sources)
    return answer


if __name__ == "__main__":
    # Promptfoo sends prompt as command line arg
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        # Or reads from stdin
        prompt = sys.stdin.read().strip()
    
    # Get answer
    answer = query_rag(prompt)
    
    # Return to Promptfoo
    print(answer)