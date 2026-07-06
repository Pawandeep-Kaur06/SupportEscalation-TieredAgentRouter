import os
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# for model in client.models.list():
#     print(model.name)

# create output folder
os.makedirs("knowledge_base", exist_ok=True)

# load filtered dataset
df = pd.read_csv("it_support_dataset.csv")

# you don't need all 500 initially
df = df[70:100]

for index, row in df.iterrows():

    ticket = f"""
SUBJECT:
{row['subject']}

DESCRIPTION:
{row['body']}

EXISTING SUPPORT RESPONSE:
{row['answer']}

QUEUE:
{row['queue']}

PRIORITY:
{row['priority']}
"""

    prompt = f"""
Convert this IT support ticket into a structured
knowledge-base document.

Format:

TITLE:
CATEGORY:
PROBLEM:
COMMON CAUSES:
TROUBLESHOOTING STEPS:
ESCALATION CONDITION:
ESCALATE TO:
PRIORITY:

Keep the response under 200 words.

Ticket:
{ticket}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        filename = f"knowledge_base/kb_{index+1}.txt"

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(response.text)

        print(f"Saved {filename}")

        # avoid rate limits
        time.sleep(5)

    except Exception as e:
        print(f"Error on row {index}:")
        print(e)
        time.sleep(15)

    