
import re
import json
from pathlib import Path

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"""
    (?:\+91[\s-]?)?[6-9]\d{9}
    |
    0\d{2,5}[-\s]?\d{6,8}
    |
    \d{10}
"""
ADDRESS_REGEX = r".{5,120}?\b\d{6}\b"

BAD_ADDRESS_PATTERNS = [
    r"\bper km\b",
    r"\bNos\.?\b",
    r"GEM/\d+",
    r"\bFY ?20\d{2}\b",
    r"\bfinancial\b",
    r"\bPAT\b",
    r"minimum of",
    r"\bMTBF\b",
    r"\bLakhs?\b",
    r"\bCrore\b",
    r"\bcompleted\b",
]

ADDRESS_KEYWORDS = [
    "road","rd","marg","nagar","place","sector","colony","bhawan","bhavan",
    "gate","lane","area","complex","building","salai","po","p.o","plot",
    "street","society","city","point","market","cantt","airport","tower",
    "circle","bypass","vihar","ghar","kunj","khas","centre"
]


def clean_text(text: str) -> str:
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)
    text = text.replace("\u00A0", " ").replace("\u202F", " ").replace("\u2009", " ")
    text = text.encode("ascii", "ignore").decode()
    return text


def extract_phone_numbers(text):
    matches = re.findall(PHONE_REGEX, text, flags=re.VERBOSE)
    cleaned = []
    for ph in matches:
        p = ph.replace(" ", "").replace("-", "").replace("/", "").replace("\\n", "")
        safe_p = re.escape(p)
        if re.search(rf"{safe_p}\\. (pdf|docx|txt|jpg)", text, flags=re.I):
            continue
        if len(p) < 10:
            continue
        if (len(p) == 10 and p[0] in "6789") or (len(p) >= 11 and p.startswith("0")) or p.startswith("+91"):
            cleaned.append(p)
    return sorted(set(cleaned))

def extract_addresses(text: str) -> list:
    text = clean_text(text)
    raw_matches = re.findall(ADDRESS_REGEX, text, flags=re.IGNORECASE)
    cleaned = []

    for addr in raw_matches:
        a = addr.strip(" ,.-\n\t")

        if len(a) < 10:
            continue

        if not any(kw.lower() in a.lower() for kw in ADDRESS_KEYWORDS):
            continue

        if any(re.search(bp, a, flags=re.IGNORECASE) for bp in BAD_ADDRESS_PATTERNS):
            continue

        cleaned.append(a)

    return sorted(set(cleaned))


def extract_from_text(text):
    emails = sorted(set(re.findall(EMAIL_REGEX, text)))
    phones = extract_phone_numbers(text)
    addresses = extract_addresses(text)
    return emails, phones, addresses

def main():
    base = Path(".")
    if not base.exists():
        print("ERROR: base folder not found.")
        return

    folders = {}
    all_emails, all_phones, all_addresses = set(), set(), set()

    patterns = ["*.pdf.txt", "*.docx.txt", "*.txt"]
    visited_files = set()

    for pattern in patterns:
        for path in base.rglob(pattern):
            if not path.is_file():
                continue

            normalized = str(path.resolve())
            if normalized in visited_files:
                continue
            visited_files.add(normalized)

            folder = path.parent.name
            file = path.name
            text = path.read_text(errors="ignore")

            emails, phones, addresses = extract_from_text(text)

            if not (emails or phones or addresses):
                continue

        all_emails.update(emails)
        all_phones.update(phones)
        all_addresses.update(addresses)

        if folder not in folders:
            folders[folder] = {"folder": folder, "files": []}

        folders[folder]["files"].append({
            "file_name": file,
            "emails": emails,
            "phones": phones,
            "addresses": addresses,
        })

    result = {
        "summary": {
            "all_emails": sorted(all_emails),
            "all_phones": sorted(all_phones),
            "all_addresses": sorted(all_addresses)
        },
        "folders": list(folders.values())
    }

    Path("extracted_results.json").write_text(
        json.dumps(result, indent=4)
    )
    
    print("\n===== SUMMARY REPORT =====")
    print("Total Emails Found      :", len(all_emails))
    print("Total Phones Found      :", len(all_phones))
    print("Total Addresses Found   :", len(all_addresses))

    prev_data_path = Path('extracted_results.json')
    if prev_data_path.exists():
        try:
            prev_data = json.loads(prev_data_path.read_text())
            prev_emails = set(prev_data.get('summary', {}).get('all_emails', []))
            prev_phones = set(prev_data.get('summary', {}).get('all_phones', []))
            prev_addresses = set(prev_data.get('summary', {}).get('all_addresses', []))

            new_emails = all_emails - prev_emails
            new_phones = all_phones - prev_phones
            new_addresses = all_addresses - prev_addresses

            print("\n===== NEW ITEMS FOUND =====")
            print("New Emails      :", len(new_emails))
            print("New Phones      :", len(new_phones))
            print("New Addresses   :", len(new_addresses))

        except Exception as e:
            print("Error comparing previous data:", e)
    else:
        print("First run: no previous data to compare.")

    print("Extraction complete.")

if __name__ == "__main__":
    main()
