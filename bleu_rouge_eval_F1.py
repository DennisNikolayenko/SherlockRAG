"""
BLEU/ROUGE + Retrieval F1 Evaluation for SherlockRAG
Comprehensive evaluation with industry-standard metrics
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


def calculate_retrieval_f1(expected_sources: List[str], actual_sources: List[str]) -> Dict:
    """
    Calculate Precision, Recall, and F1 for document retrieval
    
    This measures: Did the system retrieve the RIGHT documents?
    
    Args:
        expected_sources: List of documents that should have been retrieved
        actual_sources: List of documents actually retrieved by system
        
    Returns:
        Dictionary with precision, recall, f1, and counts
    """
    # Convert to sets for comparison
    expected_set = set(expected_sources)
    actual_set = set(actual_sources)
    
    # Calculate overlap
    true_positives = len(expected_set & actual_set)  # Correctly retrieved
    false_positives = len(actual_set - expected_set)  # Retrieved but wrong
    false_negatives = len(expected_set - actual_set)  # Missed documents
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }


def run_comprehensive_evaluation():
    """Run complete evaluation: BLEU/ROUGE + Retrieval F1"""
    
    print("=" * 70)
    print("🚀 Comprehensive Evaluation: BLEU/ROUGE + Retrieval F1")
    print("=" * 70)
    
    # Load test results
    test_file = "tests/results/test_results_comprehensive_20251208_162645.json"
    
    print(f"\n✓ Loading test results from: {test_file}")
    
    with open(test_file, 'r') as f:
        test_results = json.load(f)
    
    print(f"✓ Loaded {len(test_results)} test questions\n")
    print("Starting evaluation...")
    print("-" * 70)
    
    # Initialize results storage
    results = []
    
    # BLEU/ROUGE scores
    bleu_scores = []
    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []
    
    # Retrieval F1 scores
    retrieval_precision_scores = []
    retrieval_recall_scores = []
    retrieval_f1_scores = []
    
    # Process each question
    for i, test in enumerate(test_results, 1):
        question = test['question']
        expected = test['expected_answer']
        generated = test['actual_answer']
        category = test['category']
        
        # Get source information
        expected_sources = test.get('expected_sources', [])
        actual_sources = test.get('actual_sources', [])
        
        print(f"\n[{i}/{len(test_results)}] Category: {category}")
        print(f"Q: {question[:70]}...")
        
        try:
            # ========================================
            # PART 1: Answer Quality (BLEU/ROUGE)
            # ========================================
            bleu_score = calculate_bleu(expected, generated)
            bleu_scores.append(bleu_score)
            
            rouge_scores = calculate_rouge(expected, generated)
            rouge1_scores.append(rouge_scores['rouge1'])
            rouge2_scores.append(rouge_scores['rouge2'])
            rougeL_scores.append(rouge_scores['rougeL'])
            
            print(f"  Answer Quality:")
            print(f"    BLEU:    {bleu_score:.2f}/100")
            print(f"    ROUGE-1: {rouge_scores['rouge1']:.3f}")
            print(f"    ROUGE-L: {rouge_scores['rougeL']:.3f}")
            
            # ========================================
            # PART 2: Retrieval Quality (Precision/Recall/F1)
            # ========================================
            if expected_sources and actual_sources:
                retrieval_metrics = calculate_retrieval_f1(expected_sources, actual_sources)
                
                retrieval_precision_scores.append(retrieval_metrics['precision'])
                retrieval_recall_scores.append(retrieval_metrics['recall'])
                retrieval_f1_scores.append(retrieval_metrics['f1'])
                
                print(f"  Retrieval Quality:")
                print(f"    Precision: {retrieval_metrics['precision']:.3f}")
                print(f"    Recall:    {retrieval_metrics['recall']:.3f}")
                print(f"    F1:        {retrieval_metrics['f1']:.3f}")
            else:
                retrieval_metrics = None
                print(f"  Retrieval Quality: N/A (no source tracking)")
            
            # Store results
            results.append({
                'id': test['id'],
                'question': question,
                'category': category,
                'expected': expected,
                'generated': generated,
                'bleu': round(bleu_score, 2),
                'rouge1': round(rouge_scores['rouge1'], 3),
                'rouge2': round(rouge_scores['rouge2'], 3),
                'rougeL': round(rouge_scores['rougeL'], 3),
                'retrieval': retrieval_metrics
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # ========================================
    # OVERALL RESULTS
    # ========================================
    avg_bleu = sum(bleu_scores) / len(bleu_scores)
    avg_rouge1 = sum(rouge1_scores) / len(rouge1_scores)
    avg_rouge2 = sum(rouge2_scores) / len(rouge2_scores)
    avg_rougeL = sum(rougeL_scores) / len(rougeL_scores)
    
    print("\n" + "=" * 70)
    print("📊 OVERALL RESULTS")
    print("=" * 70)
    
    print("\nAnswer Quality Metrics:")
    print(f"  Average BLEU Score:    {avg_bleu:.2f}/100")
    print(f"  Average ROUGE-1:       {avg_rouge1:.3f}")
    print(f"  Average ROUGE-2:       {avg_rouge2:.3f}")
    print(f"  Average ROUGE-L:       {avg_rougeL:.3f}")
    
    if retrieval_precision_scores:
        avg_retrieval_precision = sum(retrieval_precision_scores) / len(retrieval_precision_scores)
        avg_retrieval_recall = sum(retrieval_recall_scores) / len(retrieval_recall_scores)
        avg_retrieval_f1 = sum(retrieval_f1_scores) / len(retrieval_f1_scores)
        
        print("\nRetrieval Quality Metrics:")
        print(f"  Average Precision:     {avg_retrieval_precision:.3f}")
        print(f"  Average Recall:        {avg_retrieval_recall:.3f}")
        print(f"  Average F1:            {avg_retrieval_f1:.3f}")
        
        print("\n📊 RESULTS BY CATEGORY")
        print("=" * 70)
        
        # Calculate by category
        category_stats = {}
        for result in results:
            cat = result['category']
            if cat not in category_stats:
                category_stats[cat] = {
                    'bleu': [],
                    'rouge1': [],
                    'rougeL': [],
                    'retrieval_f1': []
                }
            category_stats[cat]['bleu'].append(result['bleu'])
            category_stats[cat]['rouge1'].append(result['rouge1'])
            category_stats[cat]['rougeL'].append(result['rougeL'])
            if result['retrieval']:
                category_stats[cat]['retrieval_f1'].append(result['retrieval']['f1'])
        
        for cat, scores in sorted(category_stats.items()):
            cat_bleu = sum(scores['bleu']) / len(scores['bleu'])
            cat_rouge1 = sum(scores['rouge1']) / len(scores['rouge1'])
            cat_rougeL = sum(scores['rougeL']) / len(scores['rougeL'])
            cat_f1 = sum(scores['retrieval_f1']) / len(scores['retrieval_f1']) if scores['retrieval_f1'] else 0
            
            print(f"\n{cat.upper()}:")
            print(f"  BLEU:         {cat_bleu:.2f}/100")
            print(f"  ROUGE-1:      {cat_rouge1:.3f}")
            print(f"  ROUGE-L:      {cat_rougeL:.3f}")
            print(f"  Retrieval F1: {cat_f1:.3f}")
    
    print("\n" + "=" * 70)
    
    # ========================================
    # SAVE RESULTS
    # ========================================
    output = {
        'summary': {
            'total_questions': len(test_results),
            'evaluated_questions': len(bleu_scores),
            'answer_quality': {
                'avg_bleu': round(avg_bleu, 2),
                'avg_rouge1': round(avg_rouge1, 3),
                'avg_rouge2': round(avg_rouge2, 3),
                'avg_rougeL': round(avg_rougeL, 3)
            },
            'retrieval_quality': {
                'avg_precision': round(avg_retrieval_precision, 3) if retrieval_precision_scores else None,
                'avg_recall': round(avg_retrieval_recall, 3) if retrieval_recall_scores else None,
                'avg_f1': round(avg_retrieval_f1, 3) if retrieval_f1_scores else None
            } if retrieval_precision_scores else None
        },
        'detailed_results': results
    }
    
    output_file = 'comprehensive_evaluation_results.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    print("\n🎯 Evaluation Interpretation:")
    print("  Answer Quality (BLEU/ROUGE): Measures word overlap")
    print("  Retrieval Quality (F1): Measures if right documents retrieved")
    print("\n✅ Comprehensive evaluation complete!")
    
    return output


if __name__ == "__main__":
    results = run_comprehensive_evaluation()