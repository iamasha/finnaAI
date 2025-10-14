
from email_sender import send_financial_alert
from config import EMAIL_TEMPLATES

def send_savings_alert(recipient_email, amount, target):
    """Send savings goal achievement alert"""
    message = EMAIL_TEMPLATES['savings_goal']['template'].format(
        amount=amount, 
        target=target
    )
    
    return send_financial_alert(
        recipient_email=recipient_email,
        subject=EMAIL_TEMPLATES['savings_goal']['subject'],
        message=message
    )

# Usage
if __name__ == "__main__":
    send_savings_alert('hwakaasha@gmail.com', '5,250', '5,000')