import pandas as pd
import random
from datetime import datetime, timedelta

number_of_rows = 1000
data = []

for i in range(1, number_of_rows + 1):
    # Savings and loans
    savings = random.randint(10000, 2000000)
    loans = random.randint(0, 1000000)
    if i % 10 == 0:  # ensure some healthy users
        loans = random.randint(0, int(savings * 0.3))
    amount_paid = random.randint(0, loans) if loans > 0 else 0
    balance = savings - (loans - amount_paid)

    # Random date in last 3 months
    start_date = datetime.now() - timedelta(days=90)
    random_date = start_date + timedelta(days=random.randint(0, 90))

    # Consent
    consent = random.choice(["Yes", "No"])

    # Customer info
    name = f"Customer_{i}"
    email = f"{name.lower()}@gmail.com"
    phone_number = f"+2567{random.randint(10000000, 99999999)}"

    data.append({
        "CustomerID": i,
        "Name": name,
        "Email": email,
        "PhoneNumber": phone_number,
        "Savings": savings,
        "Loans": loans,
        "AmountPaid": amount_paid,
        "Balance": balance,
        "Date": random_date.strftime("%Y-%m-%d"),
        "Consent": consent
    })

# Create DataFrame
df = pd.DataFrame(data)

# Save in the same folder as the script
try:
    df.to_csv("dummy_customer_data.csv", index=False)
    print(" Dummy CSV generated successfully in the current folder!")
except Exception as e:
    print(f" Failed to generate CSV: {e}")
