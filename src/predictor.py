"""
predictor.py — N-gram tabanlı cloze (boşluk doldurma) soru çözücü.
Geliştirilmiş versiyon:
  - Log-frekans skorlama (aşırı sık bigram baskınlığını azaltır)
  - Unigram fallback (hiç n-gram eşleşmesi yoksa kelime frekansı)
  - Çoklu kelimeli şıklar için iç n-gram analizi
  - Optimize edilmiş ağırlıklar
"""

import re
import math


class ClozePredictor:
    """N-gram frekanslarına dayalı boşluk doldurma sorusu çözücü."""

    def __init__(self, ngram_model):
        self.model = ngram_model
        # Optimize edilmiş ağırlıklar
        self.weights = {
            'unigram': 0.3,
            'bigram': 1.0,
            'trigram': 4.0,
            'quadgram': 7.0
        }

    def _tokenize(self, text):
        """Metni küçük harfli tokenlara ayırır."""
        clean = re.sub(r'[^a-z\s]', ' ', text.lower())
        return [t for t in clean.split() if t]

    def _log_freq(self, freq):
        """Log-frekans: Aşırı sık kalıpların baskınlığını azaltır."""
        if freq <= 0:
            return 0.0
        return math.log2(1 + freq)

    def score_option(self, left_context, right_context, option):
        """
        Bir şıkkı bağlamla birleştirip n-gram sözlüklerinde arar.
        Sol bağlam + şık + sağ bağlam etrafındaki tüm n-gram'ları kontrol eder.
        Skor detaylarını (hangi n-gram seviyesinden ne kadar puan geldi) da döndürür.
        """
        left_tokens = self._tokenize(left_context)
        right_tokens = self._tokenize(right_context)
        option_token = self._tokenize(option)

        if not option_token:
            return 0.0, {'unigram': 0, 'bigram': 0, 'trigram': 0, 'quadgram': 0}

        opt = option_token

        score = 0.0
        breakdown = {'unigram': 0.0, 'bigram': 0.0, 'trigram': 0.0, 'quadgram': 0.0}

        # ─── UNIGRAM SKORLARI (fallback) ───
        # Şık kelimelerinin corpus'taki frekansı
        unigram_score = 0.0
        for word in opt:
            unigram_score += self._log_freq(self.model.get_word_freq(word))
        # Kelime sayısına göre normalize et
        if len(opt) > 0:
            unigram_score /= len(opt)
        unigram_contribution = unigram_score * self.weights['unigram']
        score += unigram_contribution
        breakdown['unigram'] = round(unigram_contribution, 4)

        # ─── BIGRAM SKORLARI ───
        bigram_score = 0.0

        # (son_sol_kelime, şık_ilk_kelime)
        if left_tokens:
            bigram_score += self._log_freq(
                self.model.get_bigram_freq(left_tokens[-1], opt[0])
            )

        # (şık_son_kelime, ilk_sağ_kelime)
        if right_tokens:
            bigram_score += self._log_freq(
                self.model.get_bigram_freq(opt[-1], right_tokens[0])
            )

        # Çoklu kelime şıklar için iç bigram'lar
        if len(opt) > 1:
            for i in range(len(opt) - 1):
                bigram_score += self._log_freq(
                    self.model.get_bigram_freq(opt[i], opt[i + 1])
                )

        bigram_contribution = bigram_score * self.weights['bigram']
        score += bigram_contribution
        breakdown['bigram'] = round(bigram_contribution, 4)

        # ─── TRIGRAM SKORLARI ───
        trigram_score = 0.0

        # (sol[-2], sol[-1], şık[0])
        if len(left_tokens) >= 2:
            trigram_score += self._log_freq(
                self.model.get_trigram_freq(left_tokens[-2], left_tokens[-1], opt[0])
            )

        # (sol[-1], şık[0], sağ[0]) — şık tek kelimeyse
        if left_tokens and right_tokens and len(opt) == 1:
            trigram_score += self._log_freq(
                self.model.get_trigram_freq(left_tokens[-1], opt[0], right_tokens[0])
            )

        # (şık[-1], sağ[0], sağ[1])
        if len(right_tokens) >= 2:
            trigram_score += self._log_freq(
                self.model.get_trigram_freq(opt[-1], right_tokens[0], right_tokens[1])
            )

        # Çoklu kelime şıklar: sol bağlam + şık iç trigram'ları
        if left_tokens and len(opt) >= 2:
            trigram_score += self._log_freq(
                self.model.get_trigram_freq(left_tokens[-1], opt[0], opt[1])
            )

        if len(opt) >= 2 and right_tokens:
            trigram_score += self._log_freq(
                self.model.get_trigram_freq(opt[-2], opt[-1], right_tokens[0])
            )

        # İç trigram'lar (3+ kelimeli şıklar)
        if len(opt) >= 3:
            for i in range(len(opt) - 2):
                trigram_score += self._log_freq(
                    self.model.get_trigram_freq(opt[i], opt[i + 1], opt[i + 2])
                )

        trigram_contribution = trigram_score * self.weights['trigram']
        score += trigram_contribution
        breakdown['trigram'] = round(trigram_contribution, 4)

        # ─── QUADGRAM SKORLARI ───
        quadgram_score = 0.0

        # (sol[-3], sol[-2], sol[-1], şık[0])
        if len(left_tokens) >= 3:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    left_tokens[-3], left_tokens[-2], left_tokens[-1], opt[0]
                )
            )

        # (sol[-2], sol[-1], şık[0], sağ[0])
        if len(left_tokens) >= 2 and right_tokens and len(opt) == 1:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    left_tokens[-2], left_tokens[-1], opt[0], right_tokens[0]
                )
            )

        # (sol[-1], şık[0], sağ[0], sağ[1])
        if left_tokens and len(right_tokens) >= 2 and len(opt) == 1:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    left_tokens[-1], opt[0], right_tokens[0], right_tokens[1]
                )
            )

        # (şık[-1], sağ[0], sağ[1], sağ[2])
        if len(right_tokens) >= 3:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    opt[-1], right_tokens[0], right_tokens[1], right_tokens[2]
                )
            )

        # Çoklu kelime şıklar: sınır quadgram'ları
        if len(left_tokens) >= 2 and len(opt) >= 2:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    left_tokens[-2], left_tokens[-1], opt[0], opt[1]
                )
            )

        if left_tokens and len(opt) >= 2 and right_tokens:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    left_tokens[-1], opt[0], opt[1], right_tokens[0]
                ) if len(opt) == 2 else 0
            )

        if len(opt) >= 2 and len(right_tokens) >= 2:
            quadgram_score += self._log_freq(
                self.model.get_quadgram_freq(
                    opt[-2], opt[-1], right_tokens[0], right_tokens[1]
                )
            )

        # İç quadgram'lar (4+ kelimeli şıklar)
        if len(opt) >= 4:
            for i in range(len(opt) - 3):
                quadgram_score += self._log_freq(
                    self.model.get_quadgram_freq(opt[i], opt[i+1], opt[i+2], opt[i+3])
                )

        quadgram_contribution = quadgram_score * self.weights['quadgram']
        score += quadgram_contribution
        breakdown['quadgram'] = round(quadgram_contribution, 4)

        # Normalizasyon: PDF okuma hatalarından kaynaklı aşırı uzun şıkları cezalandır
        # Skor, şıkkın kelime sayısına bölünerek normalize edilir
        norm_factor = max(1, len(opt))
        score = score / norm_factor
        for k in breakdown:
            breakdown[k] = round(breakdown[k] / norm_factor, 4)

        return score, breakdown

    def predict(self, question):
        """
        Bir cloze sorusu için tahmin yapar.
        Döndürür: (tahmin_harfi, {harf: skor, ...}, {harf: breakdown, ...})
        """
        scores = {}
        breakdowns = {}

        for letter, option_text in question['options'].items():
            score, breakdown = self.score_option(
                question['left_context'],
                question['right_context'],
                option_text
            )
            scores[letter] = score
            breakdowns[letter] = breakdown

        # En yüksek skora sahip şıkkı seç
        best = max(scores, key=scores.get)

        return best, scores, breakdowns

    def evaluate(self, test_set):
        """
        Test setini çözer ve accuracy hesaplar.
        Döndürür: {accuracy, correct, total, results: [...], ngram_contribution: {...}}
        """
        correct = 0
        total = 0
        results = []

        # N-gram katkı istatistikleri
        total_contribution = {'unigram': 0.0, 'bigram': 0.0, 'trigram': 0.0, 'quadgram': 0.0}
        correct_contribution = {'unigram': 0.0, 'bigram': 0.0, 'trigram': 0.0, 'quadgram': 0.0}

        # Şık dağılımı analizi
        predicted_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        correct_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}

        for q in test_set:
            if not q.get('correct_answer'):
                continue

            predicted, scores, breakdowns = self.predict(q)
            is_correct = (predicted == q['correct_answer'])

            if is_correct:
                correct += 1
            total += 1

            # Seçilen şıkkın katkı dağılımı
            if predicted in breakdowns:
                for key in total_contribution:
                    total_contribution[key] += breakdowns[predicted].get(key, 0)
                    if is_correct:
                        correct_contribution[key] += breakdowns[predicted].get(key, 0)

            # Şık dağılımı
            if predicted in predicted_distribution:
                predicted_distribution[predicted] += 1
            if q['correct_answer'] in correct_distribution:
                correct_distribution[q['correct_answer']] += 1

            results.append({
                'id': q['id'],
                'question': q['question_text'][:80] + '...' if len(q.get('question_text', '')) > 80 else q.get('question_text', ''),
                'predicted': predicted,
                'correct': q['correct_answer'],
                'is_correct': is_correct,
                'scores': {k: round(v, 2) for k, v in scores.items()},
                'breakdown': breakdowns.get(predicted, {})
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
            'results': results,
            'ngram_contribution': {
                k: round(v, 2) for k, v in total_contribution.items()
            },
            'correct_ngram_contribution': {
                k: round(v, 2) for k, v in correct_contribution.items()
            },
            'predicted_distribution': predicted_distribution,
            'correct_distribution': correct_distribution
        }
