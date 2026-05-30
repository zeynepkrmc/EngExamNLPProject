"""
phrase_evaluation.py

N-gram phrase extraction kalitesini ölçmek için evaluation modülü.

Bu modül:
1. Raw top-K n-gram listesini çıkarır.
2. Filtered top-K useful phrase listesini çıkarır.
3. Manual labeling için JSON template üretir.
4. Etiketlenmiş JSON üzerinden Precision@K hesaplar.
5. Raw vs Filtered improvement metriğini döndürür.
"""

import os
import json


NGRAM_TYPES = ["bigram", "trigram", "quadgram"]


def ngram_tuple_to_text(ngram):
    """
    ('according', 'to') -> 'according to'
    """
    if isinstance(ngram, tuple):
        return " ".join(ngram)

    return str(ngram)


def build_phrase_evaluation_template(ngram_model, top_k=50):
    """
    Raw ve filtered phrase listeleri için manual labeling template üretir.

    Çıktı formatı:
    [
        {
            "id": 1,
            "list_type": "raw",
            "ngram_type": "bigram",
            "rank": 1,
            "phrase": "of the",
            "frequency": 120,
            "score": null,
            "is_useful": null
        },
        ...
    ]

    is_useful alanını sen elle true / false yapacaksın.
    """

    evaluation_items = []
    item_id = 1

    for ngram_type in NGRAM_TYPES:

        # 1. RAW TOP-K
        raw_items = ngram_model.get_top_ngrams(
            n_type=ngram_type,
            top_k=top_k
        )

        for rank, item in enumerate(raw_items, start=1):
            ngram, freq = item

            evaluation_items.append({
                "id": item_id,
                "list_type": "raw",
                "ngram_type": ngram_type,
                "rank": rank,
                "phrase": ngram_tuple_to_text(ngram),
                "frequency": freq,
                "score": None,
                "is_useful": None
            })

            item_id += 1

        # 2. FILTERED TOP-K
        filtered_items = ngram_model.get_useful_phrases(
            n_type=ngram_type,
            top_k=top_k,
            min_freq=2
        )

        for rank, item in enumerate(filtered_items, start=1):
            evaluation_items.append({
                "id": item_id,
                "list_type": "filtered",
                "ngram_type": ngram_type,
                "rank": rank,
                "phrase": item.get("phrase"),
                "frequency": item.get("frequency"),
                "score": item.get("score"),
                "is_useful": None
            })

            item_id += 1

    return evaluation_items


def save_phrase_evaluation_template(
    ngram_model,
    output_path,
    top_k=50
):
    """
    Manual labeling için JSON dosyası üretir.
    """

    items = build_phrase_evaluation_template(
        ngram_model=ngram_model,
        top_k=top_k
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    return {
        "output_path": output_path,
        "top_k": top_k,
        "total_items": len(items),
        "items_per_group": top_k,
        "groups": [
            "raw_bigram",
            "raw_trigram",
            "raw_quadgram",
            "filtered_bigram",
            "filtered_trigram",
            "filtered_quadgram"
        ]
    }


def load_labeled_phrases(label_path):
    """
    Etiketlenmiş phrase evaluation JSON dosyasını okur.
    """

    with open(label_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    return items


def validate_labels(items):
    """
    is_useful alanı true/false yapılmış mı kontrol eder.
    """

    unlabeled = [
        item for item in items
        if item.get("is_useful") not in [True, False]
    ]

    return {
        "is_complete": len(unlabeled) == 0,
        "unlabeled_count": len(unlabeled),
        "unlabeled_ids": [item.get("id") for item in unlabeled[:20]]
    }


def compute_precision(items):
    """
    Verilen item listesi için precision hesaplar.

    Precision = useful / total
    """

    total = len(items)

    if total == 0:
        return {
            "total": 0,
            "useful": 0,
            "not_useful": 0,
            "precision": 0,
            "precision_pct": "0.0%"
        }

    useful = sum(1 for item in items if item.get("is_useful") is True)
    not_useful = total - useful

    precision = useful / total

    return {
        "total": total,
        "useful": useful,
        "not_useful": not_useful,
        "precision": round(precision, 4),
        "precision_pct": f"{precision:.1%}"
    }


def evaluate_labeled_phrases(items):
    """
    Manual labeled phrase listesi üzerinden:
    - overall precision
    - raw vs filtered precision
    - ngram type bazlı precision
    - raw vs filtered improvement
    hesaplar.
    """

    validation = validate_labels(items)

    if not validation["is_complete"]:
        return {
            "error": "Bazı phrase'ler henüz etiketlenmemiş.",
            "validation": validation
        }

    results = {}

    # Overall
    results["overall"] = compute_precision(items)

    # Raw / Filtered overall
    raw_items = [
        item for item in items
        if item.get("list_type") == "raw"
    ]

    filtered_items = [
        item for item in items
        if item.get("list_type") == "filtered"
    ]

    results["raw_overall"] = compute_precision(raw_items)
    results["filtered_overall"] = compute_precision(filtered_items)

    raw_precision = results["raw_overall"]["precision"]
    filtered_precision = results["filtered_overall"]["precision"]

    results["filtering_improvement"] = {
        "raw_precision": raw_precision,
        "filtered_precision": filtered_precision,
        "absolute_gain": round(filtered_precision - raw_precision, 4),
        "absolute_gain_pct": f"{(filtered_precision - raw_precision):.1%}"
    }

    # By ngram type and list type
    by_type = {}

    for ngram_type in NGRAM_TYPES:
        by_type[ngram_type] = {}

        type_items = [
            item for item in items
            if item.get("ngram_type") == ngram_type
        ]

        type_raw_items = [
            item for item in type_items
            if item.get("list_type") == "raw"
        ]

        type_filtered_items = [
            item for item in type_items
            if item.get("list_type") == "filtered"
        ]

        by_type[ngram_type]["raw"] = compute_precision(type_raw_items)
        by_type[ngram_type]["filtered"] = compute_precision(type_filtered_items)

        raw_p = by_type[ngram_type]["raw"]["precision"]
        filtered_p = by_type[ngram_type]["filtered"]["precision"]

        by_type[ngram_type]["improvement"] = {
            "absolute_gain": round(filtered_p - raw_p, 4),
            "absolute_gain_pct": f"{(filtered_p - raw_p):.1%}"
        }

    results["by_type"] = by_type

    return results


def evaluate_labeled_file(label_path):
    """
    Etiketlenmiş JSON dosyasını okuyup precision sonuçlarını döndürür.
    """

    items = load_labeled_phrases(label_path)

    return evaluate_labeled_phrases(items)