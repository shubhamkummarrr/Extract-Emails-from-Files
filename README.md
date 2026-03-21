# GitHub to Database Automation Pipeline

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey)
![Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Overview

A fully automated, single-command pipeline that clones a GitHub repository,
scans all text files inside it, extracts emails and phone numbers using regex,
and inserts the results into a MySQL database — with duplicate protection built in.

> Tested and working on Windows, macOS, and Linux.

---

## Live Output

```
=== EmailPhoneExtraction Automation Started ===
[INFO] Checking GitHub repository...
[INFO] Cloning repository...
[INFO] Creating venv...
[INFO] Installing requirements...
[INFO] Writing scan_contacts.py...
[INFO] Writing insert_contacts.py...
[INFO] Running extraction...

===== SUMMARY REPORT =====
Total Emails Found      : 39
Total Phones Found      : 31
Total Addresses Found   : 1

===== NEW ITEMS FOUND =====
New Emails      : 4
New Phones      : 2
New Addresses   : 0

Extraction complete.
[INFO] Running DB insert...
Insert complete!
=== EmailPhoneExtraction Automation Finished Successfully ===
```

---

## How It Works

```
python run_all.py
       |
       |-- Step 1: Clone / Pull from GitHub
       |
       |-- Step 2: Create venv + install mysql-connector-python
       |
       |-- Step 3: Generate scan_contacts.py
       |               Scans TenderAI/ folder
       |               Extracts emails, phones, addresses
       |               Saves to extracted_results.json
       |
       |-- Step 4: Generate insert_contacts.py
       |               Reads extracted_results.json
       |               Skips already-inserted files (duplicate-safe)
       |               Inserts new rows into MySQL
       |
       |-- Done
```

---

## Project Structure

```
GitHub-to-Database-Automation-Pipeline/
|
|-- run_all.py                    <- Single entry point. Run this file.
|
|-- TenderAI/                     <- Place your .txt files here
|   |-- construction_tender.txt
|   |-- supplier_registration.txt
|   |-- ngo_field_report.txt
|   |-- it_vendor_proposal.txt
|   |-- govt_circular.txt
|
|-- scan_contacts.py              <- Auto-generated at runtime
|-- insert_contacts.py            <- Auto-generated at runtime
|-- extracted_results.json        <- Auto-generated output
|-- requirements.txt              <- Auto-generated
|-- config.ini                    <- Your DB credentials (never committed)
|-- .gitignore
|-- README.md
```

---

## Quickstart

### Prerequisites

- Python 3.8+
- Git
- MySQL running locally

### 1. Clone this repo

```bash
git clone https://github.com/shubhamkummarrr/GitHub-to-Database-Automation-Pipeline.git
cd GitHub-to-Database-Automation-Pipeline
```

### 2. Create the database

```sql
CREATE DATABASE emails_db;
```

### 3. Fill in config.ini

```ini
[database]
host     = localhost
user     = root
password = YOUR_PASSWORD_HERE
database = emails_db
```

> config.ini is in .gitignore — credentials are never pushed to GitHub.

### 4. Run

```bash
python run_all.py
```

Everything else is handled automatically.

---

## What Gets Extracted

| Type | Examples |
|---|---|
| Email | `contact@company.gov.in`, `admin@example.in` |
| Phone | `9876543210`, `+91 9876543210`, `0612-2345678` |
| Address | Any line containing a 6-digit Indian pincode with address keywords |

### Smart Filtering

- Skips files already in the database (no duplicate rows)
- Skips phone numbers that look like filenames (`1234567890.pdf`)
- Filters out false positives in addresses (financial figures, distances, etc.)
- Deduplicates all values before inserting

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS contact_data (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    folder     VARCHAR(255),
    file       VARCHAR(255),
    email      VARCHAR(255),
    phone      VARCHAR(50),
    address    TEXT
);
```

Table is created automatically on first run — no manual setup needed.

---

## extracted_results.json

```json
{
    "summary": {
        "all_emails": ["procurement@pwd.bihar.gov.in", "admin@example.in"],
        "all_phones": ["9876543210", "8800991122"],
        "all_addresses": ["Hajipur Road, Vaishali, Bihar 844101"]
    },
    "folders": [
        {
            "folder": "TenderAI",
            "files": [
                {
                    "file_name": "construction_tender.txt",
                    "emails": ["procurement@pwd.bihar.gov.in"],
                    "phones": ["9876543210"],
                    "addresses": ["Hajipur Road, Vaishali, Bihar 844101"]
                }
            ]
        }
    ]
}
```

---

## Adding More Files to Test

Drop any `.txt` file into the `TenderAI/` folder and run again:

```
TenderAI/
|-- your_new_file.txt    <- paste any text with emails/phones
```

```bash
python run_all.py
```

New data gets extracted and inserted. Already-processed files are skipped automatically.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.8+ | Core language |
| `re` | Regex-based extraction |
| `subprocess` | Git clone/pull, venv creation |
| `pathlib` | Cross-platform file handling |
| `mysql-connector-python` | MySQL insert |
| `json` | Intermediate result storage |
| `venv` | Isolated environment |

---

## Cross-Platform

venv paths are auto-detected per OS — no changes needed.

| OS | pip path | python path |
|---|---|---|
| Windows | `venv\Scripts\pip.exe` | `venv\Scripts\python.exe` |
| Mac / Linux | `venv/bin/pip` | `venv/bin/python` |

---

## .gitignore

```
venv/
config.ini
extracted_results.json
__pycache__/
*.pyc
*.log
```

---

## Author

**Shubham Kumar**
GitHub: [@shubhamkummarrr](https://github.com/shubhamkummarrr)

---

## License

MIT License — free to use and modify.
