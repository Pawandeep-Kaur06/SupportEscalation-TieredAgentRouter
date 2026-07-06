import os
from google import genai
from dotenv import load_dotenv

# Load API key
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Create output folder
os.makedirs("processed_docs", exist_ok=True)

# Process every file in raw_docs
for file in os.listdir("raw_docs"):

    # Skip non-text files
    if not file.endswith(".txt"):
        continue

    input_path = os.path.join("raw_docs", file)

    print(f"Processing: {file}")

    # Read file
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()


# Prompt
prompt = f"""
You are building a knowledge base for an AI-Powered IT Support Escalation System.

TASK:
Extract information from the IT support document and convert it into a structured support knowledge entry.

RULES:
- Preserve all technical information from the document.
- Do not hallucinate troubleshooting steps.
- You MAY infer:
    - CATEGORY
    - PRIORITY
    - RESOLUTION TIME
    - ESCALATION TEAM
  based on standard IT support practices.
- Keep the output concise and under 250 words.
- Use bullet points, not paragraphs.
- Output ONLY in the exact format below.

PRIORITY RULES:
- Low:
  Minor inconvenience, informational request.
- Medium:
  User productivity affected.
- High:
  Service disruption, security concern, or multiple users affected.
- Critical:
  Security breach, financial loss, data leak, server outage, or account compromise.

RESOLUTION TIME RULES:
- Immediate
- Within 1 hour
- Within 24 hours
- Within 3 business days

ESCALATION TEAM OPTIONS:
- Help Desk Team
- Network Team
- System Administration Team
- Security Operations Center (SOC)
- Incident Response Team
- Cloud/Infrastructure Team
- Database Team
- Application Support Team

Format:

TITLE:
<short title>

CATEGORY:
<one category>

PROBLEM:
- point 1
- point 2

COMMON CAUSES:
- cause 1
- cause 2
- cause 3

TROUBLESHOOTING STEPS:
1. step one
2. step two
3. step three
4. step four
5. step five

RESOLUTION TIME:
- estimated time

ESCALATION CONDITION:
- condition 1
- condition 2

ESCALATE TO:
- team name

PRIORITY:
- Low/Medium/High/Critical

Document:
{text}
"""
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    base_name = os.path.splitext(file)[0]
    output_path = f"processed_docs/{base_name}_summary.txt"

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(response.text)

    print(f"✅ Saved: {output_path}")

except Exception as e:
    print(f"❌ Error processing {file}")
    print(e)