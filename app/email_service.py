"""
Email Service - Send job applications via email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from config import Config

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('MAIL_PORT', 587))
        self.username = os.getenv('MAIL_USERNAME')
        self.password = os.getenv('MAIL_PASSWORD')
        self.profile = Config.CANDIDATE_PROFILE
        
    def send_application(self, to_email, job_title, company, cover_letter, cv_path=None):
        """Send job application email with cover letter and CV"""
        
        if not all([self.smtp_server, self.username, self.password]):
            raise Exception("Email configuration missing. Set MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD environment variables.")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{self.profile['name']} <{self.username}>"
        msg['To'] = to_email
        msg['Subject'] = f"Application for {job_title} - {self.profile['name']}"
        
        text_body = self._create_text_body(company, cover_letter)
        html_body = self._create_html_body(company, cover_letter, job_title)
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        if cv_path and os.path.exists(cv_path):
            try:
                with open(cv_path, 'rb') as f:
                    cv_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    cv_filename = f"{self.profile['name'].replace(' ', '_')}_CV.pdf"
                    cv_attachment.add_header('Content-Disposition', 'attachment', 
                                           filename=cv_filename)
                    msg.attach(cv_attachment)
            except Exception as e:
                print(f"Warning: Could not attach CV: {e}")
        
        return self._send_email(msg)
    
    def _create_text_body(self, company, cover_letter):
        """Create plain text email body"""
        contact_info = []
        if self.profile.get('email'):
            contact_info.append(f"Email: {self.profile['email']}")
        if self.profile.get('phone'):
            contact_info.append(f"Phone: {self.profile['phone']}")
        if self.profile.get('github'):
            contact_info.append(f"GitHub: {self.profile['github']}")
        if self.profile.get('linkedin'):
            contact_info.append(f"LinkedIn: {self.profile['linkedin']}")
        
        return f"""Dear Hiring Manager at {company},

{cover_letter}

Best regards,
{self.profile['name']}
{chr(10).join(contact_info)}

---
This application was sent via Job Hunter"""
    
    def _create_html_body(self, company, cover_letter, job_title):
        """Create HTML email body for better formatting"""
        contact_links = []
        if self.profile.get('email'):
            contact_links.append(f'<a href="mailto:{self.profile["email"]}">{self.profile["email"]}</a>')
        if self.profile.get('phone'):
            contact_links.append(self.profile['phone'])
        if self.profile.get('github'):
            contact_links.append(f'<a href="{self.profile["github"]}">GitHub</a>')
        if self.profile.get('linkedin'):
            contact_links.append(f'<a href="{self.profile["linkedin"]}">LinkedIn</a>')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #0066cc; padding-bottom: 10px; margin-bottom: 20px; }}
        .cover-letter {{ white-space: pre-wrap; margin: 20px 0; }}
        .signature {{ margin-top: 30px; }}
        .contact {{ margin-top: 10px; color: #666; }}
        .contact a {{ color: #0066cc; text-decoration: none; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0; color: #0066cc;">Application for {job_title}</h2>
            <p style="margin: 5px 0 0 0; color: #666;">{company}</p>
        </div>
        
        <div class="cover-letter">{cover_letter}</div>
        
        <div class="signature">
            <p><strong>Best regards,</strong></p>
            <p><strong>{self.profile['name']}</strong></p>
            <div class="contact">
                {' | '.join(contact_links)}
            </div>
        </div>
        
        <div class="footer">
            <p>This application was sent via Job Hunter</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _send_email(self, msg):
        """Send email with retry logic"""
        errors = []
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
            server.set_debuglevel(0)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully to {msg['To']}")
            return True
        except smtplib.SMTPAuthenticationError as e:
            errors.append(f"Authentication failed: {e}")
        except smtplib.SMTPException as e:
            errors.append(f"SMTP error on port {self.smtp_port}: {e}")
        except Exception as e:
            errors.append(f"Port {self.smtp_port} failed: {e}")
        
        try:
            server = smtplib.SMTP_SSL(self.smtp_server, 587, timeout=15)
            server.set_debuglevel(0)
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully via SSL to {msg['To']}")
            return True
        except Exception as e:
            errors.append(f"Port 587 SSL failed: {e}")
        
        error_msg = " | ".join(errors)
        print(f"All email sending attempts failed: {error_msg}")
        raise Exception(f"Failed to send email: {error_msg}")
    
    def test_connection(self):
        """Test email server connection"""
        if not all([self.smtp_server, self.username, self.password]):
            return False, "Email configuration missing"
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.username, self.password)
            server.quit()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)