# Future Improvements for SherlockRAG

This document outlines proposed enhancements to improve SherlockRAG's performance, particularly for MULTI_HOP 
reasoning and edge cases.

## Current Performance Summary

- **Overall:** 81.3% across 50 test questions
- **Strengths:** Happy path (88.8%), Similar names (83.8%), Negative queries (93.8%)
- **Weaknesses:** Multi-hop (45.4%), Chunk boundary (64.2%)

---

## 1. Multi-Hop Reasoning Enhancement 🎯

### Current Performance
- **Multi-hop queries:** 45.4% (3/3 questions failed)
- **Single-document queries:** 88.8%
- **Gap:** 43.4 percentage points

### Problem Description

Multi-hop questions require connecting information across multiple stories:

**Example Query:** "How did Holmes fake his death and return?"

**Requires:**
1. Information from "The Final Problem" (death at Reichenbach Falls)
2. Information from "The Empty House" (return explanation)
3. Synthesis connecting both events

**Current System:**
- Retrieves 15 chunks per query variation (3 variations = 45 chunks)
- After deduplication: ~20-30 unique chunks
- **Problem:** Chunks tend to cluster from ONE story, missing the second relevant story

### Root Cause Analysis

```
Query: "How did Holmes fake death and return?"

Current retrieval pattern:
- Final Problem chunks: 12 (higher semantic match to "death")
- Empty House chunks: 3 (lower semantic match)
- Other stories: 5

Result: Missing critical "return" information from Empty House
```

---

### Solution 1: Increase Retrieval Window ⭐ **RECOMMENDED FIRST**

**Approach:** Increase k parameter from 15 to 20-25 per query variation

**Implementation:**
```python
# File: chatbot.py, line ~114
# Current:
results = vectorstore.similarity_search(q, k=15)

# Proposed:
results = vectorstore.similarity_search(q, k=20)  # or k=25
```

**Expected Impact:**
- Multi-hop: 45.4% → 60-70%
- Other metrics: ±2% (minimal impact)
- Overall: 81.3% → 82-84%

**Pros:**
- ✅ One-line change (5 minutes)
- ✅ Low risk to existing performance
- ✅ Fast to test and validate
- ✅ No architectural changes

**Cons:**
- ⚠️ More noise in context (less relevant chunks)
- ⚠️ Slightly higher API costs (~+30-50%)
- ⚠️ May not fully solve the problem

**Testing Strategy:**
1. Backup current version: `cp chatbot.py chatbot_v1.py`
2. Change k parameter to 20
3. Re-run comprehensive eval: `python3 tests/test_runner_comprehensive.py`
4. Compare metrics: Baseline (81.3%) vs New
5. If overall improves without breaking strengths → commit
6. If insufficient improvement → try Solution 2

**Estimated Development Time:** 5 minutes  
**Testing Time:** 30 minutes (50 questions)

---

### Solution 2: Query Decomposition 🎯 **BEST LONG-TERM**

**Approach:** Detect multi-hop questions and break into sub-queries before retrieval

**High-Level Flow:**
```
1. Detect multi-hop pattern (keywords: "and", "after", "then", "before")
2. Use Claude to decompose into sub-queries
3. Retrieve chunks for EACH sub-query separately
4. Combine all chunks
5. Generate answer from combined context
```

**Implementation:**

```python
# File: chatbot.py
# Add after line ~80

def is_multi_hop(query):
    """Detect multi-hop questions"""
    multi_hop_keywords = ['and', 'then', 'after', 'before', 'both']
    query_lower = query.lower()
    
    # Check for connecting words
    has_connector = any(word in query_lower for word in multi_hop_keywords)
    
    # Check for multiple question marks or complex structure
    is_complex = len(query.split()) > 15 or query.count('?') > 1
    
    return has_connector or is_complex


def decompose_query(query, api_key):
    """Use Claude to break complex query into sub-queries"""
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Break this complex question into 2-3 simpler sub-questions that together answer the original question.

Original question: {query}

Return ONLY a JSON array of sub-questions, nothing else.
Example: ["sub-question 1", "sub-question 2"]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )
    
    import json
    sub_queries = json.loads(message.content[0].text)
    return sub_queries


def retrieve_context_multi_hop(vectorstore, query, api_key, k=10):
    """Enhanced retrieval for multi-hop questions"""
    
    # Check if multi-hop
    if is_multi_hop(query):
        print("   🔗 Multi-hop question detected - using decomposition")
        
        # Decompose into sub-queries
        sub_queries = decompose_query(query, api_key)
        print(f"   📝 Sub-queries: {sub_queries}")
        
        # Retrieve for each sub-query
        all_chunks = []
        seen_content = set()
        
        for sub_q in sub_queries:
            # Use existing multi-query retrieval for each sub-question
            chunks, sources = retrieve_context(vectorstore, sub_q, k=k)
            
            # Add to collection (avoiding duplicates)
            for chunk in chunks:
                content_id = chunk[:100]  # First 100 chars as ID
                if content_id not in seen_content:
                    all_chunks.append(chunk)
                    seen_content.add(content_id)
        
        # Combine all sources
        combined_sources = list(set([s for _, sources in chunks for s in sources]))
        
        return all_chunks, combined_sources
    
    else:
        # Use standard retrieval for simple questions
        return retrieve_context(vectorstore, query, k=k)
```

**Expected Impact:**
- Multi-hop: 45.4% → 75-85%
- Other metrics: No change (only activates for multi-hop patterns)
- Overall: 81.3% → 85-87%

**Pros:**
- ✅ Targeted solution (doesn't affect simple queries)
- ✅ Significantly better multi-hop performance
- ✅ More intelligent/sophisticated approach
- ✅ Demonstrates advanced RAG techniques

**Cons:**
- ⚠️ ~40-50 lines of new code
- ⚠️ Extra API call for decomposition (~$0.01 per multi-hop query)
- ⚠️ Slightly increased latency (~1-2 seconds)
- ⚠️ Need to tune detection heuristics

**Testing Strategy:**
1. Implement on feature branch
2. Test on 3 known multi-hop questions first
3. If successful, run full 50-question eval
4. Validate that simple queries still work normally
5. Measure added cost and latency

**Estimated Development Time:** 2-3 hours  
**Testing Time:** 1 hour

---

### Solution 3: Story-Level Retrieval

**Approach:** Two-stage retrieval - first identify relevant STORIES, then get chunks from each

**High-Level Flow:**
```
1. Retrieve top 30 chunks (broad search)
2. Extract unique story titles from these chunks
3. For each relevant story, retrieve top K chunks specifically
4. Combine chunks from all relevant stories
```

**Implementation:**

```python
def retrieve_with_story_distribution(vectorstore, query, k=5):
    """Ensure chunks from multiple relevant stories"""
    
    # Stage 1: Broad retrieval to identify relevant stories
    initial_results = vectorstore.similarity_search(query, k=30)
    
    # Extract unique stories from top results
    story_scores = {}
    for i, doc in enumerate(initial_results[:15]):  # Top 15 for story detection
        title = doc.metadata.get('title', 'Unknown')
        score = 15 - i  # Higher score for higher rank
        story_scores[title] = story_scores.get(title, 0) + score
    
    # Get top 3-5 most relevant stories
    top_stories = sorted(story_scores.items(), key=lambda x: x[1], reverse=True)[:4]
    relevant_stories = [story for story, score in top_stories]
    
    print(f"   📚 Relevant stories: {relevant_stories}")
    
    # Stage 2: Get top chunks from EACH relevant story
    final_chunks = []
    seen_content = set()
    
    for story in relevant_stories:
        # Filter search to this specific story
        # Note: Requires ChromaDB metadata filtering support
        story_results = vectorstore.similarity_search(
            query,
            k=k,
            filter={"title": story}
        )
        
        for doc in story_results:
            content_id = doc.page_content[:100]
            if content_id not in seen_content:
                final_chunks.append(doc)
                seen_content.add(content_id)
    
    return final_chunks
```

**Expected Impact:**
- Multi-hop: 45.4% → 80-90%
- Other metrics: Possibly +2-5% (better story distribution)
- Overall: 81.3% → 86-89%

**Pros:**
- ✅ Guarantees chunks from multiple stories
- ✅ Intelligent distribution across sources
- ✅ Good for both multi-hop and complex queries

**Cons:**
- ⚠️ Requires ChromaDB metadata filtering (need to verify support)
- ⚠️ More complex (~50-60 lines)
- ⚠️ May slow down simple queries slightly
- ⚠️ Higher development and testing effort

**Testing Strategy:**
1. Verify ChromaDB supports metadata filtering
2. Implement on test branch
3. Test on multi-hop questions
4. Validate performance on all categories
5. Measure latency impact

**Estimated Development Time:** 4-6 hours  
**Testing Time:** 2 hours

---

### Recommendation: Phased Approach

**Phase 1:** Try Solution 1 (increase k)
- Fast, low-risk validation
- If improves multi-hop to 60-65%, may be sufficient

**Phase 2:** If Phase 1 insufficient, implement Solution 2 (query decomposition)
- More sophisticated, targeted fix
- Best balance of improvement vs complexity

**Phase 3:** Solution 3 only if targeting >85% multi-hop
- Highest complexity, highest potential gain
- Consider if SherlockRAG becomes production system

---

## 2. Chunk Boundary Optimization

### Current Performance: 64.2%

**Problem:** Specific details in very long documents split across chunks or ranked too low

**Example:** Watson's wound location in A Study in Scarlet (59k words, 445 chunks)

### Proposed Solutions

#### Option A: Increase Chunk Overlap
```python
# In build_index.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300,  # Increase from 200 to 300
    length_function=len
)
```

**Expected Impact:** 64.2% → 70-75%  
**Tradeoff:** 15-20% more chunks (higher storage/cost)

#### Option B: Smaller Chunks
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,   # Decrease from 1000
    chunk_overlap=250,
    length_function=len
)
```

**Expected Impact:** 64.2% → 72-78%  
**Tradeoff:** 40% more chunks, may lose context

#### Option C: Retrieve Adjacent Chunks
When a chunk is retrieved, also include the chunks immediately before/after it.

**Expected Impact:** 64.2% → 75-80%  
**Complexity:** Medium (requires chunk ID tracking)

---

## 3. Temperature Optimization

### Current Setting: 0.5

**Experiment conducted:** Tested 0.0, 0.3, 0.5, 0.7, 1.0

**Findings:**
- 0.0: Too robotic, terse responses
- 0.2: Very factual, minimal creativity
- 0.5: **Current choice** - good balance
- 0.7: More conversational but occasional speculation
- 1.0: Too creative, hallucination risk

### Potential Adjustment

**For maximum faithfulness:** Consider 0.3
- Expected faithfulness: 83.8% → 87-90%
- Tradeoff: Slightly less natural language

**For maximum engagement:** Consider 0.7
- Expected relevance: 77.1% → 82-85%
- Tradeoff: Possible slight decrease in faithfulness

**Recommendation:** Keep 0.5 for balanced performance

---

## 4. Contradiction Detection

### Current Performance: 74.1%

**Problem:** System doesn't surface known contradictions in Doyle's canon

**Examples:**
- Watson's wound: Shoulder (Study in Scarlet) vs Leg (Sign of Four)
- Watson's first name: John (usual) vs James (once mentioned)

### Proposed Solution

```python
def detect_contradictions(chunks, query):
    """Check if retrieved chunks contain conflicting information"""
    
    # Look for contradictory keywords
    contradiction_indicators = [
        ('shoulder', 'leg'),
        ('john', 'james'),
        ('cambridge', 'oxford')
    ]
    
    chunks_text = ' '.join([c.page_content.lower() for c in chunks])
    
    contradictions = []
    for term1, term2 in contradiction_indicators:
        if term1 in chunks_text and term2 in chunks_text:
            contradictions.append((term1, term2))
    
    return contradictions
```

**Integration:** Add note to answer when contradictions detected

**Expected Impact:** 74.1% → 82-85%

---

## 5. Other Potential Improvements

### A. Caching
- Cache query results for common questions
- Reduces API costs for repeated queries
- **Impact:** Cost reduction, faster responses

### B. Query Clarification
- Detect ambiguous queries
- Ask user for clarification before retrieval
- **Impact:** Better user experience, higher relevance

### C. Source Quality Ranking
- Prefer canonical sources (novels vs short stories)
- **Impact:** Higher correctness for core canon questions

### D. Streaming Responses
- Stream answer generation for better UX
- **Impact:** Perceived performance improvement

### E. Multi-modal Support
- Add images (story illustrations, character sketches)
- **Impact:** Richer user experience

---

## Cost-Benefit Analysis

| Improvement | Dev Time | Cost Impact | Expected Gain | Priority | Risk |
|-------------|----------|-------------|---------------|----------|------|
| Increase k | 5 min | +30% | +1-2% | **HIGH** | Low |
| Query decomp | 2-3 hrs | +$0.01/query | +4-6% | **MEDIUM** | Low |
| Story-level | 4-6 hrs | +50% | +5-8% | **LOW** | Medium |
| Chunk overlap | 30 min | +15% storage | +3-5% | **MEDIUM** | Low |
| Temperature | 5 min | None | ±2% | **LOW** | Low |
| Contradiction | 2 hrs | None | +5-7% | **MEDIUM** | Low |
| Caching | 3 hrs | -50% repeated | N/A | **LOW** | Low |

---

## Why Not Implement Everything Now?

### Diminishing Returns
- Current 81.3% is production-ready (80%+ standard)
- Improving 81% → 85% takes as much effort as 0% → 81%
- Perfect is the enemy of done

### Learning Opportunity
- Documenting trade-offs demonstrates engineering maturity
- Shows understanding of cost-benefit analysis
- Realistic production constraints (time, budget, priorities)

### User-Driven Prioritization
- In real production, implement based on user feedback
- "Which failures do users encounter most?"
- "What's the ROI of each improvement?"

### Current State is Valuable
- 81.3% with known limitations is better than:
  - 85% after 6 more months (opportunity cost)
  - Over-optimized system that's hard to maintain
  - Perfect system that never ships

---

## Contributing Guidelines

If you implement any improvement:

### Process
1. **Branch:** Create feature branch (`feature/multi-hop-decomposition`)
2. **Implement:** Make focused, isolated change
3. **Test:** Run full 50-question comprehensive eval
4. **Document:** Record before/after metrics
5. **PR:** Submit with results and analysis
6. **Update:** Add findings to this document

### Required Information in PR
- Baseline metrics (before change)
- New metrics (after change)
- Per-category breakdown
- Cost/latency impact
- Code changes summary
- Rollback plan if needed

### Example PR Description
```markdown
## Multi-Hop Enhancement: Query Decomposition

**Implementation:** Solution 2 from FUTURE_IMPROVEMENTS.md

**Results:**
- Multi-hop: 45.4% → 78.2% (+32.8%) ✅
- Overall: 81.3% → 85.1% (+3.8%) ✅
- Happy path: 88.8% → 88.5% (-0.3%) ✅ (acceptable)

**Cost Impact:** +$0.015 per multi-hop query (~8% of queries)

**Testing:** 50 comprehensive questions, 3 runs for consistency

**Recommendation:** MERGE - significant improvement with acceptable tradeoffs
```

---

## Research & Experimentation

### Areas for Further Investigation

1. **Different Embedding Models**
   - Test BGE, E5, or OpenAI embeddings
   - Compare retrieval quality vs all-MiniLM-L6-v2

2. **Hybrid Scoring**
   - Combine semantic + BM25 + metadata signals
   - Learn optimal weights

3. **Re-ranking**
   - Use cross-encoder for final ranking
   - May improve precision

4. **Graph-Based Retrieval**
   - Model story connections, character relationships
   - Enable traversal-based retrieval

5. **Agentic RAG**
   - Let Claude decide retrieval strategy dynamically
   - Iterative refinement based on intermediate results

---

## Version History

| Version | Date | Changes | Overall Score |
|---------|------|---------|---------------|
| v1.0 | Dec 2025 | Initial release | 81.3% |
| v1.1 | TBD | Increase k parameter | TBD |
| v2.0 | TBD | Query decomposition | TBD |

---

## Questions or Ideas?

Open an issue or submit a PR! This document is living and should evolve as we learn from implementation and user feedback.

---

*Last Updated: December 2025*