# """
# corpus_builder.py — YÖKDİL PDF'lerinden İngilizce corpus oluşturma modülü.
# file2.py'deki fonksiyonların modüler, import edilebilir hali.
# """

# import pdfplumber
# import re
# import os
# import glob


# def turkce_satir_mi(satir):
#     """Bir satırın Türkçe yönerge veya çeviri şıkkı olup olmadığını kontrol eder."""
#     satir_kucuk = satir.lower()

#     yonergeler = [
#         "sorularda", "cümlede", "boş bırakılan", "uygun düşen",
#         "sözcük", "ifadeyi", "bulunuz", "parçada", "tamamlayan",
#         "anlamca", "en yakın", "karşılık gelen", "çevirisini",
#         "doğru", "akışı", "bozan", "cümleyi", "diyalogda",
#         "cevap", "soruya", "verilen", "seçeneği", "işaretleyiniz",
#         "yerlere", "ya da", "diğer sayfaya geçiniz", "fen bilimleri",
#         "yökdil", "ösym", "yükseköğretim", "testi bitti",
#         "kontrol ediniz", "adayın dikkati", "kimlik numaranız",
#         "cevap anahtarı"
#     ]

#     turkce_harfler = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü']

#     turkce_kelimeler_regex = (
#         r'\b(bir|ve|bu|için|ile|olarak|olan|gibi|daha|kadar|'
#         r'göre|değil|veya|ancak|ise)\b'
#     )

#     for kelime in yonergeler:
#         if kelime in satir_kucuk:
#             return True

#     for harf in turkce_harfler:
#         if harf in satir_kucuk:
#             return True

#     if re.search(turkce_kelimeler_regex, satir_kucuk):
#         return True

#     return False


# def extract_english_tokens(pdf_path):
#     """Tek bir YÖKDİL PDF'inden temizlenmiş İngilizce token listesi çıkarır."""
#     ham_metin = ""

#     with pdfplumber.open(pdf_path) as pdf:
#         for i, page in enumerate(pdf.pages):
#             text = page.extract_text()
#             if not text:
#                 continue

#             lower_full = text.lower()
#             # Kapak sayfası kontrolü
#             if i == 0 and ("kimlik" in lower_full or "dikkat" in lower_full or "aday" in lower_full):
#                 continue

#             lines = text.split('\n')
#             clean_lines = [line for line in lines if not turkce_satir_mi(line)]
#             english_text = ' '.join(clean_lines).lower()

#             # Sadece a-z ve boşluk bırak
#             clean_text = re.sub(r'[^a-z\s]', ' ', english_text)
#             clean_text = re.sub(r'\s+', ' ', clean_text).strip()
#             ham_metin += clean_text + " "

#     tokens = [k for k in ham_metin.split(' ') if k]
#     return tokens


# def build_corpus(data_dir=None):
#     """
#     Verilen klasördeki tüm YOKDIL*.pdf dosyalarından corpus oluşturur.
#     data_dir verilmezse varsayılan 'data/' klasörünü kullanır.
#     """
#     if data_dir is None:
#         data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

#     pattern = os.path.join(data_dir, "YOKDIL*.pdf")
#     pdf_files = sorted(glob.glob(pattern))

#     all_tokens = []

#     if not pdf_files:
#         print(f"UYARI: {data_dir} içinde 'YOKDIL' ile başlayan PDF bulunamadı!")
#         return all_tokens

#     print(f"Toplam {len(pdf_files)} adet PDF bulundu. Corpus oluşturuluyor...\n")

#     for pdf_path in pdf_files:
#         tokens = extract_english_tokens(pdf_path)
#         all_tokens.extend(tokens)
#         print(f"  -> {os.path.basename(pdf_path)}: {len(tokens)} token")

#     print(f"\nToplam corpus büyüklüğü: {len(all_tokens)} kelime.")
#     return all_tokens


# if __name__ == '__main__':
#     data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
#     tokens = build_corpus(data_dir)
#     print(f"\nİlk 20 token: {tokens[:20]}")


"""
corpus_builder.py — YÖKDİL PDF'lerinden İngilizce corpus oluşturma modülü.

Bu sürüm:
- PDF sayfalarını iki kolon olarak okumaya çalışır.
- Türkçe yönergeleri, kapak yazılarını ve gereksiz satırları temizler.
- Cevap anahtarı genellikle son sayfada olduğu için son sayfayı corpus'a dahil etmez.
- Sadece İngilizce a-z karakterlerinden token üretir.
"""

import pdfplumber
import re
import os
import glob


def turkce_satir_mi(satir):
    """
    Bir satırın Türkçe yönerge, sınav açıklaması veya corpus'a girmemesi gereken
    yapısal bir satır olup olmadığını kontrol eder.
    """
    satir_kucuk = satir.lower()

    yonergeler = [
        "sorularda", "cümlede", "boş bırakılan", "uygun düşen",
        "sözcük", "ifadeyi", "bulunuz", "parçada", "tamamlayan",
        "anlamca", "en yakın", "karşılık gelen", "çevirisini",
        "doğru", "akışı", "bozan", "cümleyi", "diyalogda",
        "cevap", "soruya", "verilen", "seçeneği", "işaretleyiniz",
        "yerlere", "ya da", "diğer sayfaya geçiniz", "fen bilimleri",
        "sosyal bilimler", "sağlık bilimleri",
        "yökdil", "ösym", "yükseköğretim", "testi bitti",
        "kontrol ediniz", "adayın dikkati", "kimlik numaranız",
        "cevap anahtarı", "temel soru kitapçığı"
    ]

    turkce_harfler = ["ç", "ğ", "ı", "ö", "ş", "ü"]

    turkce_kelimeler_regex = (
        r'\b(bir|ve|bu|için|ile|olarak|olan|gibi|daha|kadar|'
        r'göre|değil|veya|ancak|ise|sonra|önce|hangi|aşağıdaki)\b'
    )

    for kelime in yonergeler:
        if kelime in satir_kucuk:
            return True

    for harf in turkce_harfler:
        if harf in satir_kucuk:
            return True

    if re.search(turkce_kelimeler_regex, satir_kucuk):
        return True

    return False


def extract_text_by_columns(page):
    """
    YÖKDİL PDF'leri çoğunlukla iki kolonlu olduğu için doğrudan page.extract_text()
    bazen sol ve sağ kolonu karıştırabilir.

    Bu fonksiyon sayfayı sol ve sağ kolon olarak ikiye böler,
    önce sol kolonu sonra sağ kolonu okur.
    """
    width = page.width
    height = page.height

    left_bbox = (0, 0, width / 2, height)
    right_bbox = (width / 2, 0, width, height)

    left_text = page.crop(left_bbox).extract_text() or ""
    right_text = page.crop(right_bbox).extract_text() or ""

    return left_text + "\n" + right_text


def clean_english_text(text):
    """
    Metni normalize eder:
    - lowercase
    - sadece a-z ve boşluk bırakır
    - fazla boşlukları temizler
    """
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_english_tokens(pdf_path):
    """
    Tek bir YÖKDİL PDF'inden temizlenmiş İngilizce token listesi çıkarır.
    """
    ham_metin = ""

    with pdfplumber.open(pdf_path) as pdf:

        # ÖNEMLİ:
        # pdf.pages[:-1] kullanıyoruz.
        # Çünkü son sayfa çoğunlukla cevap anahtarıdır.
        # Böylece cevap anahtarı corpus'a karışmaz.
        for i, page in enumerate(pdf.pages[:-1]):

            text = extract_text_by_columns(page)

            if not text:
                continue

            lower_full = text.lower()

            # Kapak / aday bilgilendirme sayfasını atla
            if i == 0 and (
                "kimlik" in lower_full or
                "dikkat" in lower_full or
                "aday" in lower_full or
                "sınav" in lower_full
            ):
                continue

            lines = text.split("\n")

            clean_lines = []

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Türkçe yönerge veya sınav yapısal metni ise alma
                if turkce_satir_mi(line):
                    continue

                clean_lines.append(line)

            english_text = " ".join(clean_lines)
            clean_text = clean_english_text(english_text)

            ham_metin += clean_text + " "

    tokens = [token for token in ham_metin.split(" ") if token]

    return tokens


def build_corpus(data_dir=None):
    """
    Verilen klasördeki tüm YOKDIL*.pdf dosyalarından corpus oluşturur.

    data_dir verilmezse varsayılan olarak proje kökündeki data/ klasörü kullanılır.
    """
    if data_dir is None:
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data"
        )

    pattern = os.path.join(data_dir, "YOKDIL*.pdf")
    pdf_files = sorted(glob.glob(pattern))

    all_tokens = []

    if not pdf_files:
        print(f"UYARI: {data_dir} içinde 'YOKDIL' ile başlayan PDF bulunamadı!")
        return all_tokens

    print(f"Toplam {len(pdf_files)} adet PDF bulundu. Corpus oluşturuluyor...\n")

    for pdf_path in pdf_files:
        tokens = extract_english_tokens(pdf_path)
        all_tokens.extend(tokens)

        print(f"  -> {os.path.basename(pdf_path)}: {len(tokens)} token")

    print(f"\nToplam corpus büyüklüğü: {len(all_tokens)} kelime.")

    return all_tokens


if __name__ == "__main__":
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data"
    )

    tokens = build_corpus(data_dir)

    print(f"\nİlk 20 token: {tokens[:20]}")