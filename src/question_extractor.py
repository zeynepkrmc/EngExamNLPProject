# """
# question_extractor.py — YÖKDİL PDF'lerinden boşluk doldurma (cloze) sorularını çıkarır.
# Cevap anahtarını her PDF'in son sayfasından okur.
# """

# import pdfplumber
# import re
# import os
# import glob
# import json


# def extract_answer_key(pdf_path):
#     """
#     PDF'in son sayfasındaki cevap anahtarını okur.
#     Döndürür: {soru_no: 'A'|'B'|'C'|'D'|'E', ...}
#     """
#     answers = {}

#     with pdfplumber.open(pdf_path) as pdf:
#         last_page = pdf.pages[-1]
#         text = last_page.extract_text()

#         if not text:
#             return answers

#         # Çeşitli ÖSYM cevap anahtarı formatlarını yakala
#         # Format: "1. A", "1 A", "1-A", "1  A" vb.
#         pattern = r'(\d+)\s*[.\-)\s]\s*([A-E])\b'
#         matches = re.findall(pattern, text)

#         for num_str, letter in matches:
#             num = int(num_str)
#             if 1 <= num <= 80:
#                 answers[num] = letter

#     return answers


# def extract_cloze_questions(pdf_path):
#     """
#     Bir YÖKDİL PDF'inden boşluk doldurma sorularını çıkarır.
#     Boşluk '----' (4+ tire) ile işaretlidir.
#     """
#     questions = []
#     all_text = ""

#     with pdfplumber.open(pdf_path) as pdf:
#         # Son sayfa (cevap anahtarı) hariç tüm sayfaları oku
#         for page in pdf.pages[:-1]:
#             text = page.extract_text()
#             if text:
#                 all_text += text + "\n"

#     # Soru sınırlarını bul: sayı + nokta ile başlayan bloklar
#     # Örn: "1. The experiment ---- that..."
#     question_blocks = re.split(r'(?:^|\n)\s*(\d+)\.\s', all_text)

#     # split sonucu: [önceki_metin, soru_no_1, metin_1, soru_no_2, metin_2, ...]
#     for i in range(1, len(question_blocks) - 1, 2):
#         try:
#             q_num = int(question_blocks[i])
#         except ValueError:
#             continue

#         q_text = question_blocks[i + 1]

#         # Sadece boşluk doldurma sorularını al (---- içerenler)
#         if not re.search(r'-{3,}', q_text):
#             continue

#         # Şıkları çıkar: A) ... B) ... C) ... D) ... E) ...
#         option_pattern = r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|$)'
#         option_matches = re.findall(option_pattern, q_text, re.DOTALL)

#         if len(option_matches) < 5:
#             continue

#         options = {}
#         for letter, opt_text in option_matches[:5]:
#             cleaned = re.sub(r'\s+', ' ', opt_text).strip()
#             options[letter] = cleaned

#         # Soru cümlesini şıklardan ayır
#         q_sentence = re.split(r'\s*A\)', q_text)[0].strip()
#         q_sentence = re.sub(r'\s+', ' ', q_sentence)

#         # Sol ve sağ bağlamı ayır (---- etrafında)
#         parts = re.split(r'-{3,}', q_sentence, maxsplit=1)
#         left_context = parts[0].strip() if len(parts) > 0 else ""
#         right_context = parts[1].strip() if len(parts) > 1 else ""

#         questions.append({
#             'id': q_num,
#             'source': os.path.basename(pdf_path),
#             'question_text': q_sentence,
#             'left_context': left_context,
#             'right_context': right_context,
#             'options': options,
#             'correct_answer': None
#         })

#     return questions


# def build_test_set(data_dir=None, output_path=None):
#     """
#     Tüm YÖKDİL PDF'lerinden cloze sorularını çıkarıp JSON test seti oluşturur.
#     """
#     if data_dir is None:
#         data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
#     if output_path is None:
#         output_path = os.path.join(
#             os.path.dirname(os.path.dirname(__file__)), 'test_data', 'cloze_test_set.json'
#         )

#     pattern = os.path.join(data_dir, "YOKDIL*.pdf")
#     pdf_files = sorted(glob.glob(pattern))

#     all_questions = []
#     global_id = 1

#     for pdf_path in pdf_files:
#         basename = os.path.basename(pdf_path)
#         print(f"\n{'='*50}")
#         print(f"{basename} işleniyor...")

#         # Soruları çıkar
#         questions = extract_cloze_questions(pdf_path)
#         print(f"  -> {len(questions)} boşluk doldurma sorusu bulundu")

#         # Cevap anahtarını çıkar
#         answers = extract_answer_key(pdf_path)
#         print(f"  -> {len(answers)} cevap anahtarı okundu")

#         # Cevapları sorularla eşleştir
#         for q in questions:
#             if q['id'] in answers:
#                 q['correct_answer'] = answers[q['id']]
#             q['original_id'] = q['id']
#             q['id'] = global_id
#             global_id += 1

#         all_questions.extend(questions)

#     # JSON olarak kaydet
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(all_questions, f, ensure_ascii=False, indent=2)

#     answered = sum(1 for q in all_questions if q['correct_answer'])
#     print(f"\n{'='*50}")
#     print(f"SONUÇ: Toplam {len(all_questions)} soru çıkarıldı.")
#     print(f"Cevaplı: {answered} | Cevapsız: {len(all_questions) - answered}")
#     print(f"Kaydedildi: {output_path}")

#     return all_questions


# if __name__ == '__main__':
#     build_test_set()

"""
question_extractor.py — YÖKDİL PDF'lerinden cloze soruları çıkarır
ve n-gram phrase'lerden otomatik practice quiz üretir.

Bu dosya iki amaç için kullanılır:

1. Gerçek YÖKDİL PDF cloze sorularını temiz şekilde çıkarmak:
   - Son sayfadaki cevap anahtarını okur.
   - Sadece ---- içeren cloze sorularını alır.
   - Türkçe yönerge, reading/translation soruları ve bozuk seçenekleri filtreler.

2. Çıkarılan n-gram phrase'lerden öğrenci için practice quiz üretmek:
   - 10 soruluk mini quiz
   - 50 soruluk full quiz
   - Bigram, trigram ve quadgram phrase'lerden boşluk doldurma soruları üretir.
"""

import pdfplumber
import re
import os
import glob
import json
import random


LETTERS = ["A", "B", "C", "D", "E"]


# ---------------------------------------------------------
# PDF TEXT EXTRACTION HELPERS
# ---------------------------------------------------------

def extract_text_by_columns(page):
    """
    İki kolonlu YÖKDİL PDF'lerinde metnin karışmasını azaltmak için
    sayfayı sol ve sağ kolon olarak ayrı ayrı okur.
    """
    width = page.width
    height = page.height

    left_bbox = (0, 0, width / 2, height)
    right_bbox = (width / 2, 0, width, height)

    left_text = page.crop(left_bbox).extract_text() or ""
    right_text = page.crop(right_bbox).extract_text() or ""

    return left_text + "\n" + right_text


def normalize_space(text):
    """
    Fazla boşlukları temizler.
    """
    return re.sub(r"\s+", " ", text).strip()


def contains_turkish_or_instruction(text):
    """
    Türkçe yönerge, sınav açıklaması veya corpus/test için gereksiz satırları yakalar.
    """
    lower = text.lower()

    bad_phrases = [
        "sorularda", "cümlede", "boş bırakılan", "uygun düşen",
        "sözcük", "ifadeyi", "bulunuz", "parçada", "tamamlayan",
        "anlamca", "en yakın", "karşılık gelen", "çevirisini",
        "doğru", "akışı", "bozan", "cümleyi", "diyalogda",
        "cevap", "soruya", "verilen", "seçeneği", "işaretleyiniz",
        "yerlere", "ya da", "diğer sayfaya geçiniz",
        "fen bilimleri", "sosyal bilimler", "sağlık bilimleri",
        "yökdil", "ösym", "yükseköğretim", "testi bitti",
        "kontrol ediniz", "adayın dikkati", "kimlik numaranız",
        "cevap anahtarı", "temel soru kitapçığı",
    ]

    turkish_chars = ["ç", "ğ", "ı", "ö", "ş", "ü"]

    turkish_words_regex = (
        r"\b(bir|ve|bu|için|ile|olarak|olan|gibi|daha|kadar|"
        r"göre|değil|veya|ancak|ise|hangi|aşağıdaki)\b"
    )

    if any(phrase in lower for phrase in bad_phrases):
        return True

    if any(ch in lower for ch in turkish_chars):
        return True

    if re.search(turkish_words_regex, lower):
        return True

    return False


# ---------------------------------------------------------
# ANSWER KEY EXTRACTION
# ---------------------------------------------------------

def extract_answer_key(pdf_path):
    """
    PDF'in son sayfasındaki cevap anahtarını okur.

    Döndürür:
    {
        1: "A",
        2: "C",
        ...
    }
    """
    answers = {}

    with pdfplumber.open(pdf_path) as pdf:
        last_page = pdf.pages[-1]
        text = last_page.extract_text() or ""

    if not text:
        return answers

    # Formatlar:
    # 1. A
    # 1 A
    # 1-A
    # 1) A
    pattern = r"\b(\d{1,2})\s*[.\-)]?\s*([A-E])\b"
    matches = re.findall(pattern, text)

    for num_str, letter in matches:
        num = int(num_str)

        if 1 <= num <= 80:
            answers[num] = letter

    return answers


# ---------------------------------------------------------
# REAL YÖKDİL CLOZE QUESTION EXTRACTION
# ---------------------------------------------------------

def is_bad_question_text(question_text):
    """
    Cloze olmayan veya proje için uygun olmayan soru tiplerini eler.
    """
    lower = question_text.lower()

    bad_phrases = [
        "sorularda",
        "verilen cümlede",
        "boş bırakılan yerlere",
        "uygun düşen",
        "türkçe",
        "çevirisini",
        "ingilizce cümleye",
        "anlamca",
        "parçaya göre",
        "according to the passage",
        "it can be understood from the passage",
        "which could be the best title",
        "the passage is mainly about",
        "underlined word",
        "closest in meaning",
        "irrelevant sentence",
        "complete the dialogue",
    ]

    return any(phrase in lower for phrase in bad_phrases)


def is_valid_option(option_text):
    """
    Şık metni kullanılabilir mi kontrol eder.
    PDF parse bozulursa şık içine uzun soru blokları veya sayfa yazıları karışabilir.
    """
    option_text = normalize_space(option_text)
    lower = option_text.lower()

    if not option_text:
        return False

    bad_parts = [
        "diğer sayfaya geçiniz",
        "yökdil",
        "ösym",
        "fen bilimleri",
        "sosyal bilimler",
        "sağlık bilimleri",
        "testi bitti",
        "cevap anahtarı",
        "sorularda",
        "boş bırakılan",
        "according to the passage",
        "it can be understood",
        "which could be the best title",
        "the passage is mainly about",
    ]

    if any(part in lower for part in bad_parts):
        return False

    # Şık içinde boşluk işareti varsa büyük ihtimalle soru metni şık içine karışmıştır.
    if re.search(r"-{3,}", option_text):
        return False

    # Şık içinde cümle devamı karışmış olabilir.
    # Cloze seçenekleri genelde 1-5 kelime olur.
    if len(option_text.split()) > 7:
        return False

    # Çok fazla noktalama varsa muhtemelen soru cümlesi şık içine karışmıştır.
    if option_text.count(",") + option_text.count(".") + option_text.count(";") > 1:
        return False

    # Şık içinde başka soru numarası başlıyorsa parse bozulmuştur.
    if re.search(r"\b\d{1,2}\.\s+[A-Z]", option_text):
        return False

    # Şık içinde yeni seçenek harfleri görünüyorsa parse bozulmuştur.
    if re.search(r"\b[A-E]\)\s+", option_text):
        return False

    return True


def is_valid_cloze_question(question):
    """
    Çıkarılan soru gerçekten temiz bir cloze sorusu mu?
    """
    question_text = question.get("question_text", "")
    options = question.get("options", {})

    # Soru metninde mutlaka boşluk olmalı
    if not re.search(r"-{3,}", question_text):
        return False

    if is_bad_question_text(question_text):
        return False

    if set(options.keys()) != {"A", "B", "C", "D", "E"}:
        return False

    if not question.get("left_context") and not question.get("right_context"):
        return False

    # Sol + sağ bağlam temiz olmalı
    left_context = question.get("left_context", "")
    right_context = question.get("right_context", "")

    if contains_turkish_or_instruction(left_context):
        return False

    if contains_turkish_or_instruction(right_context):
        return False

    # Soru çok kısa ise genelde parse hatasıdır
    left_len = len(left_context.split())
    right_len = len(right_context.split())

    if left_len + right_len < 5:
        return False

    # Soru cümlesinin içinde seçenek harfi kalmışsa parse bozulmuş olabilir
    if re.search(r"\b[A-E]\)\s+", question_text):
        return False

    for option in options.values():
        if not is_valid_option(option):
            return False

    return True


def extract_cloze_questions(pdf_path):
    """
    Bir YÖKDİL PDF'inden gerçek cloze sorularını çıkarır.
    Boşluk '----' ile işaretlenmiş olmalıdır.
    """
    questions = []
    all_text = ""

    with pdfplumber.open(pdf_path) as pdf:

        # Son sayfa cevap anahtarı olduğu için okunmaz.
        for page_index, page in enumerate(pdf.pages[:-1]):

            text = extract_text_by_columns(page)

            if not text:
                continue

            lower = text.lower()

            # Kapak / aday bilgilendirme sayfasını atla
            if page_index == 0 and (
                "kimlik" in lower or
                "aday" in lower or
                "dikkat" in lower
            ):
                continue

            # Türkçe yönerge satırlarını temizle
            clean_lines = []

            for line in text.split("\n"):
                line = line.strip()

                if not line:
                    continue

                if contains_turkish_or_instruction(line):
                    continue

                clean_lines.append(line)

            all_text += "\n".join(clean_lines) + "\n"

    # Soru bloklarını ayır:
    # 1. The experiment ---- ...
    question_blocks = re.split(r"(?:^|\n)\s*(\d{1,2})\.\s+", all_text)

    for i in range(1, len(question_blocks) - 1, 2):

        try:
            q_num = int(question_blocks[i])
        except ValueError:
            continue

        raw_block = normalize_space(question_blocks[i + 1])
        # Eğer bu blok içinde yanlışlıkla sonraki soru numarası kaldıysa kes
        raw_block = re.split(r"\s+\d{1,2}\.\s+", raw_block)[0]
        raw_block = normalize_space(raw_block)

        if not re.search(r"-{3,}", raw_block):
            continue

        # A) ... B) ... C) ... D) ... E) ...
        #option_pattern = r"\b([A-E])\)\s*(.*?)(?=\s+[A-E]\)|$)"
        option_pattern = r"(?:^|\s)([A-E])\)\s*(.*?)(?=\s+[A-E]\)|$)"
        option_matches = re.findall(option_pattern, raw_block)

        if len(option_matches) < 5:
            continue

        options = {}

        for letter, opt_text in option_matches[:5]:
            cleaned = normalize_space(opt_text)
            options[letter] = cleaned

        # A)'dan önceki kısım soru cümlesidir.
        #q_sentence = re.split(r"\s+A\)", raw_block, maxsplit=1)[0]
        q_sentence = re.split(r"(?:^|\s)A\)", raw_block, maxsplit=1)[0]
        q_sentence = normalize_space(q_sentence)

        parts = re.split(r"-{3,}", q_sentence, maxsplit=1)

        if len(parts) != 2:
            continue

        left_context = parts[0].strip()
        right_context = parts[1].strip()

        question = {
            "id": q_num,
            "source": os.path.basename(pdf_path),
            "question_type": "real_cloze",
            "question_text": q_sentence,
            "left_context": left_context,
            "right_context": right_context,
            "options": options,
            "correct_answer": None,
        }

        if is_valid_cloze_question(question):
            questions.append(question)

    return questions


def build_test_set(data_dir=None, output_path=None):
    """
    Tüm YÖKDİL PDF'lerinden gerçek cloze sorularını çıkarıp JSON test seti oluşturur.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "test_data",
            "cloze_test_set.json"
        )

    pattern = os.path.join(data_dir, "YOKDIL*.pdf")
    pdf_files = sorted(glob.glob(pattern))

    all_questions = []
    global_id = 1

    for pdf_path in pdf_files:
        basename = os.path.basename(pdf_path)

        print(f"\n{'=' * 50}")
        print(f"{basename} işleniyor...")

        questions = extract_cloze_questions(pdf_path)
        print(f"  -> {len(questions)} temiz cloze sorusu bulundu")

        answers = extract_answer_key(pdf_path)
        print(f"  -> {len(answers)} cevap anahtarı okundu")

        for question in questions:
            original_id = question["id"]

            if original_id in answers:
                question["correct_answer"] = answers[original_id]

            question["original_id"] = original_id
            question["id"] = global_id

            global_id += 1

        # Cevabı olmayanları test setine alma
        questions = [q for q in questions if q.get("correct_answer")]

        all_questions.extend(questions)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    answered = sum(1 for q in all_questions if q.get("correct_answer"))

    print(f"\n{'=' * 50}")
    print(f"SONUÇ: Toplam {len(all_questions)} temiz soru çıkarıldı.")
    print(f"Cevaplı: {answered} | Cevapsız: {len(all_questions) - answered}")
    print(f"Kaydedildi: {output_path}")

    return all_questions


# ---------------------------------------------------------
# N-GRAM BASED PRACTICE QUIZ GENERATION
# ---------------------------------------------------------

def get_source_for_ngram_type(ngram_model, ngram_type):
    """
    NgramModel içinden istenen n-gram Counter objesini döndürür.
    """
    if ngram_type == "bigram":
        return ngram_model.bigrams

    if ngram_type == "trigram":
        return ngram_model.trigrams

    if ngram_type == "quadgram":
        return ngram_model.quadgrams

    return ngram_model.bigrams


# def choose_blank_index(words):
#     """
#     Phrase içinde hangi kelimenin boş bırakılacağını seçer.

#     Amaç:
#     - Bigramlarda çoğunlukla ikinci kelimeyi boş bırakmak:
#       according ----
#     - Trigramlarda ortadaki veya son kelimeyi boş bırakmak:
#       as ---- as
#       due to ----
#     - Quadgramlarda phrase'in anlamlı bir kelimesini boş bırakmak:
#       as a result ----
#     """
#     n = len(words)

#     if n == 2:
#         return 1

#     if n == 3:
#         return 1

#     if n >= 4:
#         return random.choice([1, 2, 3])
    

#     return 0

def choose_blank_index(words):
    """
    Phrase içinde hangi kelimenin boş bırakılacağını seçer.
    Öncelik: phrase'in anlam taşıyan kelimesini boş bırakmak.
    """
    phrase = " ".join(words)

    special_blanks = {
        "according to": 1,
        "such as": 1,
        "due to": 1,
        "because of": 1,
        "rather than": 1,
        "as well as": 1,
        "in terms of": 1,
        "in order to": 1,
        "as a result": 2,
        "as a result of": 2,
        "on the other hand": 3,
        "in addition to": 1,
        "in contrast to": 1,
    }

    if phrase in special_blanks and special_blanks[phrase] < len(words):
        return special_blanks[phrase]

    n = len(words)

    if n == 2:
        return 1

    if n == 3:
        return 1

    if n >= 4:
        # Article / preposition yerine daha anlamlı kelimeyi seçmeye çalış
        weak_words = {"the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with"}

        candidate_indexes = [
            i for i, word in enumerate(words)
            if i != 0 and word not in weak_words
        ]

        if candidate_indexes:
            return candidate_indexes[0]

        return min(2, n - 1)

    return 0


def build_question_text_from_phrase(words, blank_index):
    """
    Phrase'i boşluk doldurma formatına çevirir.
    """
    question_words = []

    for i, word in enumerate(words):
        if i == blank_index:
            question_words.append("----")
        else:
            question_words.append(word)

    return " ".join(question_words)


def make_options(correct_word, distractor_pool):
    """
    Doğru cevabın yanına 4 yanlış seçenek ekler.
    """
    correct_word = correct_word.lower().strip()

    clean_pool = []

    for word in distractor_pool:
        word = word.lower().strip()

        if not word:
            continue

        if word == correct_word:
            continue

        if len(word) <= 1:
            continue

        if not re.match(r"^[a-z]+$", word):
            continue

        clean_pool.append(word)

    clean_pool = list(set(clean_pool))

    if len(clean_pool) < 4:
        return None, None

    wrong_options = random.sample(clean_pool, 4)
    all_options = wrong_options + [correct_word]
    random.shuffle(all_options)

    options = {}
    correct_letter = None

    for letter, option in zip(LETTERS, all_options):
        options[letter] = option

        if option == correct_word:
            correct_letter = letter

    return options, correct_letter

# def is_good_practice_phrase(words, ngram_type):
#     """
#     Practice test için gerçekten öğretici phrase'leri seçer.

#     Amaç:
#     - it is, the passage, can be, have been gibi çok genel kalıpları azaltmak
#     - according to, such as, due to, as well as, in terms of gibi
#       akademik/öğretici kalıpları öne çıkarmak
#     """

#     if not words or len(words) < 2:
#         return False

#     phrase = " ".join(words)

#     weak_starts = {
#         "the", "a", "an",
#         "it", "they", "we", "he", "she", "there",
#         "this", "that", "these", "those",
#         "can", "could", "may", "might", "must",
#         "have", "has", "had", "is", "are", "was", "were",
#         "to"
#     }

#     weak_phrases = {
#         "it is",
#         "it was",
#         "they are",
#         "there are",
#         "there is",
#         "can be",
#         "could be",
#         "may be",
#         "might be",
#         "have been",
#         "has been",
#         "had been",
#         "to be",
#         "the passage",
#         "the sun",
#         "the world"
#     }

#     useful_starts = {
#         "according", "due", "because", "although", "despite",
#         "whereas", "while", "rather", "such", "as",
#         "in", "on", "by", "with", "without", "for"
#     }

#     useful_words = {
#         "according", "due", "because", "although", "despite",
#         "whereas", "while", "rather", "such", "result",
#         "terms", "order", "basis", "effect", "effects",
#         "associated", "related", "likely", "lead", "leads",
#         "caused", "causes", "process", "increase", "decrease"
#     }

#     weak_ends = {
#         "the", "a", "an",
#         "and", "or", "but",
#         "of", "to", "in", "on", "at", "for", "with", "by"
#     }

#     if phrase in weak_phrases:
#         return False

#     if ngram_type in ["trigram", "quadgram"] and words[-1] in weak_ends:
#         return False

#     # Bigramlarda zayıf başlangıçları büyük ölçüde ele
#     if ngram_type == "bigram" and words[0] in weak_starts:
#         return False

#     # Trigram/quadgramlarda da zayıf başlangıçları ele,
#     # ancak phrase içinde useful word varsa izin ver.
#     if ngram_type in ["trigram", "quadgram"]:
#         if words[0] in weak_starts and not any(w in useful_words for w in words):
#             return False

#     # En az bir öğretici işaret taşısın
#     if words[0] in useful_starts:
#         return True

#     if any(w in useful_words for w in words):
#         return True

#     # Bigramlarda "associated with", "related to", "lead to" gibi yapılar
#     if len(words) == 2 and words[1] in {"to", "with", "of", "for", "from", "by", "as"}:
#         return True

#     return False
def is_good_practice_phrase(words, ngram_type):
    """
    Practice test için gerçekten öğretici phrase'leri seçer.

    Amaç:
    - it is, the passage, can be, have been gibi çok genel kalıpları azaltmak
    - according to, such as, due to, as well as, in terms of gibi
      akademik/öğretici kalıpları öne çıkarmak
    """

    if not words or len(words) < 2:
        return False

    phrase = " ".join(words)

    weak_starts = {
        "the", "a", "an",
        "it", "they", "we", "he", "she", "there",
        "this", "that", "these", "those",
        "can", "could", "may", "might", "must",
        "have", "has", "had", "is", "are", "was", "were",
        "to"
    }

    weak_ends = {
        "the", "a", "an",
        "and", "or", "but",
        "of", "to", "in", "on", "at", "for", "with", "by"
    }

    weak_phrases = {
        "it is",
        "it was",
        "they are",
        "there are",
        "there is",
        "can be",
        "could be",
        "may be",
        "might be",
        "have been",
        "has been",
        "had been",
        "to be",
        "the passage",
        "the sun",
        "the world",
        "the same",
        "the first",
        "the most",
        "one of"
    }

    always_good_phrases = {
        "according to",
        "such as",
        "due to",
        "because of",
        "rather than",
        "as well",
        "as well as",
        "in terms",
        "in terms of",
        "in order",
        "in order to",
        "as a result",
        "as a result of",
        "on the other hand",
        "in addition to",
        "in contrast to",
        "associated with",
        "related to",
        "lead to",
        "leads to",
        "likely to",
        "is likely to"
    }

    useful_starts = {
        "according", "due", "because", "although", "despite",
        "whereas", "while", "rather", "such", "as",
        "in", "on", "by", "with", "without", "for"
    }

    useful_words = {
        "according", "due", "because", "although", "despite",
        "whereas", "while", "rather", "such", "result",
        "terms", "order", "basis", "effect", "effects",
        "associated", "related", "likely", "lead", "leads",
        "caused", "causes", "process", "increase", "decrease",
        "contrast", "addition", "compared", "similar", "different"
    }

    if phrase in always_good_phrases:
        return True

    if phrase in weak_phrases:
        return False

    # Trigram ve quadgramlarda phrase sonda edat/article ile bitiyorsa yarım kalmış olabilir.
    # Bigramlarda bunu uygulamıyoruz çünkü "according to", "due to", "associated with" gibi
    # iyi bigramlar edatla biter.
    if ngram_type in ["trigram", "quadgram"] and words[-1] in weak_ends:
        return False

    # Bigramlarda zayıf başlangıçları büyük ölçüde ele
    if ngram_type == "bigram" and words[0] in weak_starts:
        return False

    # Trigram/quadgramlarda da zayıf başlangıçları ele,
    # ancak phrase içinde useful word varsa izin ver.
    if ngram_type in ["trigram", "quadgram"]:
        if words[0] in weak_starts and not any(w in useful_words for w in words):
            return False

    # En az bir öğretici işaret taşısın
    if words[0] in useful_starts:
        return True

    if any(w in useful_words for w in words):
        return True

    # Bigramlarda "associated with", "related to", "lead to" gibi yapılar
    if len(words) == 2 and words[1] in {"to", "with", "of", "for", "from", "by", "as"}:
        return True

    return False

def generate_ngram_practice_questions(
    ngram_model,
    quiz_size=10,
    ngram_types=None,
    min_freq=2,
    seed=42
):
    """
    N-gram phrase'lerden otomatik boşluk doldurma practice soruları üretir.

    Örnek soru:
    according ----
    A) from
    B) to
    C) in
    D) with
    E) by

    Parametreler:
    - ngram_model: NgramModel nesnesi
    - quiz_size: 10 veya 50 gibi soru sayısı
    - ngram_types: ['bigram', 'trigram', 'quadgram']
    - min_freq: phrase corpus'ta en az kaç kez geçmeli
    - seed: aynı quiz'i tekrar üretmek için sabit random seed

    Döndürür:
    [
        {
            "id": 1,
            "question_type": "ngram_practice",
            "ngram_type": "bigram",
            "question_text": "according ----",
            "left_context": "according",
            "right_context": "",
            "options": {"A": "...", ...},
            "correct_answer": "B",
            "correct_word": "to",
            "source_phrase": "according to",
            "frequency": 38
        }
    ]
    """
    random.seed(seed)

    if ngram_types is None:
        ngram_types = ["bigram", "trigram", "quadgram"]

    all_candidates = []

    for ngram_type in ngram_types:

        source = get_source_for_ngram_type(ngram_model, ngram_type)

        # Önce useful phrase fonksiyonu varsa onu kullan.
        # Yoksa doğrudan Counter üzerinden devam et.
        if hasattr(ngram_model, "get_useful_phrases"):
            useful_phrases = ngram_model.get_useful_phrases(
                n_type=ngram_type,
                top_k=300,
                min_freq=min_freq
            )

            for item in useful_phrases:
                phrase = item["phrase"]
                words = phrase.split()

                if len(words) < 2:
                    continue
                if not is_good_practice_phrase(words, ngram_type):
                    continue

                # all_candidates.append({
                #     "words": words,
                #     "phrase": phrase,
                #     "frequency": item.get("frequency", 0),
                #     "ngram_type": ngram_type
                # })
                all_candidates.append({
                    "words": words,
                    "phrase": phrase,
                    "frequency": item.get("frequency", 0),
                    "score": item.get("score", item.get("frequency", 0)),
                    "ngram_type": ngram_type
                })

        else:
            for ngram, freq in source.items():
                if freq < min_freq:
                    continue

                words = list(ngram)

                if len(words) < 2:
                    continue

                

                if not is_good_practice_phrase(words, ngram_type):
                    continue

                phrase = " ".join(words)
            #     all_candidates.append({
            #     "words": words,
            #     "phrase": phrase,
            #     "frequency": freq,
            #     "score": freq,
            #     "ngram_type": ngram_type
            # })
                
                all_candidates.append({
                "words": words,
                "phrase": phrase,
                "frequency": freq,
                "score": freq,
                "ngram_type": ngram_type
            })
                # all_candidates.append({
                #     "words": words,
                #     "phrase": phrase,
                #     "frequency": freq,
                #     "ngram_type": ngram_type
                # })

    # Frekansa göre yüksekten düşüğe sırala
    # all_candidates.sort(
    #     key=lambda item: item["frequency"],
    #     reverse=True
    # )

    all_candidates.sort(
    key=lambda item: (item.get("score", 0), item.get("frequency", 0)),
    reverse=True
)

    # Distractor havuzu: tüm n-gramlardaki kelimeler
    all_words = []

    for item in all_candidates:
        all_words.extend(item["words"])

    all_words = list(set([
        word for word in all_words
        if len(word) > 1 and re.match(r"^[a-z]+$", word)
    ]))

    questions = []
    used_phrases = set()

    for item in all_candidates:

        if len(questions) >= quiz_size:
            break

        phrase = item["phrase"]

        if phrase in used_phrases:
            continue

        words = item["words"]
        blank_index = choose_blank_index(words)

        if blank_index >= len(words):
            continue

        correct_word = words[blank_index]

        # Aynı pozisyondaki kelimeler daha iyi distractor olur.
        positional_pool = []

        for other in all_candidates:
            other_words = other["words"]

            if len(other_words) > blank_index:
                positional_pool.append(other_words[blank_index])

        distractor_pool = positional_pool + all_words

        options, correct_letter = make_options(correct_word, distractor_pool)

        if not options or not correct_letter:
            continue

        question_text = build_question_text_from_phrase(words, blank_index)

        left_context = " ".join(words[:blank_index])
        right_context = " ".join(words[blank_index + 1:])

        question = {
            "id": len(questions) + 1,
            "question_type": "ngram_practice",
            "ngram_type": item["ngram_type"],
            "question_text": question_text,
            "left_context": left_context,
            "right_context": right_context,
            "options": options,
            "correct_answer": correct_letter,
            "correct_word": correct_word,
            "source_phrase": phrase,
            "frequency": item["frequency"],
        }

        questions.append(question)
        used_phrases.add(phrase)

    return questions


def save_ngram_practice_quiz(
    ngram_model,
    quiz_size=10,
    output_path=None,
    min_freq=2,
    seed=42
):
    """
    N-gram phrase'lerden practice quiz üretir ve JSON olarak kaydeder.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "test_data",
            f"ngram_practice_{quiz_size}.json"
        )

    questions = generate_ngram_practice_questions(
        ngram_model=ngram_model,
        quiz_size=quiz_size,
        min_freq=min_freq,
        seed=seed
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"{quiz_size} soruluk n-gram practice quiz kaydedildi: {output_path}")

    return questions


def evaluate_student_answers(questions, student_answers):
    """
    Öğrencinin cevaplarını kontrol eder.

    questions:
    [
        {
            "id": 1,
            "correct_answer": "B",
            ...
        }
    ]

    student_answers:
    {
        "1": "B",
        "2": "A"
    }

    Döndürür:
    {
        "total": 10,
        "correct": 8,
        "wrong": 2,
        "score_pct": "80.0%",
        "results": [...]
    }
    """
    correct = 0
    results = []

    for question in questions:
        q_id = str(question["id"])

        student_answer = student_answers.get(q_id)
        correct_answer = question.get("correct_answer")

        is_correct = student_answer == correct_answer

        if is_correct:
            correct += 1

        result = {
            "id": question["id"],
            "question_text": question.get("question_text", ""),
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "correct_word": question.get("correct_word"),
            "source_phrase": question.get("source_phrase"),
            "frequency": question.get("frequency"),
            "ngram_type": question.get("ngram_type"),
        }

        results.append(result)

    total = len(questions)
    wrong = total - correct
    accuracy = correct / total if total > 0 else 0

    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "score": round(accuracy, 4),
        "score_pct": f"{accuracy:.1%}",
        "results": results,
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    build_test_set()