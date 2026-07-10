from pathlib import Path
import pandas as pd
import re
import sys

# -----------------------------
# Locate knowledge_base folder
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "knowledge_base"

print("=" * 60)
print("Current Working Directory :", Path.cwd())
print("Script Location           :", BASE_DIR)
print("Knowledge Base Folder     :", KB_DIR)
print("Folder Exists             :", KB_DIR.exists())
print("=" * 60)

if not KB_DIR.exists():
    print("\nERROR: knowledge_base folder not found!")
    sys.exit()

files = list(KB_DIR.glob("*.txt"))

print(f"\nFound {len(files)} KB files.\n")

if len(files) == 0:
    print("No .txt files found inside knowledge_base!")
    sys.exit()


# -----------------------------
# Extract helper
# -----------------------------
def extract(text, field):
    """
    Extracts fields like:
    TITLE:
    **TITLE:**
    TITLE: xyz
    **TITLE:** xyz
    """

    pattern = rf"\**{field}\**\s*:?\s*(.+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        return match.group(1).strip()

    return "Not Found"


# -----------------------------
# Read all KB files
# -----------------------------
records = []

for file in files:

    text = file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    records.append({
        "File": file.name,
        "Title": extract(text, "TITLE"),
        "Category": extract(text, "CATEGORY"),
        "Priority": extract(text, "PRIORITY"),
        "Length": len(text)
    })


# -----------------------------
# Create DataFrame
# -----------------------------
df = pd.DataFrame(records)

print("\nFirst 10 Documents\n")
print(df.head(10))

print("\n" + "=" * 60)
print("Knowledge Base Summary")
print("=" * 60)

print(f"Total Documents : {len(df)}")

print("\nCategory Distribution\n")
print(df["Category"].value_counts(dropna=False))

print("\nPriority Distribution\n")
print(df["Priority"].value_counts(dropna=False))

print("\nTop 10 Largest Documents\n")
print(df.sort_values("Length", ascending=False).head(10))

# -----------------------------
# Save CSV
# -----------------------------
csv_path = BASE_DIR / "kb_audit.csv"

df.to_csv(csv_path, index=False)

print(f"\nAudit saved successfully to:\n{csv_path}")