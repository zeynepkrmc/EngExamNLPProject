import nltk
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder, QuadgramCollocationFinder

# NLTK kütüphaneleri (Zaten inmişse sessizce geçer)
nltk.download('stopwords', quiet=True)

def kapsamli_ngram_analizi(token_listesi, top_n=15):
    print("\nNLTK ile Çoklu N-Gram (Bi-gram, Tri-gram, Quad-gram) Analizi Başlatılıyor...")
    
    stop_words = set(stopwords.words('english'))
    # Önceki temizlikten kalan gürültüler
    ekstra_stop_words = {'b', 'c', 'd', 'e', 'is', 'are', 'was', 'were', 'ngi', 'li', 'zce', 'fen', 'bi', 'mleri', 'th', 'nd', 'st', 'rd'} 
    stop_words = stop_words.union(ekstra_stop_words)
    
    # KÜÇÜK BİR DÜZELTME: İngilizcedeki 'a' kelimesini (örn: "a number of") korumak için, 
    # 1 harfli kelimeleri elerken 'a' yı istisna tutuyoruz.
    def gürültü_mü(kelime):
        return len(kelime) < 2 and kelime != 'a'

    # --- 1. BI-GRAM (İKİLİ KALIPLAR) ---
    bi_finder = BigramCollocationFinder.from_words(token_listesi)
    bi_finder.apply_ngram_filter(lambda w1, w2: (w1 in stop_words and w2 in stop_words) or gürültü_mü(w1) or gürültü_mü(w2))
    bi_finder.apply_freq_filter(3)
    bigramlar = bi_finder.ngram_fd.most_common(top_n)
    
    # --- 2. TRI-GRAM (ÜÇLÜ KALIPLAR) ---
    tri_finder = TrigramCollocationFinder.from_words(token_listesi)
    # Bütün kelimeleri dolgu kelimesi (stop word) olanları veya gürültü içerenleri ele
    tri_finder.apply_ngram_filter(lambda w1, w2, w3: (w1 in stop_words and w2 in stop_words and w3 in stop_words) or any(gürültü_mü(w) for w in [w1, w2, w3]))
    tri_finder.apply_freq_filter(3)
    trigramlar = tri_finder.ngram_fd.most_common(top_n)
    
    # --- 3. QUAD-GRAM (DÖRTLÜ KALIPLAR) ---
    quad_finder = QuadgramCollocationFinder.from_words(token_listesi)
    quad_finder.apply_ngram_filter(lambda w1, w2, w3, w4: (w1 in stop_words and w2 in stop_words and w3 in stop_words and w4 in stop_words) or any(gürültü_mü(w) for w in [w1, w2, w3, w4]))
    quad_finder.apply_freq_filter(2) # 4'lü kalıplar daha nadir olduğu için frekans limitini 2'ye çektik
    quadgramlar = quad_finder.ngram_fd.most_common(top_n)
    
    return bigramlar, trigramlar, quadgramlar

# Analizi çalıştır (tum_corpus_tokenlari listesini PDF okuma fonksiyonundan almıştık)
populer_bi, populer_tri, populer_quad = kapsamli_ngram_analizi(tum_corpus_tokenlari, top_n=10)

# ----------------- ÇIKTILARI EKRANA YAZDIRMA -----------------
print("\n" + "="*50)
print("1. EN SIK ÇIKAN İKİLİ KALIPLAR (BI-GRAM)")
print("="*50)
for i, (kalip, frekans) in enumerate(populer_bi, 1):
    print(f"{i:02d}. {' '.join(kalip):.<30} {frekans} kez")

print("\n" + "="*50)
print("2. EN SIK ÇIKAN ÜÇLÜ KALIPLAR (TRI-GRAM)")
print("="*50)
for i, (kalip, frekans) in enumerate(populer_tri, 1):
    print(f"{i:02d}. {' '.join(kalip):.<30} {frekans} kez")

print("\n" + "="*50)
print("3. EN SIK ÇIKAN DÖRTLÜ KALIPLAR (QUAD-GRAM)")
print("="*50)
for i, (kalip, frekans) in enumerate(populer_quad, 1):
    print(f"{i:02d}. {' '.join(kalip):.<30} {frekans} kez")