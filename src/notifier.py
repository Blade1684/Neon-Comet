
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class Notifier:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        
        if self.email_user: self.email_user = self.email_user.strip()
        if self.email_pass: self.email_pass = self.email_pass.strip()
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587

    def send_notification(self, product_url, price, threshold, to_email, sender_email=None, sender_pass=None):
        # Use passed credentials if available, else fall back to env
        user = sender_email or self.email_user
        password = sender_pass or self.email_pass

        if not user or not password:
            print("Email credentials not set. Skipping email.")
            return {'success': False, 'message': 'Sender email/password missing'}

        print(f"Attempting login with User: '{user}'")
        print(f"Password length: {len(password)}")
        # Remove spaces from app password just in case user added them
        password = password.replace(" ", "")
        print(f"Password length after cleanup: {len(password)}")

        subject = f"Price Drop Alert! Now {price}"
        body = f"Good news! The price for your tracked product has dropped below {threshold}.\n\nCurrent Price: {price}\nLink: {product_url}"

        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())
            server.quit()
            print(f"Email sent to {to_email}")
            return {'success': True, 'message': 'Email sent successfully'}
        except Exception as e:
            print(f"Failed to send email: {e}")
            return {'success': False, 'message': str(e)}
