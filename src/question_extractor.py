"""
question_extractor.py — YÖKDİL PDF'lerinden boşluk doldurma (cloze) sorularını çıkarır.
Cevap anahtarını her PDF'in son sayfasından okur.
"""

import pdfplumber
import re
import os
import glob
import json


def extract_answer_key(pdf_path):
    """
    PDF'in son sayfasındaki cevap anahtarını okur.
    Döndürür: {soru_no: 'A'|'B'|'C'|'D'|'E', ...}
    """
    answers = {}

    with pdfplumber.open(pdf_path) as pdf:
        last_page = pdf.pages[-1]
        text = last_page.extract_text()

        if not text:
            return answers

        # Çeşitli ÖSYM cevap anahtarı formatlarını yakala
        # Format: "1. A", "1 A", "1-A", "1  A" vb.
        pattern = r'(\d+)\s*[.\-)\s]\s*([A-E])\b'
        matches = re.findall(pattern, text)

        for num_str, letter in matches:
            num = int(num_str)
            if 1 <= num <= 80:
                answers[num] = letter

    return answers


def extract_cloze_questions(pdf_path):
    """
    Bir YÖKDİL PDF'inden boşluk doldurma sorularını çıkarır.
    Boşluk '----' (4+ tire) ile işaretlidir.
    """
    questions = []
    all_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        # Son sayfa (cevap anahtarı) hariç tüm sayfaları oku
        for page in pdf.pages[:-1]:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

    # Soru sınırlarını bul: sayı + nokta ile başlayan bloklar
    # Örn: "1. The experiment ---- that..."
    question_blocks = re.split(r'(?:^|\n)\s*(\d+)\.\s', all_text)

    # split sonucu: [önceki_metin, soru_no_1, metin_1, soru_no_2, metin_2, ...]
    for i in range(1, len(question_blocks) - 1, 2):
        try:
            q_num = int(question_blocks[i])
        except ValueError:
            continue

        q_text = question_blocks[i + 1]

        # Sadece boşluk doldurma sorularını al (---- içerenler)
        if not re.search(r'-{3,}', q_text):
            continue

        # Şıkları çıkar: A) ... B) ... C) ... D) ... E) ...
        option_pattern = r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)\s|$)'
        option_matches = re.findall(option_pattern, q_text, re.DOTALL)

        if len(option_matches) < 5:
            continue

        options = {}
        for letter, opt_text in option_matches[:5]:
            cleaned = re.sub(r'\s+', ' ', opt_text).strip()
            options[letter] = cleaned

        # Soru cümlesini şıklardan ayır
        q_sentence = re.split(r'\s*A\)', q_text)[0].strip()
        q_sentence = re.sub(r'\s+', ' ', q_sentence)

        # Sol ve sağ bağlamı ayır (---- etrafında)
        parts = re.split(r'-{3,}', q_sentence, maxsplit=1)
        left_context = parts[0].strip() if len(parts) > 0 else ""
        right_context = parts[1].strip() if len(parts) > 1 else ""

        questions.append({
            'id': q_num,
            'source': os.path.basename(pdf_path),
            'question_text': q_sentence,
            'left_context': left_context,
            'right_context': right_context,
            'options': options,
            'correct_answer': None
        })

    return questions


def build_test_set(data_dir=None, output_path=None):
    """
    Tüm YÖKDİL PDF'lerinden cloze sorularını çıkarıp JSON test seti oluşturur.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'test_data', 'cloze_test_set.json'
        )

    pattern = os.path.join(data_dir, "YOKDIL*.pdf")
    pdf_files = sorted(glob.glob(pattern))

    all_questions = []
    global_id = 1

    for pdf_path in pdf_files:
        basename = os.path.basename(pdf_path)
        print(f"\n{'='*50}")
        print(f"{basename} işleniyor...")

        # Soruları çıkar
        questions = extract_cloze_questions(pdf_path)
        print(f"  -> {len(questions)} boşluk doldurma sorusu bulundu")

        # Cevap anahtarını çıkar
        answers = extract_answer_key(pdf_path)
        print(f"  -> {len(answers)} cevap anahtarı okundu")

        # Cevapları sorularla eşleştir
        for q in questions:
            if q['id'] in answers:
                q['correct_answer'] = answers[q['id']]
            q['original_id'] = q['id']
            q['id'] = global_id
            global_id += 1

        all_questions.extend(questions)

    # JSON olarak kaydet
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    answered = sum(1 for q in all_questions if q['correct_answer'])
    print(f"\n{'='*50}")
    print(f"SONUÇ: Toplam {len(all_questions)} soru çıkarıldı.")
    print(f"Cevaplı: {answered} | Cevapsız: {len(all_questions) - answered}")
    print(f"Kaydedildi: {output_path}")

    return all_questions


if __name__ == '__main__':
    build_test_set()
