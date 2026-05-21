"""
ngram_model.py — Corpus'tan bigram, trigram ve quadgram frekans sözlükleri oluşturur.
Hızlı arama için collections.Counter tabanlı sade yapı.
"""

from collections import Counter


class NgramModel:
    """N-gram frekans sözlüklerini tutan ve sorgulatan model."""

    def __init__(self, tokens=None):
        self.tokens = tokens or []
        self.unigrams = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.quadgrams = Counter()

        if self.tokens:
            self._build()

    def _build(self):
        """Corpus token listesinden tüm n-gram sözlüklerini oluşturur."""
        n = len(self.tokens)
        print(f"N-gram sözlükleri oluşturuluyor ({n} token)...")

        # Unigram (tekli kelime frekansları)
        self.unigrams = Counter(self.tokens)

        for i in range(n - 1):
            self.bigrams[tuple(self.tokens[i:i + 2])] += 1

        for i in range(n - 2):
            self.trigrams[tuple(self.tokens[i:i + 3])] += 1

        for i in range(n - 3):
            self.quadgrams[tuple(self.tokens[i:i + 4])] += 1

        print(f"  -> Unigram : {len(self.unigrams):,} benzersiz")
        print(f"  -> Bigram  : {len(self.bigrams):,} benzersiz")
        print(f"  -> Trigram : {len(self.trigrams):,} benzersiz")
        print(f"  -> Quadgram: {len(self.quadgrams):,} benzersiz")

    def get_word_freq(self, word):
        """Tekli kelime frekansını döndürür."""
        return self.unigrams.get(word, 0)

    def get_bigram_freq(self, w1, w2):
        return self.bigrams.get((w1, w2), 0)

    def get_trigram_freq(self, w1, w2, w3):
        return self.trigrams.get((w1, w2, w3), 0)

    def get_quadgram_freq(self, w1, w2, w3, w4):
        return self.quadgrams.get((w1, w2, w3, w4), 0)

    def get_top_ngrams(self, n_type='bigram', top_k=20):
        """En sık n-gram'ları döndürür."""
        source = {
            'bigram': self.bigrams,
            'trigram': self.trigrams,
            'quadgram': self.quadgrams
        }.get(n_type, self.bigrams)

        return source.most_common(top_k)

    def stats(self):
        """Model istatistiklerini döndürür."""
        return {
            'corpus_size': len(self.tokens),
            'unique_tokens': len(self.unigrams),
            'unique_bigrams': len(self.bigrams),
            'unique_trigrams': len(self.trigrams),
            'unique_quadgrams': len(self.quadgrams),
            'total_bigram_freq': sum(self.bigrams.values()),
            'total_trigram_freq': sum(self.trigrams.values()),
            'total_quadgram_freq': sum(self.quadgrams.values()),
        }


def analyze_text(text, model):
    """
    Serbest bir metni analiz eder: kelime sayısı, n-gram istatistikleri,
    metindeki en sık geçen kalıplar.
    """
    import re
    # Metni tokenize et
    clean = re.sub(r'[^a-z\s]', ' ', text.lower())
    tokens = [t for t in clean.split() if t]

    if not tokens:
        return {'error': 'Metin boş veya geçersiz.'}

    # Metindeki bi/tri/quad-gramları say
    text_bigrams = Counter()
    text_trigrams = Counter()
    text_quadgrams = Counter()

    for i in range(len(tokens) - 1):
        bg = tuple(tokens[i:i + 2])
        text_bigrams[bg] += 1

    for i in range(len(tokens) - 2):
        tg = tuple(tokens[i:i + 3])
        text_trigrams[tg] += 1

    for i in range(len(tokens) - 3):
        qg = tuple(tokens[i:i + 4])
        text_quadgrams[qg] += 1

    # Corpus'taki frekanslarla eşleştir
    corpus_matches_bi = []
    for bg, cnt in text_bigrams.most_common(30):
        freq = model.get_bigram_freq(*bg)
        if freq > 0:
            corpus_matches_bi.append({
                'ngram': ' '.join(bg),
                'text_freq': cnt,
                'corpus_freq': freq
            })

    corpus_matches_tri = []
    for tg, cnt in text_trigrams.most_common(30):
        freq = model.get_trigram_freq(*tg)
        if freq > 0:
            corpus_matches_tri.append({
                'ngram': ' '.join(tg),
                'text_freq': cnt,
                'corpus_freq': freq
            })

    corpus_matches_quad = []
    for qg, cnt in text_quadgrams.most_common(20):
        freq = model.get_quadgram_freq(*qg)
        if freq > 0:
            corpus_matches_quad.append({
                'ngram': ' '.join(qg),
                'text_freq': cnt,
                'corpus_freq': freq
            })

    return {
        'word_count': len(tokens),
        'unique_words': len(set(tokens)),
        'sentence_count': text.count('.') + text.count('!') + text.count('?'),
        'bigram_matches': corpus_matches_bi[:10],
        'trigram_matches': corpus_matches_tri[:10],
        'quadgram_matches': corpus_matches_quad[:10],
        'total_bigram_types': len(text_bigrams),
        'total_trigram_types': len(text_trigrams),
        'total_quadgram_types': len(text_quadgrams),
    }
