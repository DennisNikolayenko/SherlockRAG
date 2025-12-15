"""
BLEU/ROUGE Evaluation for SherlockRAG
Adds industry-standard NLG metrics to complement custom evaluation
"""

import json
from rouge_score import rouge_scorer
from sacrebleu.metrics import BLEU
from typing import Dict, List

# Initialize BLEU and ROUGE scorers
bleu_metric = BLEU()
rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)


def calculate_bleu(reference: str, candidate: str) -> float:
    """Calculate BLEU score (0-100, higher is better)"""
    score = bleu_metric.sentence_score(candidate, [reference])
    return score.score


def calculate_rouge(reference: str, candidate: str) -> Dict[str, float]:
    """Calculate ROUGE scores (0-1, higher is better)"""
    scores = rouge.score(reference, candidate)
    return {
        'rouge1': scores['rouge1'].fmeasure,
        'rouge2': scores['rouge2'].fmeasure,
        'rougeL': scores['rougeL'].fmeasure
    }


def run_bleu_rouge_evaluation():
    """Run BLEU/ROUGE evaluation on SherlockRAG test results"""
    
    print("=" * 70)
    print("🚀 BLEU/ROUGE Evaluation for SherlockRAG")
    print("=" * 70)
    
    # Load your comprehensive test results
    test_file = "tests/results/test_results_comprehensive_20251208_162645.json"
    
    print(f"\n✓ Loading test results from: {test_file}")
    
    with open(test_file, 'r') as f:
        test_results = json.load(f)
    
    print(f"✓ Loaded {len(test_results)} test questions\n")
    print("Starting BLEU/ROUGE evaluation...")
    print("-" * 70)
    
    # Initialize results storage
    results = []
    bleu_scores = []
    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []
    
    # Process each question
    for i, test in enumerate(test_results, 1):
        question = test['question']
        expected = test['expected_answer']
        generated = test['actual_answer']
        category = test['category']
        
        print(f"\n[{i}/{len(test_results)}] Category: {category}")
        print(f"Q: {question[:70]}...")
        
        try:
            # Calculate BLEU score
            bleu_score = calculate_bleu(expected, generated)
            bleu_scores.append(bleu_score)
            
            # Calculate ROUGE scores
            rouge_scores = calculate_rouge(expected, generated)
            rouge1_scores.append(rouge_scores['rouge1'])
            rouge2_scores.append(rouge_scores['rouge2'])
            rougeL_scores.append(rouge_scores['rougeL'])
            
            print(f"  BLEU:    {bleu_score:.2f}/100")
            print(f"  ROUGE-1: {rouge_scores['rouge1']:.3f}")
            print(f"  ROUGE-2: {rouge_scores['rouge2']:.3f}")
            print(f"  ROUGE-L: {rouge_scores['rougeL']:.3f}")
            
            results.append({
                'id': test['id'],
                'question': question,
                'category': category,
                'expected': expected,
                'generated': generated,
                'bleu': round(bleu_score, 2),
                'rouge1': round(rouge_scores['rouge1'], 3),
                'rouge2': round(rouge_scores['rouge2'], 3),
                'rougeL': round(rouge_scores['rougeL'], 3)
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Calculate averages
    avg_bleu = sum(bleu_scores) / len(bleu_scores)
    avg_rouge1 = sum(rouge1_scores) / len(rouge1_scores)
    avg_rouge2 = sum(rouge2_scores) / len(rouge2_scores)
    avg_rougeL = sum(rougeL_scores) / len(rougeL_scores)
    
    # Calculate by category
    category_stats = {}
    for result in results:
        cat = result['category']
        if cat not in category_stats:
            category_stats[cat] = {
                'bleu': [],
                'rouge1': [],
                'rouge2': [],
                'rougeL': []
            }
        category_stats[cat]['bleu'].append(result['bleu'])
        category_stats[cat]['rouge1'].append(result['rouge1'])
        category_stats[cat]['rouge2'].append(result['rouge2'])
        category_stats[cat]['rougeL'].append(result['rougeL'])
    
    # Print results
    print("\n" + "=" * 70)
    print("📊 OVERALL RESULTS")
    print("=" * 70)
    print(f"Questions Evaluated:   {len(bleu_scores)}")
    print(f"Average BLEU Score:    {avg_bleu:.2f}/100")
    print(f"Average ROUGE-1:       {avg_rouge1:.3f}")
    print(f"Average ROUGE-2:       {avg_rouge2:.3f}")
    print(f"Average ROUGE-L:       {avg_rougeL:.3f}")
    print("=" * 70)
    
    # Print category breakdown
    print("\n📊 RESULTS BY CATEGORY")
    print("=" * 70)
    for cat, scores in sorted(category_stats.items()):
        cat_bleu = sum(scores['bleu']) / len(scores['bleu'])
        cat_rouge1 = sum(scores['rouge1']) / len(scores['rouge1'])
        cat_rougeL = sum(scores['rougeL']) / len(scores['rougeL'])
        print(f"\n{cat.upper()}:")
        print(f"  BLEU:    {cat_bleu:.2f}/100")
        print(f"  ROUGE-1: {cat_rouge1:.3f}")
        print(f"  ROUGE-L: {cat_rougeL:.3f}")
    
    print("\n" + "=" * 70)
    
    # Save results
    output = {
        'summary': {
            'total_questions': len(test_results),
            'evaluated_questions': len(bleu_scores),
            'avg_bleu': round(avg_bleu, 2),
            'avg_rouge1': round(avg_rouge1, 3),
            'avg_rouge2': round(avg_rouge2, 3),
            'avg_rougeL': round(avg_rougeL, 3)
        },
        'by_category': {
            cat: {
                'avg_bleu': round(sum(scores['bleu']) / len(scores['bleu']), 2),
                'avg_rouge1': round(sum(scores['rouge1']) / len(scores['rouge1']), 3),
                'avg_rouge2': round(sum(scores['rouge2']) / len(scores['rouge2']), 3),
                'avg_rougeL': round(sum(scores['rougeL']) / len(scores['rougeL']), 3)
            }
            for cat, scores in category_stats.items()
        },
        'detailed_results': results
    }
    
    output_file = 'bleu_rouge_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n🎯 What these scores mean:")
    print("  BLEU 30-50:   Good (RAG answers differ in wording)")
    print("  ROUGE-L 0.4-0.6: Good coverage of reference content")
    print("\n✅ BLEU/ROUGE evaluation complete!")
    
    return output


if __name__ == "__main__":
    results = run_bleu_rouge_evaluation()

