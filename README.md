# SherlockRAG 🔍

A production-ready Retrieval-Augmented Generation (RAG) system for the complete Sherlock Holmes canon by Arthur Conan Doyle.

**Performance:** 81.3% overall accuracy across 50 comprehensive test questions

## 🎯 Project Overview

SherlockRAG demonstrates professional RAG system development, comprehensive evaluation methodology, and security testing. Built as a portfolio project to showcase AI engineering and QA skills.

### Key Features

- **Hybrid Retrieval:** Multi-query semantic search + keyword fallback
- **Comprehensive Evaluation:** 50-question test suite across 8 failure categories
- **Security Testing:** Red team evaluation with 11 attack vectors
- **Production Architecture:** Flask API wrapper for easy integration
- **Systematic Debugging:** Documented case studies of retrieval optimization

## 📊 Performance Metrics

| Metric | Score | Status |
|--------|-------|--------|
| **Overall** | **81.3%** | ✅ Production-ready |
| Retrieval | 88.0% | ✅ Strong |
| Relevance | 77.1% | ✅ Good |
| Faithfulness | 83.8% | ✅ Strong |
| Correctness | 76.2% | ✅ Good |

### By Category

| Category | Score | Description |
|----------|-------|-------------|
| Negative Queries | 93.8% | Handles anachronistic/absent info |
| Happy Path | 88.8% | Common questions |
| Similar Names | 83.8% | Disambiguation |
| Needle in Haystack | 79.5% | Specific rare facts |
| Adversarial | 75.0% | Prompt injection resistance |
| Contradiction | 74.1% | Handles Doyle inconsistencies |
| Chunk Boundary | 64.2% | Long document details |
| Multi-Hop | 45.4% | Cross-document synthesis |

**See:** [EVALUATION_REPORT.md](EVALUATION_REPORT.md) for detailed analysis

## 🏗️ Architecture

```
User Query
    ↓
┌─────────────────────────────────┐
│  Hybrid Retrieval System        │
│  ┌──────────────────────────┐  │
│  │ 1. Multi-Query Generation│  │  Generate 3 query variations
│  │    (Claude API)          │  │  with Claude
│  └──────────────────────────┘  │
│             ↓                   │
│  ┌──────────────────────────┐  │
│  │ 2. Semantic Search       │  │  Vector similarity search
│  │    (ChromaDB)            │  │  15 chunks × 3 queries
│  └──────────────────────────┘  │
│             ↓                   │
│  ┌──────────────────────────┐  │
│  │ 3. Keyword Fallback      │  │  Exact term matching for
│  │    (Pattern Matching)    │  │  proper nouns & specifics
│  └──────────────────────────┘  │
│             ↓                   │
│  ┌──────────────────────────┐  │
│  │ 4. Deduplication         │  │  ~20-30 unique chunks
│  └──────────────────────────┘  │
└─────────────────────────────────┘
    ↓
Retrieved Context (20-30 chunks)
    ↓
┌─────────────────────────────────┐
│  Answer Generation               │
│  (Claude Sonnet 4, temp=0.5)    │
└─────────────────────────────────┘
    ↓
Answer + Source Citations
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- API key from Anthropic (Claude)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/SherlockRAG.git
cd SherlockRAG

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Build the Knowledge Base

```bash
# Parse stories and build vector database
python3 parse_stories.py
python3 build_index.py

# This creates:
# - data/processed/stories/ (61 story files)
# - data/chroma_db/ (vector database with 5,039 chunks)
```

### Run the Chatbot

```bash
# Interactive Q&A
python3 chatbot.py

# Example queries:
# - "What is Holmes's address?"
# - "Did Watson have a moustache?"
# - "Tell me about The Hound of the Baskervilles"
```

### Run as API (Optional)

```bash
# Start Flask API server
python3 api_server.py

# In another terminal, query the API:
curl -X POST http://127.0.0.1:5000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Who is Professor Moriarty?"}'
```

## 🧪 Testing & Evaluation

### Run Evaluation Suite

```bash
# Run all 50 test questions
python3 tests/test_runner_comprehensive.py

# Evaluate results with 4 metrics
python3 tests/evaluation.py

# Results saved to: tests/results/
```

### Run Red Team Security Tests

```bash
# Start API server (Terminal 1)
python3 api_server.py

# Run Promptfoo security tests (Terminal 2)
npx promptfoo@latest eval -c promptfooconfig-api.yaml

# View results in browser
npx promptfoo@latest view
```

## 📁 Project Structure

```
SherlockRAG/
├── README.md                          # This file
├── EVALUATION_REPORT.md               # Detailed evaluation results
├── FUTURE_IMPROVEMENTS.md             # Proposed enhancements
├── DEBUGGING_REFERENCE.txt            # Case study: Watson's moustache
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
│
├── data/
│   ├── raw/
│   │   └── sherlock_complete.txt      # Source text (61 stories)
│   ├── processed/
│   │   ├── stories/                   # Individual story files
│   │   └── stories_metadata.json      # Story metadata
│   └── chroma_db/                     # Vector database (persistent)
│
├── parse_stories.py                   # Data pipeline
├── build_index.py                     # Vector DB builder
├── chatbot.py                         # Main RAG system
├── api_server.py                      # Flask API wrapper
│
└── tests/
    ├── test_suite.py                  # 20 basic questions
    ├── test_suite_comprehensive.py    # 50 comprehensive questions
    ├── test_runner_comprehensive.py   # Test execution
    ├── evaluation.py                  # 4-metric evaluation
    ├── temperature_experiment.py      # Temperature testing
    ├── promptfooconfig-api.yaml       # Red team config
    └── results/                       # Evaluation outputs
        ├── baseline_comprehensive_v1.0.json
        └── evaluation_results_*.json
```

## 🛡️ Security

Red team testing with 11 attack vectors:

- ✅ **Prompt Injection:** 100% resistance (refuses off-topic requests)
- ✅ **Information Leakage:** 100% protection (no API keys, system prompts, or DB info exposed)
- ✅ **Jailbreaking:** 100% resistance (refuses harmful/criminal requests)
- ✅ **System Prompt Extraction:** 100% protection (doesn't reveal operational details)

**Note:** Automated tests showed 75-88% pass rates due to strict keyword matching, but manual review confirmed 100% security. See evaluation report for details.

## 🎯 Known Limitations

### Multi-Hop Reasoning (45.4%)
Queries requiring synthesis across multiple stories show reduced accuracy.

**Examples:**
- "How did Holmes fake his death and return?" (requires 2 stories)
- "What happened to Moriarty's organization after his death?" (cause → effect)

**Current approach:** Single-retrieval pass optimized for single-document queries

**Workaround:** Break complex questions into simpler parts:
- "How did Holmes fake his death?" → 88% accuracy ✅
- "How did Holmes return?" → 88% accuracy ✅

### Chunk Boundary Issues (64.2%)
Specific details in very long documents (e.g., Watson's wound location in 59k-word story) may rank outside retrieval window.

**Solution in progress:** See [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md)

## 💡 Key Learnings & Debugging Stories

### Case Study 1: Watson's Moustache (Needle in Haystack)
**Problem:** Query "Did Watson have a moustache?" returned "not mentioned" despite fact existing in corpus.

**Investigation:**
1. Verified data exists (grep found "modest moustache" in Red Circle)
2. Tested retrieval directly (chunk ranked #15-20, outside k=10 window)
3. Identified semantic mismatch (moustache mentioned in forensics discussion, not appearance description)

**Solution:** Implemented keyword fallback for specific terms (moustache, watson, etc.)

**Result:** Success rate improved from 60% → 90% on edge cases

**See:** [DEBUGGING_REFERENCE.txt](DEBUGGING_REFERENCE.txt) for full analysis

### Case Study 2: Temperature Optimization
**Discovery:** Initial temperature=0.7 caused occasional creative embellishment beyond retrieved context.

**Experiment:** Tested 0.0, 0.3, 0.7, 1.0 on same questions

**Finding:** Temperature 0.5 provides optimal balance of natural language while maintaining faithfulness to sources.

**Result:** Faithfulness improved from 75.8% → 83.8%

## 🔧 Technical Stack

- **LLM:** Claude Sonnet 4 (Anthropic)
- **Vector Database:** ChromaDB
- **Embeddings:** all-MiniLM-L6-v2 (384 dimensions)
- **Framework:** LangChain (document processing, text splitting)
- **API:** Flask (optional HTTP interface)
- **Testing:** Custom eval framework + Promptfoo (red team)
- **Language:** Python 3.9+

## 📈 Development Timeline

- **Week 1:** Built keyword RAG (73% retrieval)
- **Week 2:** Implemented vector search (96% retrieval)
- **Week 3:** Added LangChain framework
- **Week 4:** Built SherlockRAG with hybrid retrieval
- **Week 5:** Comprehensive evaluation (20 → 50 questions)
- **Week 6:** Red team security testing
- **Total:** 6 weeks from concept to production-ready system

## 🎓 Educational Value

This project demonstrates:

1. **RAG Architecture:** Multi-stage retrieval, hybrid search, query optimization
2. **Evaluation Methodology:** 4-metric framework, comprehensive test coverage, edge case testing
3. **Security Testing:** Red team methodology, attack vector identification, automated testing
4. **Debugging Skills:** Systematic root cause analysis, iterative improvement, regression testing
5. **Production Thinking:** Trade-off analysis, documentation, known limitations, cost awareness
6. **Engineering Maturity:** Knowing when to ship vs optimize, documenting future work

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Multi-hop reasoning enhancement (see FUTURE_IMPROVEMENTS.md)
- Additional test cases
- Performance optimizations
- UI/UX improvements

Please:
1. Fork the repository
2. Create a feature branch
3. Run full evaluation suite
4. Document before/after metrics
5. Submit PR with results

## 📄 License

This project uses public domain texts (Sherlock Holmes canon) and is provided for educational purposes.

## 🙏 Acknowledgments

- **Data Source:** Project Gutenberg (public domain Sherlock Holmes texts)
- **Inspiration:** AI Bootcamp evaluation projects
- **Framework:** Built with Claude (Anthropic) and open-source tools

## 📞 Contact

Built by [Your Name] as part of AI Engineering portfolio

- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)
- Portfolio: [yourwebsite.com](https://yourwebsite.com)

---

**Status:** Production-ready (81.3% overall accuracy)

**Last Updated:** December 2025

**Next Steps:** See [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md) for enhancement roadmap