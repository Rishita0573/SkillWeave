import pdfplumber
import csv
import re
from pathlib import Path

# ---------- PATHS ----------
ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)

PDFS = [
    PDF_DIR / "NCO_2015_Vol_II.pdf",
    PDF_DIR / "NCO_Vol_II-B-2015.pdf",
]

OUT_FILE = OUT_DIR / "nco_2015_FINAL.csv"

# ---------- PATTERNS ----------
# STRICT: 4-digit code + title only
HEADER_RE = re.compile(r"^([1-9][0-9]{3})\s{1,}([A-Za-z][A-Za-z ,&()/\-]+)$")

def clean(line):
    return re.sub(r"\s+", " ", line).strip()

# ---------- EXTRACTION ----------
def extract():
    rows = []
    current_code = None
    current_title = None
    current_desc = []

    for pdf_path in PDFS:
        print("Processing:", pdf_path.name)
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2)
                if not text:
                    continue

                for raw in text.split("\n"):
                    line = clean(raw)
                    if not line:
                        continue

                    # Check if this line starts a NEW occupation
                    m = HEADER_RE.match(line)
                    if m:
                        # save previous
                        if current_code and current_desc:
                            rows.append([
                                current_code,
                                current_title,
                                " ".join(current_desc)
                            ])

                        code, title = m.groups()

                        # reject years / garbage
                        if int(code) < 1111 or int(code) > 9629:
                            current_code = None
                            current_desc = []
                            continue

                        current_code = code
                        current_title = title.strip()
                        current_desc = []
                        continue

                    # Otherwise: description line
                    if current_code:
                        current_desc.append(line)

    # flush last
    if current_code and current_desc:
        rows.append([current_code, current_title, " ".join(current_desc)])

    # ---------- CLEANING ----------
    final = {}
    for code, title, desc in rows:
        desc = re.sub(r"\d{4}\.\d+", "", desc)      # remove sub-codes
        desc = re.sub(r"\s+", " ", desc).strip()

        if len(desc) < 30:
            continue  # junk description

        if code not in final:
            final[code] = [code, title, desc]

    # ---------- SAVE ----------
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nco_code", "title", "description"])
        for k in sorted(final):
            writer.writerow(final[k])

    print("\nDONE")
    print("Total occupations:", len(final))
    print("Saved to:", OUT_FILE)

if __name__ == "__main__":
    extract()
