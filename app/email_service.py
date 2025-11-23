"""
Email Service - Send job applications via email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('MAIL_SERVER')
        self.smtp_port = int(os.getenv('MAIL_PORT', 587))
        self.username = os.getenv('MAIL_USERNAME')
        self.password = os.getenv('MAIL_PASSWORD')
        
    def send_application(self, to_email, job_title, company, cover_letter, cv_path=None):
        """Send job application email"""
        
        if not all([self.smtp_server, self.username, self.password]):
            raise Exception("Email configuration missing")
        
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        msg['Subject'] = f"Application for {job_title} - John Orioki Oguta"
        
        body = f"""Dear Hiring Manager at {company},

{cover_letter}

Best regards,
John Orioki Oguta
Email: johnmarkoguta@gmail.com
Phone: +254-799-366-734
GitHub: https://github.com/Markjohns1
LinkedIn: https://www.linkedin.com/in/john-mark-a01129337

---
This application was sent via JobHunterPro"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        if cv_path and os.path.exists(cv_path):
            with open(cv_path, 'rb') as f:
                cv_attachment = MIMEApplication(f.read(), _subtype='pdf')
                cv_attachment.add_header('Content-Disposition', 'attachment', 
                                       filename='John_Orioki_Oguta_CV.pdf')
                msg.attach(cv_attachment)
        
        try:
            # Try port 587 with TLS
            try:
                server = smtplib.SMTP(self.smtp_server, 587, timeout=10)
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                server.quit()
                return True
            except:
                # Fallback to port 465 with SSL
                server = smtplib.SMTP_SSL(self.smtp_server, 465, timeout=10)
                server.login(self.username, self.password)
                server.send_message(msg)
                server.quit()
                return True
            
        except Exception as e:
            print(f"Email send error: {e}")
            raise