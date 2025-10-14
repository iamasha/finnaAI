import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_CONFIG
import ssl


def send_financial_alert(recipient_email, subject, message):
    """Send email alerts to customers"""
    try:
        import ssl
        import certifi

        # Create SSL context using certifi's trusted CA certificates
        context = ssl._create_unverified_context()

        print(f"Connecting to {GMAIL_CONFIG['server']}:{GMAIL_CONFIG['port']}...")

        with smtplib.SMTP(GMAIL_CONFIG['server'], GMAIL_CONFIG['port']) as server:
            server.starttls(context=context)
            server.login(GMAIL_CONFIG['username'], GMAIL_CONFIG['password'])
            
            msg = MIMEMultipart('alternative')
            msg['From'] = GMAIL_CONFIG['sender_email']
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Create HTML content
            html_content = create_html_template(message)
            
            # Attach both versions
            text_part = MIMEText(message, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            server.send_message(msg)
            print(f"Alert sent to {recipient_email}")
            return True
            
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def create_html_template(message):
    """Create HTML email template"""
    return f"""
    <html>
      <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #1a5276;">Financial Insights Alert</h2>
          <div style="background-color: #f8f9f9; padding: 20px; border-radius: 5px;">
            {message.replace('\n', '<br>')}
          </div>
          <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
            This is an automated message from your financial institution.
          </p>
        </div>
      </body>
    </html>
    """