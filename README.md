# 🎓 YÖKDİL NLP — N-Gram Tabanlı Boşluk Doldurma Tahmin Sistemi

**Akademik İngilizce sınav metinlerinden oluşturulan corpus üzerinde N-gram tabanlı cloze (boşluk doldurma) sorusu çözme algoritması ve interaktif web arayüzü.**

> 📚 Doğal Dil İşleme (NLP) Dersi Projesi

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Mimari ve Teknolojiler](#-mimari-ve-teknolojiler)
- [Proje Yapısı](#-proje-yapısı)
- [Kurulum](#-kurulum)
- [Çalıştırma](#-çalıştırma)
- [API Referansı](#-api-referansı)
- [Algoritma Detayları](#-algoritma-detayları)
- [Web Arayüzü](#-web-arayüzü)

---

## 🔍 Proje Hakkında

Bu proje, YÖKDİL (Yükseköğretim Kurumları Yabancı Dil Sınavı) Fen Bilimleri İngilizce PDF'lerinden otomatik olarak:

1. **Corpus (derlem) oluşturur** — PDF'lerden İngilizce metinleri çıkarır, Türkçe satırları filtreler
2. **N-gram frekans sözlükleri üretir** — Unigram, Bigram, Trigram ve Quadgram
3. **Boşluk doldurma sorularını çıkarır** — Regex ile cloze sorularını ve cevap anahtarını parse eder
4. **Ağırlıklı N-gram skorlama ile tahmin yapar** — Her şıkkı bağlamla birleştirip n-gram eşleşmelerini arar
5. **Sonuçları interaktif web arayüzünde sunar** — Flask backend + Bootstrap frontend

### Motivasyon

Projenin amacı, klasik istatistiksel NLP yöntemlerinden biri olan **N-gram dil modelleri**nin, çoktan seçmeli boşluk doldurma soruları üzerindeki başarısını ölçmek ve görselleştirmektir. Derin öğrenme modelleri kullanılmadan, yalnızca kelime dizilimlerinin frekans bilgisiyle ne kadar doğru tahmin yapılabileceği araştırılmıştır.

---

## 🏗 Mimari ve Teknolojiler

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **PDF İşleme** | `pdfplumber` | YÖKDİL PDF'lerinden metin çıkarma |
| **NLP Motor** | Python (stdlib) | N-gram frekans analizi, ağırlıklı skorlama |
| **Backend** | Flask | REST API, warm-up ile model yükleme |
| **Frontend** | HTML + CSS + JS | Bootstrap 5, Chart.js, glassmorphism dark tema |
| **Veri Formatı** | JSON | Test seti ve API yanıtları |

---

## 📁 Proje Yapısı

```
EngExamNLPProject/
├── app.py                          # Flask backend (ana uygulama)
├── requirements.txt                # Python bağımlılıkları
├── README.md                       # Bu dosya
│
├── src/                            # Kaynak kod modülleri
│   ├── __init__.py
│   ├── corpus_builder.py           # PDF → Corpus oluşturma
│   ├── ngram_model.py              # N-gram sözlük oluşturma ve sorgulama
│   ├── predictor.py                # Cloze soru çözücü (ağırlıklı skorlama)
│   └── question_extractor.py       # PDF → JSON soru çıkarma
│
├── data/                           # YÖKDİL PDF dosyaları
│   ├── YOKDIL1_Ingilizce_fen.pdf
│   ├── YOKDIL1_Ingilizce_fen (1).pdf
│   ├── YOKDIL2_Ingilizce_fen.pdf
│   ├── YOKDIL2_Ingilizce_fen (1).pdf
│   └── YOKDIL_Ingilizce_fen.pdf
│
├── test_data/                      # Çıkarılmış test seti
│   └── cloze_test_set.json         # 50+ boşluk doldurma sorusu (cevaplı)
│
├── templates/                      # Flask HTML şablonları
│   └── index.html                  # Ana sayfa
│
├── static/                         # Statik dosyalar
│   ├── css/
│   │   └── style.css               # Glassmorphism dark tema
│   └── js/
│       └── app.js                  # Frontend mantığı ve Chart.js grafikleri
│
└── _archive/                       # Eski prototip scriptler (referans için)
    ├── file.py
    ├── file2.py
    └── 3garm4gram.py
```

---

## 🚀 Kurulum

### Gereksinimler

- **Python 3.9+**
- **pip** (Python paket yöneticisi)

### Adım Adım Kurulum

```bash
# 1. Projeyi klonlayın
git clone https://github.com/zeynepkrmc/EngExamNLPProject.git
cd EngExamNLPProject

# 2. Sanal ortam oluşturun
python -m venv venv

# 3. Sanal ortamı etkinleştirin
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# 4. Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### PDF Dosyaları

YÖKDİL Fen Bilimleri İngilizce PDF'lerini `data/` klasörüne yerleştirin. Dosya adları `YOKDIL` ile başlamalıdır.

### Test Setini Oluşturma (İlk Kurulum)

Eğer `test_data/cloze_test_set.json` dosyası yoksa:

```bash
python -c "from src.question_extractor import build_test_set; build_test_set()"
```

Bu komut PDF'lerden boşluk doldurma sorularını çıkarır ve cevap anahtarını eşleştirir.

---

## ▶️ Çalıştırma

```bash
# Flask sunucusunu başlatın
python app.py
```

Uygulama başlarken:
1. ✅ PDF'lerden corpus oluşturulur
2. ✅ N-gram sözlükleri (unigram, bigram, trigram, quadgram) hesaplanır
3. ✅ Test seti yüklenir
4. ✅ Model RAM'de hazır bekletilir (warm-up)

Tarayıcınızda açın: **http://localhost:5000**

---

## 📡 API Referansı

### `GET /api/stats`
Model istatistiklerini döndürür.

**Yanıt:**
```json
{
  "corpus_size": 32000,
  "unique_tokens": 5200,
  "unique_bigrams": 24000,
  "unique_trigrams": 30000,
  "unique_quadgrams": 31000,
  "test_set_size": 55
}
```

---

### `POST /api/analyze`
Serbest metin analizi yapar — kelime sayısı, n-gram istatistikleri, corpus eşleşmeleri.

**İstek:**
```json
{
  "text": "The process of photosynthesis involves the conversion of light energy..."
}
```

**Yanıt:**
```json
{
  "word_count": 12,
  "unique_words": 10,
  "sentence_count": 1,
  "bigram_matches": [{"ngram": "the process", "text_freq": 1, "corpus_freq": 15}],
  "trigram_matches": [...],
  "quadgram_matches": [...]
}
```

---

### `POST /api/predict`
Tek bir cloze sorusu için tahmin yapar.

**İstek (ID ile):**
```json
{"question_id": 1}
```

**Yanıt:**
```json
{
  "question_id": 1,
  "predicted_answer": "E",
  "correct_answer": "E",
  "is_correct": true,
  "scores": {"A": 1.5, "B": 3.2, "C": 0.8, "D": 2.1, "E": 7.4},
  "breakdown": {"unigram": 0.3, "bigram": 1.2, "trigram": 4.0, "quadgram": 1.9}
}
```

---

### `GET /api/test`
Tüm test setini çözüp detaylı sonuçları döndürür.

**Yanıt:**
```json
{
  "accuracy": 0.25,
  "accuracy_pct": "25.0%",
  "correct": 14,
  "total": 55,
  "ngram_contribution": {"unigram": 12.5, "bigram": 45.3, "trigram": 28.1, "quadgram": 8.7},
  "predicted_distribution": {"A": 15, "B": 12, "C": 10, "D": 10, "E": 8},
  "results": [...]
}
```

---

### `GET /api/questions`
Test setindeki soruları listeler (cevap anahtarı gizli).

---

## 🧠 Algoritma Detayları

### N-Gram Frekans Sözlükleri

Corpus'tan 4 seviyede n-gram sözlüğü çıkarılır:

| N-Gram | Örnek | Kullanım |
|--------|-------|----------|
| **Unigram** | `"photosynthesis"` | Kelime düzeyinde fallback |
| **Bigram** | `("the", "process")` | Temel kelime çifti kalıpları |
| **Trigram** | `("in", "order", "to")` | Akademik üçlü kalıplar |
| **Quadgram** | `("on", "the", "other", "hand")` | Bağlaç ve geçiş kalıpları |

### Ağırlıklı Skorlama

Her şık için bağlam penceresi oluşturulur:

```
[... sol_bağlam] + [ŞIK] + [sağ_bağlam ...]
```

Bu penceredeki tüm n-gram'lar sözlükte aranır ve **log-frekans** dönüşümü uygulanır:

```
skor = log₂(1 + frekans)
```

Ağırlıklar:
- Unigram: **×0.3** (düşük güvenilirlik, fallback)
- Bigram:  **×1.0** (temel referans)
- Trigram: **×4.0** (yüksek güvenilirlik)
- Quadgram: **×7.0** (en yüksek güvenilirlik)

### Optimizasyonlar

1. **Log-frekans**: Aşırı sık bigram'ların (`"of the"`) baskınlığını azaltır
2. **Unigram fallback**: Hiç n-gram eşleşmesi olmadığında kelime frekansıyla karar verir
3. **İç n-gram analizi**: Çoklu kelimeli şıklar (`"carried out"`) için iç bigram/trigram'lar da değerlendirilir
4. **Sınır n-gram'ları**: Şıkkın başlangıç ve bitişinde bağlam ile oluşan tüm n-gram kombinasyonları kontrol edilir

---

## 🖥 Web Arayüzü

Arayüz 3 ana sekmeden oluşur:

### 1. Serbest Metin Analizi
Herhangi bir İngilizce metin girilerek corpus ile n-gram eşleşmeleri incelenebilir. Bigram, trigram ve quadgram seviyesinde corpus frekansları gösterilir.

### 2. Cloze Test (Boşluk Doldurma)
İnteraktif soru çözme ekranı:
- Kullanıcı bir şık seçer
- Model de kendi tahminini yapar
- Doğru cevap, kullanıcı ve model skorları anlık olarak karşılaştırılır
- Her şıkkın n-gram skoru gösterilir

### 3. Sonuçlar (Model Performansı)
"Tüm Testi Çalıştır" butonu ile modelin tüm test seti üzerindeki performansı ölçülür:
- **Doğru/Yanlış** doughnut grafiği
- **N-Gram katkı dağılımı** radar grafiği (hangi n-gram seviyesi ne kadar katkı yaptı)
- **Şık dağılımı** karşılaştırma grafiği (model tahmini vs doğru cevap)
- **Soru bazlı** sonuç bar grafiği
- **Detaylı sonuç tablosu**

---

## 📜 Lisans

Bu proje akademik amaçlı geliştirilmiştir.

---
## Önemli endpoint listesi
http://127.0.0.1:5000/api/evaluation/template?top_k=50
## 👤 Geliştirici

Doğal Dil İşleme dersi kapsamında hazırlanmıştır.
