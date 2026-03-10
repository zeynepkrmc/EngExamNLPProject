import pdfplumber
import re
import os
import glob

import nltk
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures

def sinav_metnini_hazirla(pdf_yolu):
    ham_metin = ""
    
    # Sınavlarda karşımıza çıkabilecek Türkçe ÖSYM şablonları
    turkce_sablonlar = [
        "diğer sayfaya geçiniz", "fen bilimleri", "yökdil", "ösym", 
        "yükseköğretim kurumları yabancı dil sınavı", "testi bitti", 
        "cevaplarınızı kontrol ediniz", "adayın dikkati", "kimlik numaranız"
    ]
    
    print(f"{os.path.basename(pdf_yolu)} okunuyor...")
    with pdfplumber.open(pdf_yolu) as pdf:
        for i, sayfa in enumerate(pdf.pages):
            sayfa_metni = sayfa.extract_text()
            
            if not sayfa_metni:
                continue
                
            kucuk_metin = sayfa_metni.lower()
            
            # KAPAK SAYFASI KONTROLÜ: İlk sayfada ÖSYM kapak kelimeleri varsa atla
            if i == 0 and ("kimlik" in kucuk_metin or "dikkat" in kucuk_metin or "aday" in kucuk_metin):
                print("  -> Kapak sayfası tespit edildi, atlanıyor...")
                continue
                
            # TÜRKÇE KALIP TEMİZLİĞİ
            for sablon in turkce_sablonlar:
                kucuk_metin = kucuk_metin.replace(sablon, " ")
            
            # İNGİLİZCE HARF FİLTRESİ (Sadece a-z ve boşluklar kalır)
            temiz_metin = re.sub(r'[^a-z\s]', ' ', kucuk_metin)
            temiz_metin = re.sub(r'\s+', ' ', temiz_metin).strip()
            
            ham_metin += temiz_metin + " "
            
    # Boş stringleri eleyerek tokenizasyon
    kelimeler = [k for k in ham_metin.split(' ') if k]
    
    return kelimeler

# Dosya yolu tanımlaması
dataset_klasoru = r"C:\Users\zeyne\GITHUB\NLP_Eng_Exam_Project\dataset"

# SADECE adı "YOKDIL" ile başlayan PDF dosyalarını bulma
arama_deseni = os.path.join(dataset_klasoru, "YOKDIL*.pdf")
pdf_dosyalari = glob.glob(arama_deseni)

tum_corpus_tokenlari = []

if not pdf_dosyalari:
    print(f"Uyarı: {dataset_klasoru} içinde 'YOKDIL' ile başlayan PDF dosyası bulunamadı!")
else:
    print(f"Toplam {len(pdf_dosyalari)} adet uygun PDF bulundu. İşlem başlıyor...\n")
    
    # Her bir PDF dosyasını sırayla işleme
    for dosya in pdf_dosyalari:
        dosya_tokenlari = sinav_metnini_hazirla(dosya)
        tum_corpus_tokenlari.extend(dosya_tokenlari)
        print(f"  -> {os.path.basename(dosya)} dosyasından {len(dosya_tokenlari)} kelime çıkarıldı.\n")
        
    print(f"Tüm işlem tamam! Toplam derlem (corpus) büyüklüğü: {len(tum_corpus_tokenlari)} kelime.")


# İlk çalıştırmada NLTK'nin stop words (dolgu kelimeleri) listesini indirmemiz gerekiyor
nltk.download('stopwords')

def en_sik_bigramlari_bul(token_listesi, top_n=20):
    print("\nNLTK ile akademik kalıplar (bi-gram) analiz ediliyor...")
    
    # İngilizce dolgu kelimelerini alalım
    stop_words = set(stopwords.words('english'))
    
    # Şık harfleri veya pdf okuma hatalarından kalan tek harfleri de filtreye ekleyelim
    ekstra_stop_words = {'a', 'b', 'c', 'd', 'e', 'is', 'are', 'was', 'were'} 
    stop_words = stop_words.union(ekstra_stop_words)

    # NLTK Collocation Finder objesini oluşturalım
    bigram_measures = BigramAssocMeasures()
    finder = BigramCollocationFinder.from_words(token_listesi)
    
    # FİLTRE 1: İki kelimesi de dolgu kelimesi (stop word) olanları yoksay
    # Yani "of the" elenir, ama "associated with" (with dolgu olsa bile associated olmadığı için) kalır.
    finder.apply_ngram_filter(lambda w1, w2: w1 in stop_words and w2 in stop_words)
    
    # FİLTRE 2: Frekansı 3'ten az olan rastgele yan yana gelmeleri yoksay
    finder.apply_freq_filter(3)
    
    # En sık geçen bi-gram'ları frekanslarıyla birlikte alalım
    frekanslar = finder.ngram_fd.most_common(top_n)
    
    return frekanslar

# Oluşturduğumuz tum_corpus_tokenlari listesini fonksiyona gönderiyoruz
populer_bigramlar = en_sik_bigramlari_bul(tum_corpus_tokenlari, top_n=30)

print("\nYÖKDİL Fen Bilimleri - En Sık Çıkan 30 İkili Kalıp:\n" + "-"*50)
for i, (bigram, frekans) in enumerate(populer_bigramlar, 1):
    kalip = ' '.join(bigram)
    print(f"{i}. {kalip:.<30} {frekans} kez")