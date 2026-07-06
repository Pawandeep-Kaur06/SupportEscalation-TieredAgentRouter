import pandas as pd

# Load dataset
df = pd.read_csv("customer_support_tickets.csv")

# Dataset overview
print("Columns:")
print(df.columns)

print("\nQueue distribution:")
print(df["queue"].value_counts())

print("\nLanguage distribution:")
print(df["language"].value_counts())

# IT-related queues
IT_QUEUES = [
    "Technical Support",
    "IT Support",
    "Product Support",
    "Service Outages and Maintenance"
]

# Filter IT tickets
it_df = df[df["queue"].isin(IT_QUEUES)]

print("\nAfter queue filtering:")
print(it_df.shape)

# Remove rows with missing data
it_df = it_df.dropna(
    subset=["subject", "body", "answer"]
)

# Keep only English tickets
it_df = it_df[
    it_df["language"] == "en"
]

print("\nAfter cleaning:")
print(it_df.shape)

# Priority distribution
print("\nPriority distribution:")
print(it_df["priority"].value_counts())

# Randomly select 500 tickets
it_df = it_df.sample(
    n=500,
    random_state=42
)

print("\nFinal dataset size:")
print(it_df.shape)

# Save filtered dataset
it_df.to_csv(
    "it_support_dataset.csv",
    index=False
)

print("\nSaved as: it_support_dataset.csv")