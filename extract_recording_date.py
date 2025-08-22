# extract_recording_date.py
import spacy
from spacy.pipeline import EntityRuler
import dateparser.search
import re
import sys
import os
from typing import Literal

EntityLabel = Literal['CARDINAL', 'DATE', 'EVENT', 'FAC', 'GPE', 'LANGUAGE', 'LAW',
 'LOC', 'MONEY', 'NORP', 'ORDINAL', 'ORG', 'PERCENT',
 'PERSON', 'PRODUCT', 'QUANTITY', 'TIME', 'WORK_OF_ART']

nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.add_patterns([
    {
        "label": "DATE",
        "pattern": [{"TEXT": {"REGEX": r"\d{2}\.\d{2}\.\d{2}"}}]
    }
])

def extract_recording_date(note: str):
    os.environ['TZ'] = 'Asia/Tokyo'
    recorded_phrases = None
    # wordと\d{1,2}の間のカンマと複数スペースを1つのスペースに変換 August, 15, 1955 -> August 15, 1955
    note = re.sub(r"(\w+)\s*,\s*(\d{1,2})", r"\1 \2", note)
    for pattern in [
        r'(?:Recorded|Live|Recording).*?(?:\.(?!\d)|\n|$)',
        # 必要に応じて他のパターンを追加
    ]:
        recorded_phrases = re.findall(pattern, note, re.IGNORECASE)
        if recorded_phrases:
            date = extract_sub(recorded_phrases)
            if date:
                return date
    #hitしない場合、文全体を対象
    recorded_phrases =re.findall(r"(?:Recorded|Live|Recording).*", note, re.IGNORECASE | re.DOTALL)
    if recorded_phrases:
        date = extract_sub(recorded_phrases)
        if date:
            return date
    return None

def extract_sub(recorded_phrases: list):
   for phrase in recorded_phrases:
        doc = nlp(phrase)
        i = 0
        for ent in doc.ents:
            label: EntityLabel = ent.label_ 
            if label == "DATE":
                date_text = ent.text
                # 例: "May 11 & 12, 1984" → "May 11", "1984"
                match = re.search(r"(\w+\.? \d{1,2})(?!\d)[^,]*,?\s*(\d{4})", date_text)
                if match:
                    month_day, year = match.groups()
                    full_date = f"{month_day} {year}"
                    parsed = dateparser.parse(full_date)
                    print(f"dateparser: {date_text} -> {parsed}", file=sys.stderr, flush=True)
                    if parsed:
                        return parsed.strftime("%Y-%m-%d")
                else:
                     # 日付に年と月しか含まれていない場合、1日を補う
                    ent_text = ent.text
                    ent_match = re.search(r"([a-zA-Z]+)\s*,?\s*(\d{4})", ent_text)
                    if ent_match:
                        ent_text = f"{ent_match.group(1)} 01 {ent_match.group(2)}"
                        parsed = dateparser.parse(ent_text)
                        if parsed:
                            #log出力
                            print(f"dateparser: {ent.text} -> {parsed}", file=sys.stderr, flush=True)
                            return parsed.strftime("%Y-%m-%d")
                    # 年だけの場合、"01 01 {年}" として補完
                    ent_match = re.search(r"(\d{4})", ent_text)
                    if ent_match:
                        ent_text = f"01 01 {ent_match.group(1)}"
                    parsed = dateparser.parse(ent_text)
                    if parsed:
                        #log出力
                        print(f"dateparser: {ent.text} -> {parsed}", file=sys.stderr, flush=True)
                        return parsed.strftime("%Y-%m-%d")
                    #対象の次があって数字ならそれが年とみなす
                    if len(doc.ents) > i+1:
                        year = doc.ents[i+1].text
                        if re.match(r"\d{2,4}", year):
                            ent_text =  re.search(r"(\w+\.? \d{1,2})", ent_text)
                            ent_text = f"{ent_text.group(1)} {year}"
                            parsed = dateparser.parse(ent_text)
                            #log出力
                            print(f"dateparser: {ent.text} -> {parsed}", file=sys.stderr, flush=True)
                            if parsed:
                                return parsed.strftime("%Y-%m-%d")
            i += 1
        return None

def read_arg(i):
    arg = sys.argv[i]
    if arg.endswith(".txt"):
        with open(arg, "r", encoding="utf-8") as f:
            return f.read()
    return arg

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No input text provided", file=sys.stderr)
        sys.exit(1)

    input_text = read_arg(1)
    result = extract_recording_date(input_text.strip())

    if result:
        print(result)

 
