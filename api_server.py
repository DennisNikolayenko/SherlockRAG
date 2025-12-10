#!/usr/bin/env python3
"""
Simple Flask API for SherlockRAG
Allows Promptfoo to test via HTTP endpoint
"""

from flask import Flask, request, jsonify
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import load_vector_store, retrieve_context, generate_answer

app = Flask(__name__)

# Load vector store once at startup
print("Loading vector store...")
vectorstore = load_vector_store("data/chroma_db")
print("✅ Ready!")


@app.route('/query', methods=['POST'])
def query():
    """
    Endpoint for Promptfoo to call
    Expects JSON: {"prompt": "your question"}
    Returns JSON: {"answer": "response"}
    """
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        # Query RAG
        context, sources = retrieve_context(vectorstore, prompt)
        answer = generate_answer(prompt, context, sources)
        
        return jsonify({
            "answer": answer,
            "sources": sources
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    # Run on localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=False)