"""
app.py — YÖKDİL NLP Projesi Flask Backend
Warm-up: Uygulama başlarken model RAM'e yüklenir.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import sys

# src modülünü import edebilmek için
sys.path.insert(0, os.path.dirname(__file__))

from src.corpus_builder import build_corpus
from src.ngram_model import NgramModel, analyze_text
from src.predictor import ClozePredictor

app = Flask(__name__)

# ── Yollar ──
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEST_SET_PATH = os.path.join(BASE_DIR, 'test_data', 'cloze_test_set.json')

# ── WARM-UP: Model Yükleme ──
print("\n" + "=" * 60)
print("  YÖKDİL NLP MODELİ YÜKLENIYOR (Warm-up)")
print("=" * 60)

# 1. Corpus oluştur
corpus_tokens = build_corpus(DATA_DIR)

# 2. N-gram sözlüklerini oluştur
ngram_model = NgramModel(corpus_tokens)

# 3. Tahmin motorunu başlat
predictor = ClozePredictor(ngram_model)

# 4. Test setini yükle
test_set = []
if os.path.exists(TEST_SET_PATH):
    with open(TEST_SET_PATH, 'r', encoding='utf-8') as f:
        test_set = json.load(f)
    print(f"\nTest seti yüklendi: {len(test_set)} soru")
else:
    print(f"\nUYARI: Test seti bulunamadı: {TEST_SET_PATH}")
    print("Önce question_extractor.py'yi çalıştırın!")

print("\n" + "=" * 60)
print("  MODEL HAZIR! Sunucu başlatılıyor...")
print("=" * 60 + "\n")


# ── ROUTES ──

@app.route('/')
def index():
    """Ana sayfa — Frontend arayüzünü render eder."""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    Serbest metin analizi.
    POST body: {"text": "..."}
    Döndürür: Kelime sayısı, n-gram istatistikleri, corpus eşleşmeleri
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Lütfen "text" alanı gönderin.'}), 400

    text = data['text'].strip()
    if not text:
        return jsonify({'error': 'Metin boş olamaz.'}), 400

    result = analyze_text(text, ngram_model)
    return jsonify(result)


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Tek bir cloze sorusu için tahmin.
    POST body: {"question_id": 1} veya tam soru objesi
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Geçersiz istek.'}), 400

    # question_id ile test setinden soru çek
    if 'question_id' in data:
        q_id = data['question_id']
        question = next((q for q in test_set if q['id'] == q_id), None)
        if not question:
            return jsonify({'error': f'Soru bulunamadı: {q_id}'}), 404
    else:
        # Doğrudan soru objesi gönderilmiş
        question = data

    predicted, scores, breakdowns = predictor.predict(question)

    return jsonify({
        'question_id': question.get('id'),
        'question_text': question.get('question_text', ''),
        'predicted_answer': predicted,
        'correct_answer': question.get('correct_answer'),
        'is_correct': predicted == question.get('correct_answer') if question.get('correct_answer') else None,
        'scores': {k: round(v, 2) for k, v in scores.items()},
        'options': question.get('options', {}),
        'breakdown': breakdowns.get(predicted, {})
    })


@app.route('/api/test', methods=['GET'])
def api_test():
    """
    Tüm test setini çözüp sonuçları döndürür.
    GET /api/test
    """
    if not test_set:
        return jsonify({'error': 'Test seti yüklenmemiş.'}), 404

    evaluation = predictor.evaluate(test_set)
    return jsonify(evaluation)


@app.route('/api/questions', methods=['GET'])
def api_questions():
    """
    Test setindeki soruları listeler (frontend için).
    GET /api/questions
    """
    # Cevap anahtarını gizle (kullanıcı görmeden çözsün)
    safe_questions = []
    for q in test_set:
        safe_q = {
            'id': q['id'],
            'source': q.get('source', ''),
            'question_text': q.get('question_text', ''),
            'left_context': q.get('left_context', ''),
            'right_context': q.get('right_context', ''),
            'options': q.get('options', {})
        }
        safe_questions.append(safe_q)

    return jsonify({
        'total': len(safe_questions),
        'questions': safe_questions
    })


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Model istatistiklerini döndürür."""
    stats = ngram_model.stats()
    stats['test_set_size'] = len(test_set)
    return jsonify(stats)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
