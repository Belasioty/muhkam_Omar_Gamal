import fitz
import re
import json
import sys
from dateutil import parser as dateparser


RULES = [
    ("CET1_Ratio", re.compile(r"\bCET1\s*ratio\b", re.I), None),
    ("Tier1_Ratio", re.compile(r"\bTier\s*1\s*ratio\b", re.I), None),
    ("RWA_Total", re.compile(r"\bRWA\b", re.I), None),

   
    ("Percent", re.compile(r"\b\d+(?:\.\d+)?%\b", re.I),
        lambda t: float(t.strip("%"))),

   
    ("Amount", re.compile(r"(?:£|\$|EUR|USD|GBP)?\s?\d[\d,]*(?:\.\d+)?\s?(?:m|bn|k)?", re.I),
        lambda t: (
            lambda nums: (
                float(nums[0]) *
                (1_000_000 if t.lower().strip().endswith("m")
                 else 1_000_000_000 if t.lower().strip().endswith("bn")
                 else 1_000 if t.lower().strip().endswith("k")
                 else 1)
            ) if nums else None
        )(re.findall(r"\d+(?:\.\d+)?", t.replace(",", "")))),

  # NOTE: output date will be in YYYY_MM_DD format     
    ("Date", re.compile(
        r"\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}"
        r"|\d{4}-\d{2}-\d{2}", re.I),
        lambda t: (
            lambda dt: dt.date().isoformat() if dt else None
        )(dateparser.parse(t, dayfirst=True) if t else None)
    ),

    # Currency 
    ("Currency", re.compile(r"\b(GBP|USD|EUR|AED)\b", re.I), None)
]


def get_text(path):
    try:
        doc = fitz.open(path)
        text = []
        for page in doc:
            text.append(page.get_text("text"))
        doc.close()
        return "\n".join(text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)


def extract(text):
    ents = []
    for etype, pat, norm in RULES:
        for m in pat.finditer(text):
            ent = {
                "entity": m.group().strip(),
                "type": etype,
                "start": m.start(),
                "end": m.end()
            }
            if norm:
                try:
                    val = norm(m.group())
                except Exception:
                    val = None
                if val is not None:
                    ent["value"] = val
            ents.append(ent)
    return sorted(ents, key=lambda x: x["start"])


# Runner part
if __name__ == "__main__":
    print("🚀 Runner started")

    pdf = "ICAAP_en_uk_report (1).pdf"
    print(f"📂 Trying to open: {pdf}")

    text = get_text(pdf)

    if not text:
        print("⚠️ No text extracted — maybe the PDF is empty or unreadable.")
    else:
        print(f"📄 Extracted {len(text)} characters from PDF")
        entities = extract(text)
        print(f"🔍 Found {len(entities)} entities")
        print(json.dumps(entities, indent=2))


