import os
import re
import glob
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# -----------------------------
# Create/Clean knowledge base
# -----------------------------
os.makedirs("knowledge_base", exist_ok=True)



# -----------------------------
# Load filtered dataset
# -----------------------------
df = pd.read_csv("it_support_dataset.csv")

# -----------------------------
# Balanced Sampling
# -----------------------------
DOCS_PER_QUEUE = 35

sample_list = []

for queue in df["queue"].unique():

    queue_df = df[df["queue"] == queue]

    sample = queue_df.sample(
        n=min(DOCS_PER_QUEUE, len(queue_df)),
        random_state=42
    )

    sample_list.append(sample)

sample_df = pd.concat(sample_list, ignore_index=True)

# Batch generation (change these ranges as needed)
sample_df = sample_df.iloc[100:140].reset_index(drop=True)

print("\nSelected Documents:\n")
print(sample_df["queue"].value_counts())

print(f"\nTotal Documents: {len(sample_df)}")


# -----------------------------
# Generate KB
# -----------------------------
for index, row in sample_df.iterrows():

    ticket = f"""
SUBJECT:
{row['subject']}

DESCRIPTION:
{row['body']}

SUPPORT RESPONSE:
{row['answer']}

QUEUE:
{row['queue']}

PRIORITY:
{row['priority']}
"""

    prompt = f"""
You are an Enterprise IT Knowledge Engineer.

Convert this support ticket into a reusable Enterprise IT
knowledge-base article.

IMPORTANT:

If the ticket is NOT about enterprise IT support,
reply ONLY with:

SKIP

Enterprise IT includes:

- Passwords
- Login
- Authentication
- MFA
- VPN
- WiFi
- Networking
- DNS
- Firewall
- Servers
- Databases
- Software
- Windows
- Linux
- Email
- Outlook
- Cloud
- Azure
- AWS
- Docker
- Kubernetes
- Hardware
- Security
- Access Permissions

Remove:

- Greetings
- Customer names
- Email signatures
- Polite customer support language
- Healthcare-specific context
- Marketing context
- Finance context
- Business context

Return ONLY:

TITLE:
CATEGORY:
PROBLEM:
COMMON CAUSES:
TROUBLESHOOTING STEPS:
ESCALATION CONDITION:
ESCALATE TO:
PRIORITY:

Maximum 180 words.

Ticket:

{ticket}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        text = response.text.strip()

        if text.upper() == "SKIP":
            print(f"Skipped ticket {index+1}")
            continue

        # -----------------------------
        # Create filename from TITLE
        # -----------------------------
        title = f"kb_{index+1}"

        for line in text.splitlines():
            if line.upper().startswith("TITLE"):
                title = line.split(":", 1)[1].strip()
                break

        filename = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            title.lower()
        ).strip("_")

        filepath = f"knowledge_base/{filename}.txt"

        # Prevent duplicate filenames
        counter = 1
        original = filepath

        while os.path.exists(filepath):
            filepath = original.replace(
                ".txt",
                f"_{counter}.txt"
            )
            counter += 1

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(text)

        print(f"Saved: {os.path.basename(filepath)}")

        # Avoid API rate limits
        time.sleep(30)

    except Exception as e:

        print(f"\nError on ticket {index+1}")
        print(e)

        # Wait before next request
        time.sleep(20)

print("\nKnowledge Base generation completed!")