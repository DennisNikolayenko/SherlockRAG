===================================================
        CORE COMPONENTS OF A RAG SYSTEM
                   (Text / Query Flow)
===================================================

A Retrieval-Augmented Generation (RAG) system works
through two major phases: INGESTION and EXECUTION.


===================================================
                 PHASE 1: INGESTION
                   (Indexing Data)
===================================================

[1] LOADER / DOCUMENT LOADER
---------------------------------------
Function : Connects to data sources (PDFs, APIs,
           databases) and extracts raw content.
Output   : Raw text documents + metadata.


[2] SPLITTER / TEXT SPLITTER
---------------------------------------
Function : Breaks large documents into smaller,
           meaningful chunks for retrieval.
Output   : Small, indexed text chunks.


[3] EMBEDDINGS MODEL / GENERATOR
---------------------------------------
Function : Converts text chunks into dense numerical
           vectors that capture semantic meaning.
Output   : Vector embeddings ("memory" of the system).


[4] VECTOR STORE / VECTOR DATABASE
---------------------------------------
Function : Stores and indexes embeddings for fast
           similarity search.
Output   : Searchable vector-based knowledge base.


===================================================
                PHASE 2: EXECUTION
                (Query & Answering)
===================================================

[1] USER QUERY / INPUT
---------------------------------------
Function : The user's natural language question.


[2] QUERY ENCODER
---------------------------------------
Function : Uses the same embeddings model to convert
           the user query into a query vector.


[3] RETRIEVER
---------------------------------------
Function : Searches the Vector Store for the top 'k'
           most relevant chunks (cosine similarity, etc.).
Output   : Top 'k' relevant passages/documents.


[4] RE-RANKER (Optional, Recommended)
---------------------------------------
Function : Re-scores retrieved chunks to ensure the
           most contextually relevant pieces are kept.
Output   : Optimized, high-quality context set.


[5] CONTEXT BUILDER / PROMPT BUILDER
---------------------------------------
Function : Assembles the final prompt for the LLM:
           - User question
           - Retrieved context
           - System instructions


[6] LLM / GENERATOR (Large Language Model)
---------------------------------------
Function : Generates a grounded answer using the
           provided context + user question.
Output   : Final answer.


[7] CITATION GENERATOR
---------------------------------------
Function : Pulls metadata from the source chunks and
           adds citations to the final answer.


===================================================
