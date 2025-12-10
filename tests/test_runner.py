#!/usr/bin/env python3
"""
SherlockRAG Test Runner
Runs all test questions and saves results for evaluation
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path so we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_suite import test_questions
from chatbot import load_vector_store, retrieve_context, generate_answer


def run_test_suite():
    """Run all test questions and save results"""
    
    print("=" * 70)
    print("🔍 SHERLOCKRAG TEST RUNNER")
    print("=" * 70)
    print(f"\nTotal questions: {len(test_questions)}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nLoading knowledge base...")
    
    # Load vector store
    vectorstore = load_vector_store("data/chroma_db")
    print("✅ Knowledge base loaded\n")
    
    # Run tests
    results = []
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_questions)}: {test['question']}")
        print(f"Category: {test['category']}")
        print("-" * 70)
        
        try:
            # Retrieve context
            context, sources = retrieve_context(vectorstore, test['question'])
            
            print(f"Retrieved {len(sources)} sources: {', '.join(sources[:3])}")
            
            # Generate answer
            answer = generate_answer(test['question'], context, sources)
            
            print(f"\n📖 Answer:")
            print(answer[:200] + "..." if len(answer) > 200 else answer)
            
            # Save result
            result = {
                "id": test['id'],
                "question": test['question'],
                "category": test['category'],
                "expected_answer": test['expected_answer'],
                "expected_sources": test.get('expected_sources', []),
                "actual_answer": answer,
                "actual_sources": sources,
                "difficulty": test['difficulty'],
                "notes": test.get('notes', '')
            }
            
            results.append(result)
            print("\n✅ Test complete")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            result = {
                "id": test['id'],
                "question": test['question'],
                "category": test['category'],
                "error": str(e)
            }
            results.append(result)
    
    # Save results
    output_file = f"tests/results/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ All tests complete!")
    print(f"📁 Results saved to: {output_file}")
    print(f"🔜 Next: Run evaluation.py to score results")
    print("=" * 70)
    
    return results, output_file


if __name__ == "__main__":
    results, output_file = run_test_suite()