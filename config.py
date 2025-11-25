"""
Configuration settings for Job Hunter
"""
import os
from datetime import timedelta

class Config:
    # Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///jobhunter.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Job Search Config - Extended with new job types
    KEYWORDS = [
        # Tech/Cybersecurity roles
        'SOC Analyst', 'Security Analyst', 'Cybersecurity', 
        'Junior Developer', 'DevSecOps', 'InfoSec',
        'Security Engineer', 'Threat Analyst', 'Python Developer',
        'Full Stack Developer', 'Backend Developer',
        # NEW: Data & Network roles
        'Data Analyst', 'Data Engineer', 'Database Administrator',
        'Network Administrator', 'Network Engineer',
        'IT Technician', 'IT Support Specialist', 'IT Support Engineer',
        'Systems Administrator', 'Infrastructure Engineer',
        # General IT
        'IT Specialist', 'Computer Technician', 'Technical Support',
        'Help Desk', 'System Administrator'
    ]
    
    # East Africa locations (Kenya + surrounding)
    LOCATIONS = [
        'Kenya', 'Nairobi', 'Mombasa', 'Kisumu',
        'Uganda', 'Kampala',
        'Tanzania', 'Dar es Salaam',
        'Rwanda', 'Kigali',
        'Remote', 'East Africa', 'Africa'
    ]
    
    # Scraping Config
    SCRAPE_INTERVAL = 21600  # 6 hours in seconds
    MAX_APPLICATIONS_PER_DAY = 15
    
    # LinkedIn Config (Optional)
    LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL')
    LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD')
    
    # OpenAI Config (Optional - for AI cover letters)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Brevo Email Config
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
    
    # Email Config (for sending applications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Telegram Config (for notifications)
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
    
    # File Upload Config
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    
    # Your Profile (for cover letters)
    CANDIDATE_PROFILE = {
        'name': 'John Orioki Oguta',
        'email': 'johnmarkoguta@gmail.com',
        'phone': '+254799366734',
        'github': 'https://github.com/Markjohns1',
        'linkedin': 'https://linkedin.com/in/your-profile',
        'skills': [
            'Python (Flask, FastAPI)', 'JavaScript (React)', 'PHP',
            'Cybersecurity', 'SOC Operations', 'Network Security',
            'Linux Administration', 'CCNA2 Certified',
            'Threat Detection', 'Incident Response',
            'Data Analysis', 'Network Administration',
            'IT Support', 'System Administration'
        ],
        'education': 'BSc Computer Science - ZETECH University (Expected Nov 2026)',
        'certifications': ['CCNA2', 'Hack The Box', 'TryHackMe'],
        'key_project': 'MailSentra - Spam & Phishing Email Detector using ML'
    }