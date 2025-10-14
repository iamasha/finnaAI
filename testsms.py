from __future__ import print_function
import os
from dotenv import load_dotenv
import pandas as pd
from twilio.rest import Client
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from email_sender import send_financial_alert
import africastalking
import random
import json

load_dotenv()

# ------------------ TWILIO CONFIG ------------------
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
WHATSAPP = os.getenv("whatsapp")
twilio_client = Client(ACCOUNT_SID, AUTH_TOKEN)
SMS_USERNAME = os.getenv("SMS_USERNAME")
SMS_API_KEY = os.getenv("SMS_API_KEY")

# ------------------ LOAD & PROCESS DATA ------------------
df = pd.read_csv("dummy_customer_data.csv")

summary = df.groupby(
    ["CustomerID", "Name", "Email", "PhoneNumber", "Date", "Consent"]
).agg({
    "Savings": "mean",
    "Loans": "mean",
    "AmountPaid": "sum",
    "Balance": "mean"
}).reset_index()

print("Data summary head:")
print(summary.head())

# Feature engineering
summary["loan_to_savings_ratio"] = summary["Loans"] / (summary["Savings"] + 1)
summary["payment_efficiency"] = summary["AmountPaid"] / (summary["Loans"] + 1)
summary["balance_health"] = summary["Balance"] / (summary["Savings"] + summary["Loans"] + 1)

# Label financial health
def label_financial_health(row):
    if row["loan_to_savings_ratio"] > 2:
        return "at_risk"
    elif row["payment_efficiency"] > 1 and row["balance_health"] > 0.5:
        return "healthy"
    else:
        return "neutral"

summary["label"] = summary.apply(label_financial_health, axis=1)

# ------------------ MODEL TRAINING ------------------
X = summary[["Savings", "Loans", "AmountPaid", "Balance",
             "loan_to_savings_ratio", "payment_efficiency", "balance_health"]]
y = LabelEncoder().fit_transform(summary["label"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(X_train, y_train)
summary["pred_label"] = model.predict(X)

print(f"\n Model trained successfully. Processed {len(summary)} customers.")

# ------------------ GENERATE INSIGHTS ------------------
def generate_insight(row):
    if row["pred_label"] == 0:
        return "You're spending too much relative to your savings. Try to increase your savings by 10% this month."
    elif row["pred_label"] == 1:
        return "Excellent progress! Your financial habits show good balance and repayment discipline."
    else:
        return "You’re managing okay, but consider reducing your debt ratio for long-term stability."

summary["insight"] = summary.apply(generate_insight, axis=1)

# ------------------ FINANCIAL SCORE ------------------
def calculate_financial_score(row):
    savings_score = min(row["Savings"] / (row["Savings"] + row["Loans"] + 1), 1) * 40
    repayment_score = min(row["payment_efficiency"], 1.5) / 1.5 * 30
    balance_score = min(row["balance_health"], 1) * 30
    total_score = savings_score + repayment_score + balance_score
    return round(total_score, 1)

summary["financial_score"] = summary.apply(calculate_financial_score, axis=1)

# ------------------ EXPORT DASHBOARD DATA ------------------
summary.to_json("dashboard_data.json", orient="records", force_ascii=False)

# print(" Data exported to dashboard_data.json (includes financial_score)")

# ------------------ SEND WHATSAPP + EMAIL ALERTS ------------------
for index, row in summary.iterrows():
    message_body = f"Hello {row['Name']}, {row['insight']}\nYour Financial Score: {row['financial_score']}"

    # --- Send WhatsApp message ---
    try:
        message = twilio_client.messages.create(
            from_=WHATSAPP,  # Twilio sandbox number
            to=f"whatsapp:{row['PhoneNumber']}",
            body=message_body
        )
        print(f" WhatsApp sent to {row['Name']} (SID: {message.sid})")
    except Exception as e:
        print(f" Failed to send WhatsApp to {row['Name']}: {e}")

    # --- Send Email ---
    try:
        email_success = send_financial_alert(
            recipient_email=row["Email"],
            subject="Your Financial Health Update",
            message=message_body + "\n\nThank you for trusting us to guide your financial journey!"
        )
        if email_success:
            print(f" Email sent to {row['Name']} ({row['Email']})")
        else:
            print(f" Failed to send email to {row['Name']}")
    except Exception as e:
        print(f" Email error for {row['Name']}: {e}")

# ------------------ SMS (AFRICASTALKING) ------------------
class SMS:
    def __init__(self):
        africastalking.initialize(self.username, self.api_key)
        africastalking.initialize(SMS_USERNAME, SMS_API_KEY)
        self.sms = africastalking.SMS

    def send(self):
        recipients = ["+256757941028", "+256726372066"]
        message = "Keep up with your savings goals — remember, consistency builds wealth!"
        sender = "shortCode"
        try:
            response = self.sms.send(message, recipients, sender)
            print("SMS sent:", response)
        except Exception as e:
            print("Error sending SMS:", str(e))


if __name__ == "__main__":
    SMS().send()
    print("\n All processes completed successfully.")
