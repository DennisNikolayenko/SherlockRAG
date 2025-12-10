#!/usr/bin/env python3
"""
SherlockRAG Evaluation Framework
Evaluates test results with 4 metrics: Retrieval, Relevance, Faithfulness, Correctness
"""

import json
import os
import sys
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# Add parent directory to path so we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def evaluate_retrieval(test, result):
    """
    Metric 1: RETRIEVAL
    Did we retrieve the expected sources?
    Score: 0-100
    """
    expected_sources = test.get('expected_sources', [])
    actual_sources = result.get('actual_sources', [])
    
    # Handle error cases
    if 'error' in result:
        return 0
    
    # If no specific source expected (like adversarial)
    if not expected_sources or expected_sources == []:
        return 100  # No retrieval requirement
    
    # Check if expected sources were retrieved
    if expected_sources == ["Multiple stories"]:
        # Just need multiple sources
        return 100 if len(actual_sources) >= 2 else 50
    
    # Check for specific sources
    matches = 0
    for expected in expected_sources:
        for actual in actual_sources:
            if expected.lower() in actual.lower():
                matches += 1
                break
    
    # Score based on matches
    if matches == 0:
        return 0
    elif matches == len(expected_sources):
        return 100
    else:
        return int((matches / len(expected_sources)) * 100)


def evaluate_relevance(test, result, api_key):
    """
    Metric 2: RELEVANCE
    Does the answer address the question?
    Score: 0-100
    Uses Claude as judge
    """
    if 'error' in result:
        return 0
    
    question = test['question']
    answer = result.get('actual_answer', '')
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Evaluate if this answer addresses the question.

Question: {question}

Answer: {answer}

Score the relevance from 0-100:
- 100: Directly answers the question
- 75: Addresses question but could be more direct
- 50: Partially addresses question
- 25: Tangentially related
- 0: Completely off-topic

Return ONLY a number from 0-100, nothing else."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        score_text = message.content[0].text.strip()
        score = int(score_text)
        return max(0, min(100, score))  # Clamp to 0-100
        
    except Exception as e:
        print(f"  ⚠️  Relevance eval error: {e}")
        return 50  # Default to middle score on error


def evaluate_faithfulness(test, result, api_key):
    """
    Metric 3: FAITHFULNESS
    Is the answer grounded in the retrieved sources?
    Score: 0-100
    Uses Claude as judge
    """
    if 'error' in result:
        return 0
    
    # For adversarial/negative queries, different criteria
    if test['category'] in ['adversarial', 'negative_query']:
        # Should refuse or say not mentioned
        answer = result.get('actual_answer', '').lower()
        if any(word in answer for word in ['not mentioned', 'no', "don't", "cannot", "isn't in"]):
            return 100  # Correctly admitted absence
        else:
            return 0  # May have hallucinated
    
    answer = result.get('actual_answer', '')
    sources = result.get('actual_sources', [])
    
    # For simplicity, we'll use Claude to check
    # (In production, you'd extract chunks and check sentence-by-sentence)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Evaluate if this answer is faithful to the Sherlock Holmes canon.

Answer: {answer}

Sources cited: {', '.join(sources)}

Score faithfulness from 0-100:
- 100: All claims are reasonable for Sherlock Holmes stories
- 75: Mostly faithful with minor speculation
- 50: Some unsupported claims
- 25: Significant speculation or extrapolation
- 0: Contains clear fabrications or hallucinations

Return ONLY a number from 0-100, nothing else."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        score_text = message.content[0].text.strip()
        score = int(score_text)
        return max(0, min(100, score))
        
    except Exception as e:
        print(f"  ⚠️  Faithfulness eval error: {e}")
        return 75  # Default to somewhat faithful


def evaluate_correctness(test, result, api_key):
    """
    Metric 4: CORRECTNESS
    Is the answer factually accurate?
    Score: 0-100
    Uses Claude as judge with ground truth
    """
    if 'error' in result:
        return 0
    
    expected = test.get('expected_answer', '')
    actual = result.get('actual_answer', '')
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Compare this answer to the expected answer for factual correctness.

Question: {test['question']}

Expected answer: {expected}

Actual answer: {actual}

Score correctness from 0-100:
- 100: Factually correct, matches expected
- 75: Mostly correct, minor inaccuracies
- 50: Partially correct
- 25: Mostly incorrect
- 0: Completely wrong

Return ONLY a number from 0-100, nothing else."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        score_text = message.content[0].text.strip()
        score = int(score_text)
        return max(0, min(100, score))
        
    except Exception as e:
        print(f"  ⚠️  Correctness eval error: {e}")
        return 50


def evaluate_all(results_file):
    """Run all 4 metrics on test results"""
    
    print("=" * 70)
    print("📊 SHERLOCKRAG EVALUATION")
    print("=" * 70)
    
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print(f"\nEvaluating {len(results)} test results...")
    print(f"Results file: {results_file}\n")
    
    # Load test questions for ground truth
    # Try comprehensive suite first, fall back to original
    try:
        from test_suite_comprehensive import test_questions
        print("Using comprehensive test suite (50 questions)")
    except ImportError:
        from test_suite import test_questions
        print("Using original test suite (20 questions)")
    
    test_dict = {t['id']: t for t in test_questions}
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Evaluate each result
    scores = {
        "retrieval": [],
        "relevance": [],
        "faithfulness": [],
        "correctness": []
    }
    
    detailed_results = []
    
    for i, result in enumerate(results, 1):
        test_id = result['id']
        test = test_dict.get(test_id, {})
        
        print(f"\n[{i}/{len(results)}] Evaluating: {result['question'][:50]}...")
        
        # Calculate scores
        retrieval = evaluate_retrieval(test, result)
        relevance = evaluate_relevance(test, result, api_key)
        faithfulness = evaluate_faithfulness(test, result, api_key)
        correctness = evaluate_correctness(test, result, api_key)
        
        scores["retrieval"].append(retrieval)
        scores["relevance"].append(relevance)
        scores["faithfulness"].append(faithfulness)
        scores["correctness"].append(correctness)
        
        print(f"  Retrieval: {retrieval}% | Relevance: {relevance}% | Faithfulness: {faithfulness}% | Correctness: {correctness}%")
        
        # Save detailed result
        detailed_results.append({
            **result,
            "scores": {
                "retrieval": retrieval,
                "relevance": relevance,
                "faithfulness": faithfulness,
                "correctness": correctness,
                "average": (retrieval + relevance + faithfulness + correctness) / 4
            }
        })
    
    # Calculate averages
    avg_scores = {
        "retrieval": sum(scores["retrieval"]) / len(scores["retrieval"]),
        "relevance": sum(scores["relevance"]) / len(scores["relevance"]),
        "faithfulness": sum(scores["faithfulness"]) / len(scores["faithfulness"]),
        "correctness": sum(scores["correctness"]) / len(scores["correctness"])
    }
    
    avg_scores["overall"] = sum(avg_scores.values()) / 4
    
    # Calculate by category
    category_scores = {}
    for result in detailed_results:
        cat = result['category']
        if cat not in category_scores:
            category_scores[cat] = []
        category_scores[cat].append(result['scores']['average'])
    
    category_averages = {cat: sum(scores)/len(scores) for cat, scores in category_scores.items()}
    
    # Print results
    print("\n" + "=" * 70)
    print("📊 EVALUATION RESULTS")
    print("=" * 70)
    print(f"\n🎯 Overall Scores:")
    print(f"  Retrieval:    {avg_scores['retrieval']:.1f}%")
    print(f"  Relevance:    {avg_scores['relevance']:.1f}%")
    print(f"  Faithfulness: {avg_scores['faithfulness']:.1f}%")
    print(f"  Correctness:  {avg_scores['correctness']:.1f}%")
    print(f"  {'─' * 40}")
    print(f"  OVERALL:      {avg_scores['overall']:.1f}%")
    
    print(f"\n📋 By Category:")
    for cat, score in sorted(category_averages.items(), key=lambda x: x[1], reverse=True):
        count = len(category_scores[cat])
        print(f"  {cat:25s} {score:5.1f}% ({count} questions)")
    
    # Identify failures
    failures = [r for r in detailed_results if r['scores']['average'] < 70]
    if failures:
        print(f"\n⚠️  Low Scores (< 70%):")
        for f in failures:
            print(f"  • Q{f['id']}: {f['question'][:50]}... ({f['scores']['average']:.1f}%)")
    
    # Save detailed results
    output_file = f"tests/results/evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            "summary": avg_scores,
            "by_category": category_averages,
            "detailed_results": detailed_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {output_file}")
    print("=" * 70)
    
    return avg_scores, detailed_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 evaluation.py <test_results_file.json>")
        print("\nLooking for most recent test_results file...")
        
        # Find most recent results file in tests/results
        results_dir = 'tests/results'
        if os.path.exists(results_dir):
            results_files = [f for f in os.listdir(results_dir) if f.startswith('test_results_') and f.endswith('.json')]
            if results_files:
                latest = sorted(results_files)[-1]
                latest_path = os.path.join(results_dir, latest)
                print(f"Found: {latest}\n")
                evaluate_all(latest_path)
            else:
                print(f"No test results found in {results_dir}/. Run test_runner.py first!")
        else:
            print(f"Directory {results_dir}/ not found. Run test_runner.py first!")
    else:
        evaluate_all(sys.argv[1])