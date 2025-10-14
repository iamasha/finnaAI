import os
from dotenv import load_dotenv
load_dotenv()



# Email configuration

GMAIL_CONFIG = {
    'server': os.getenv('EMAIL_SERVER'),
    'port': int(os.getenv('EMAIL_PORT', 587)),
    'username': os.getenv('EMAIL_USERNAME'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'sender_email': os.getenv('SENDER_EMAIL')
}

# Email templates
EMAIL_TEMPLATES = {
    'savings_goal': {
        'subject': 'Savings Goal Achieved!',
        'template': """
Dear Customer,

Your savings account has reached your target goal for this month. 
Great job maintaining your financial discipline!

Current Savings: ${amount}
Monthly Target: ${target}

Keep up the good work towards your financial goals.

Sincerely,
Your Financial Insights Team
"""
    }
}