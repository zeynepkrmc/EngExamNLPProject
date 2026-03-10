import pdfplumber
import re
import os
import glob

import nltk
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures

def turkce_satir_mi(satir):
    """
    Bir satırın Türkçe yönerge veya Türkçe çeviri şıkkı olup olmadığını kontrol eder.
    """
    satir_kucuk = satir.lower()
    
    # 1. ÖSYM Soru Yönergeleri ve Kapak Kelimeleri
    yonergeler = [
        "sorularda", "cümlede", "boş bırakılan", "uygun düşen", 
        "sözcük", "ifadeyi", "bulunuz", "parçada", "tamamlayan", 
        "anlamca", "en yakın", "karşılık gelen", "çevirisini", 
        "doğru", "akışı", "bozan", "cümleyi", "diyalogda", 
        "cevap", "soruya", "verilen", "seçeneği", "işaretleyiniz",
        "yerlere", "ya da", "diğer sayfaya geçiniz", "fen bilimleri", 
        "yökdil", "ösym", "yükseköğretim", "testi bitti", 
        "kontrol ediniz", "adayın dikkati", "kimlik numaranız"
    ]
    
    # 2. Türkçe'ye özgü harfler (Çeviri şıklarını anında yakalar)
    turkce_harfler = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']
    
    # 3. Sık kullanılan Türkçe kelimeler (Regex \b ile sadece tam kelime eşleşmesi arıyoruz)
    turkce_kelimeler_regex = r'\b(bir|ve|bu|için|ile|olarak|olan|gibi|daha|kadar|göre|değil|veya|ancak|ise)\b'
    
    # Kontroller
    for kelime in yonergeler:
        if kelime in satir_kucuk:
            return True
            
    for harf in turkce_harfler:
        if harf in satir_kucuk:
            return True
            
    if re.search(turkce_kelimeler_regex, satir_kucuk):
        return True
        
    return False

def sinav_metnini_hazirla(pdf_yolu):
    ham_metin = ""
    
    print(f"{os.path.basename(pdf_yolu)} okunuyor...")
    with pdfplumber.open(pdf_yolu) as pdf:
        for i, sayfa in enumerate(pdf.pages):
            sayfa_metni = sayfa.extract_text()
            
            if not sayfa_metni:
                continue
                
            # Kapak sayfası kontrolü
            kucuk_metin_tam = sayfa_metni.lower()
            if i == 0 and ("kimlik" in kucuk_metin_tam or "dikkat" in kucuk_metin_tam or "aday" in kucuk_metin_tam):
                print("  -> Kapak sayfası tespit edildi, atlanıyor...")
                continue
                
            # Sayfayı satırlara böl ve Türkçe olan satırları filtrele
            satirlar = sayfa_metni.split('\n')
            temiz_satirlar = []
            
            for satir in satirlar:
                # Eğer satır Türkçe DEĞİLSE listeye ekle
                if not turkce_satir_mi(satir):
                    temiz_satirlar.append(satir)
            
            # Kalan sadece İngilizce satırları birleştir
            ingilizce_metin = ' '.join(temiz_satirlar).lower()
            
            # İNGİLİZCE HARF FİLTRESİ (Sayılar, noktalamalar silinir, sadece a-z ve boşluklar kalır)
            temiz_metin = re.sub(r'[^a-z\s]', ' ', ingilizce_metin)
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
        print(f"  -> {os.path.basename(dosya)} dosyasından {len(dosya_tokenlari)} salt İngilizce kelime çıkarıldı.\n")
        
    print(f"Tüm işlem tamam! Toplam derlem (corpus) büyüklüğü: {len(tum_corpus_tokenlari)} kelime.")



# İlk defa çalıştırıyorsan NLTK'nin stop words kütüphanesini indirecektir
nltk.download('stopwords', quiet=True)

def en_sik_bigramlari_bul(token_listesi, top_n=30):
    print("\nNLTK ile akademik kalıplar (bi-gram) analiz ediliyor...")
    
    # İngilizce dolgu kelimeleri (stop words)
    stop_words = set(stopwords.words('english'))
    
    # PDF okuma hatalarından veya şıklardan kalan tek harfleri filtreye ekleyelim
    ekstra_stop_words = {'a', 'b', 'c', 'd', 'e', 'is', 'are', 'was', 'were', 'ngi', 'li', 'zce', 'fen', 'bi', 'mleri', 'th', 'nd', 'st', 'rd'} 

    stop_words = stop_words.union(ekstra_stop_words)

    # NLTK Collocation Finder objesini oluşturalım
    bigram_measures = BigramAssocMeasures()
    finder = BigramCollocationFinder.from_words(token_listesi)
    
    # FİLTRE 1: İki kelimesi de dolgu kelimesi (stop word) veya tek harf olanları yoksay
    # Ayrıca kelimelerden herhangi biri 1 harfliyse direkt eleyelim
    finder.apply_ngram_filter(lambda w1, w2: (w1 in stop_words and w2 in stop_words) or len(w1) < 2 or len(w2) < 2)
    
    # FİLTRE 2: Frekansı 3'ten az olan rastgele yan yana gelmeleri yoksay
    finder.apply_freq_filter(3)
    
    # En sık geçen bi-gram'ları frekanslarıyla birlikte alalım
    frekanslar = finder.ngram_fd.most_common(top_n)
    
    return frekanslar

# Oluşturduğumuz tum_corpus_tokenlari listesini NLTK fonksiyonuna gönderiyoruz
populer_bigramlar = en_sik_bigramlari_bul(tum_corpus_tokenlari, top_n=30)

print("\nYÖKDİL FEN BİLİMLERİ - EN SIK ÇIKAN 30 İKİLİ KALIP (BI-GRAM):\n" + "-"*60)
for i, (bigram, frekans) in enumerate(populer_bigramlar, 1):
    kalip = ' '.join(bigram)
    print(f"{i:02d}. {kalip:.<30} {frekans} kez kullanılmış")