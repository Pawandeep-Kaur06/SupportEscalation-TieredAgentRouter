import pandas as pd

# Load original dataset
df = pd.read_csv("customer_support_tickets.csv")

# -----------------------------
# Keep only IT-related queues
# -----------------------------
IT_QUEUES = [
    "Technical Support",
    "IT Support",
    "Product Support",
    "Service Outages and Maintenance"
]

df = df[df["queue"].isin(IT_QUEUES)]

# -----------------------------
# English only
# -----------------------------
df = df[df["language"] == "en"]

# -----------------------------
# Remove incomplete rows
# -----------------------------
df = df.dropna(
    subset=["subject", "body", "answer"]
)

# -----------------------------
# IT keywords
# -----------------------------
GOOD_KEYWORDS = [

    # Authentication
    "password",
    "login",
    "authentication",
    "mfa",
    "account",
    "credential",

    # Network
    "vpn",
    "network",
    "wifi",
    "dns",
    "firewall",
    "proxy",

    # Email
    "email",
    "outlook",
    "mail",

    # Software
    "software",
    "application",
    "install",
    "installation",
    "update",
    "crash",
    "bug",
    "error",

    # Systems
    "server",
    "database",
    "windows",
    "linux",

    # Cloud
    "azure",
    "aws",
    "docker",
    "kubernetes",

    # Hardware
    "printer",
    "laptop",
    "keyboard",
    "monitor",

    # Security
    "phishing",
    "malware",
    "security",

    # General
    "support",
    "access",
    "permission"
]

# -----------------------------
# Non-IT keywords
# -----------------------------
BAD_KEYWORDS = [

    "marketing",
    "campaign",
    "seo",
    "customer satisfaction",
    "patient",
    "hospital",
    "medical",
    "doctor",
    "pharmacy",
    "investment",
    "trading",
    "stock",
    "portfolio",
    "bank",
    "loan",
    "insurance",
    "retail",
    "sales",
    "return",
    "refund",
    "shipping",
    "delivery",
    "crm",
    "advertisement"
]

# -----------------------------
# Combine subject + body
# -----------------------------
df["combined"] = (
    df["subject"].fillna("") +
    " " +
    df["body"].fillna("")
).str.lower()

# Keep rows with GOOD keywords
good_pattern = "|".join(GOOD_KEYWORDS)

filtered = df[
    df["combined"].str.contains(
        good_pattern,
        case=False,
        regex=True
    )
]

# Remove BAD keywords
bad_pattern = "|".join(BAD_KEYWORDS)

filtered = filtered[
    ~filtered["combined"].str.contains(
        bad_pattern,
        case=False,
        regex=True
    )
]

# Remove helper column
filtered = filtered.drop(columns=["combined"])

print("Final Dataset Size:", filtered.shape)

print("\nQueue Distribution:\n")
print(filtered["queue"].value_counts())

filtered.to_csv(
    "it_support_dataset.csv",
    index=False
)

print("\nSaved it_support_dataset.csv")