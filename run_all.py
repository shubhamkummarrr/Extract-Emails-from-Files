import os
import sys
import subprocess
import platform
from pathlib import Path

print("=== EmailPhoneExtraction Automation Started ===")

# -----------------------------------------
# Define script directory and switch to it
# -----------------------------------------
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

print("[INFO] Script directory:", script_dir)

# -----------------------------------------
# Clone or Pull from GitHub
# -----------------------------------------
print("[INFO] Checking GitHub repository...")

repo_url = "https://github.com/shubhamkummarrr/GitHub-to-Database-Automation-Pipeline.git"
branch_name = "main"
clone_dir = script_dir / "GitHub-to-Database-Automation-Pipeline"

if not clone_dir.exists():
    print("[INFO] Cloning repository...")
    subprocess.check_call(["git", "clone", repo_url])

    print(f"[INFO] Switching to branch {branch_name}...")
    subprocess.check_call(["git", "-C", str(clone_dir), "checkout", branch_name])

else:
    print("[INFO] Repository already exists. Pulling latest changes...")
    subprocess.check_call(["git", "-C", str(clone_dir), "pull"])

    print(f"[INFO] Ensuring branch {branch_name} is active...")
    subprocess.check_call(["git", "-C", str(clone_dir), "checkout", branch_name])


# -----------------------------------------
# Move inside Extract-Emails-from-Files folder
# -----------------------------------------
tms_path = script_dir / "GitHub-to-Database-Automation-Pipeline"

if tms_path.exists():
    print("[INFO] Switching into GitHub-to-Database-Automation-Pipeline folder...")
    os.chdir(tms_path)
else:
    print("[WARNING] Extract-Emails-from-Files folder NOT found. Running in current directory.")


# -----------------------------------------
# 1) Create requirements.txt
# -----------------------------------------
print("[INFO] Creating requirements.txt...")

req_text = "mysql-connector-python==8.2.0\n"

with open("requirements.txt", "w") as f:
    f.write(req_text)


# -----------------------------------------
# 2) Create Virtual Environment
# -----------------------------------------
print("[INFO] Checking virtual environment...")

if not Path("venv").exists():
    print("[INFO] Creating venv...")
    subprocess.check_call([sys.executable, "-m", "venv", "venv"])
else:
    print("[INFO] venv already exists.")


# -----------------------------------------
# 3) Activate venv (Cross-platform)
# -----------------------------------------
print("[INFO] Activating venv & installing requirements...")

if platform.system() == "Windows":
    pip_path = "venv\\Scripts\\pip.exe"
    python_path = "venv\\Scripts\\python.exe"
else:
    pip_path = "venv/bin/pip"
    python_path = "venv/bin/python"

try:
    os.chmod(pip_path, 0o755)
except:
    pass

subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])


# -----------------------------------------
# 4) SCAN SCRIPT (write scan_contacts.py)
# -----------------------------------------
print("[INFO] Writing scan_contacts.py...")

scan_script = r'''
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
    base = Path("TenderAI")
    if not base.exists():
        print("ERROR: TenderAI folder not found.")
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

    prev_data_path = Path("extracted_results.json")
    if prev_data_path.exists():
        try:
            prev_data = json.loads(prev_data_path.read_text())
            prev_emails = set(prev_data.get("summary", {}).get("all_emails", []))
            prev_phones = set(prev_data.get("summary", {}).get("all_phones", []))
            prev_addresses = set(prev_data.get("summary", {}).get("all_addresses", []))

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
'''

with open("scan_contacts.py", "w") as f:
    f.write(scan_script)


# -----------------------------------------
# 5) INSERT SCRIPT (duplicate-safe)
# -----------------------------------------
print("[INFO] Writing insert_contacts.py...")

insert_script = r'''
import mysql.connector
import json

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="SHUB@@1234",
    database="emails_db"
)

cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS contact_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folder VARCHAR(255),
    file VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT
)
""")

data = json.load(open("extracted_results.json"))


def file_exists(folder, file):
    cursor.execute(
        "SELECT 1 FROM contact_data WHERE folder=%s AND file=%s LIMIT 1",
        (folder, file)
    )
    return cursor.fetchone() is not None


def insert_row(folder, file, email=None, phone=None, address=None):
    cursor.execute("""
        INSERT INTO contact_data (folder, file, email, phone, address)
        VALUES (%s, %s, %s, %s, %s)
    """, (folder, file, email, phone, address))


for folder_obj in data["folders"]:
    folder = folder_obj["folder"]

    for file_obj in folder_obj["files"]:
        file = file_obj["file_name"]

        if file_exists(folder, file):
            print("Skipping duplicate:", folder, file)
            continue

        emails = file_obj["emails"]
        phones = file_obj["phones"]
        addresses = file_obj["addresses"]

        for e in emails:
            insert_row(folder, file, email=e)
        for p in phones:
            insert_row(folder, file, phone=p)
        for a in addresses:
            insert_row(folder, file, address=a)

conn.commit()
cursor.close()
conn.close()

print("Insert complete!")
'''

with open("insert_contacts.py", "w") as f:
    f.write(insert_script)


# -----------------------------------------
# 6) Run scripts
# -----------------------------------------
print("[INFO] Running extraction...")
subprocess.check_call([python_path, "scan_contacts.py"])

print("[INFO] Running DB insert...")
subprocess.check_call([python_path, "insert_contacts.py"])

print("=== EmailPhoneExtraction Automation Finished Successfully ===")