"""
predictor.py — N-gram tabanlı cloze (boşluk doldurma) soru çözücü.
Ağırlıklı skorlama: Bigram=1, Trigram=3, Quadgram=5
"""

import re


class ClozePredictor:
    """N-gram frekanslarına dayalı boşluk doldurma sorusu çözücü."""

    def __init__(self, ngram_model):
        self.model = ngram_model
        # Ağırlıklar: Daha uzun n-gram eşleşmelerine daha yüksek puan
        self.weights = {
            'bigram': 1.0,
            'trigram': 3.0,
            'quadgram': 5.0
        }

    def _tokenize(self, text):
        """Metni küçük harfli tokenlara ayırır."""
        clean = re.sub(r'[^a-z\s]', ' ', text.lower())
        return [t for t in clean.split() if t]

    def score_option(self, left_context, right_context, option):
        """
        Bir şıkkı bağlamla birleştirip n-gram sözlüklerinde arar.
        Sol bağlam + şık + sağ bağlam etrafındaki tüm n-gram'ları kontrol eder.
        """
        left_tokens = self._tokenize(left_context)
        right_tokens = self._tokenize(right_context)
        option_token = self._tokenize(option)

        if not option_token:
            return 0.0

        # Şık birden fazla kelimeden oluşabilir, hepsini dahil et
        opt = option_token  # örn: ["carried", "out"] veya ["effective"]

        score = 0.0

        # ─── BIGRAM SKORLARI ───
        # (son_sol_kelime, şık_ilk_kelime)
        if left_tokens:
            freq = self.model.get_bigram_freq(left_tokens[-1], opt[0])
            score += freq * self.weights['bigram']

        # (şık_son_kelime, ilk_sağ_kelime)
        if right_tokens:
            freq = self.model.get_bigram_freq(opt[-1], right_tokens[0])
            score += freq * self.weights['bigram']

        # ─── TRIGRAM SKORLARI ───
        # (sol[-2], sol[-1], şık[0])
        if len(left_tokens) >= 2:
            freq = self.model.get_trigram_freq(left_tokens[-2], left_tokens[-1], opt[0])
            score += freq * self.weights['trigram']

        # (sol[-1], şık[0], sağ[0])  — şık tek kelimeyse
        if left_tokens and right_tokens and len(opt) == 1:
            freq = self.model.get_trigram_freq(left_tokens[-1], opt[0], right_tokens[0])
            score += freq * self.weights['trigram']

        # (şık[-1], sağ[0], sağ[1])
        if len(right_tokens) >= 2:
            freq = self.model.get_trigram_freq(opt[-1], right_tokens[0], right_tokens[1])
            score += freq * self.weights['trigram']

        # ─── QUADGRAM SKORLARI ───
        # (sol[-3], sol[-2], sol[-1], şık[0])
        if len(left_tokens) >= 3:
            freq = self.model.get_quadgram_freq(
                left_tokens[-3], left_tokens[-2], left_tokens[-1], opt[0]
            )
            score += freq * self.weights['quadgram']

        # (sol[-2], sol[-1], şık[0], sağ[0])
        if len(left_tokens) >= 2 and right_tokens and len(opt) == 1:
            freq = self.model.get_quadgram_freq(
                left_tokens[-2], left_tokens[-1], opt[0], right_tokens[0]
            )
            score += freq * self.weights['quadgram']

        # (sol[-1], şık[0], sağ[0], sağ[1])
        if left_tokens and len(right_tokens) >= 2 and len(opt) == 1:
            freq = self.model.get_quadgram_freq(
                left_tokens[-1], opt[0], right_tokens[0], right_tokens[1]
            )
            score += freq * self.weights['quadgram']

        # (şık[-1], sağ[0], sağ[1], sağ[2])
        if len(right_tokens) >= 3:
            freq = self.model.get_quadgram_freq(
                opt[-1], right_tokens[0], right_tokens[1], right_tokens[2]
            )
            score += freq * self.weights['quadgram']

        return score

    def predict(self, question):
        """
        Bir cloze sorusu için tahmin yapar.
        Döndürür: (tahmin_harfi, {harf: skor, ...})
        """
        scores = {}

        for letter, option_text in question['options'].items():
            scores[letter] = self.score_option(
                question['left_context'],
                question['right_context'],
                option_text
            )

        # En yüksek skora sahip şıkkı seç
        best = max(scores, key=scores.get)

        # Tüm skorlar 0 ise (hiçbir n-gram eşleşmesi yok), A döndür
        if all(s == 0 for s in scores.values()):
            best = 'A'

        return best, scores

    def evaluate(self, test_set):
        """
        Test setini çözer ve accuracy hesaplar.
        Döndürür: {accuracy, correct, total, results: [...]}
        """
        correct = 0
        total = 0
        results = []

        for q in test_set:
            if not q.get('correct_answer'):
                continue

            predicted, scores = self.predict(q)
            is_correct = (predicted == q['correct_answer'])

            if is_correct:
                correct += 1
            total += 1

            results.append({
                'id': q['id'],
                'question': q['question_text'][:80] + '...' if len(q.get('question_text', '')) > 80 else q.get('question_text', ''),
                'predicted': predicted,
                'correct': q['correct_answer'],
                'is_correct': is_correct,
                'scores': {k: round(v, 2) for k, v in scores.items()}
            })

        accuracy = correct / total if total > 0 else 0

        # Konsola özet yazdır
        print(f"\n{'='*50}")
        print(f"MODEL DEĞERLENDİRME SONUÇLARI")
        print(f"{'='*50}")
        print(f"Toplam Soru : {total}")
        print(f"Doğru       : {correct}")
        print(f"Yanlış      : {total - correct}")
        print(f"Accuracy    : {accuracy:.1%}")
        print(f"{'='*50}")

        # Hatalı tahminleri göster
        wrong = [r for r in results if not r['is_correct']]
        if wrong:
            print(f"\nHATALI TAHMİNLER ({len(wrong)} adet):")
            print('-' * 50)
            for r in wrong[:10]:
                print(f"  Soru {r['id']}: {r['question']}")
                print(f"    Tahmin: {r['predicted']} | Doğru: {r['correct']} | Skorlar: {r['scores']}")

        return {
            'accuracy': round(accuracy, 4),
            'accuracy_pct': f"{accuracy:.1%}",
            'correct': correct,
            'total': total,
            'results': results
        }
