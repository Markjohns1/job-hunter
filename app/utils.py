"""
Utility functions for Job Hunter
"""

import os
import requests
from datetime import datetime, date
from config import Config

def generate_cover_letter(job_title, company_name, job_description=''):
    """Generate customized cover letter"""
    
    # Try OpenAI first if API key available
    if Config.OPENAI_API_KEY:
        try:
            return generate_ai_cover_letter(job_title, company_name, job_description)
        except Exception as e:
            print(f"AI generation failed: {e}, using template")
    
    # Fallback to template
    return generate_template_cover_letter(job_title, company_name)


def generate_ai_cover_letter(job_title, company_name, job_description):
    """Generate cover letter using OpenAI"""
    
    profile = Config.CANDIDATE_PROFILE
    
    prompt = f"""Write a professional cover letter for this job application:

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description[:500]}

Candidate Information:
- Name: {profile['name']}
- Education: {profile['education']}
- Key Skills: {', '.join(profile['skills'][:5])}
- Certifications: {', '.join(profile['certifications'])}
- Notable Project: {profile['key_project']}

Requirements:
1. Keep it under 300 words
2. Show genuine enthusiasm for THIS specific role
3. Highlight 2-3 most relevant skills
4. Mention the key project if relevant
5. Professional but warm tone
6. Strong call to action
7. No generic phrases

Format: Professional business letter without address headers."""

    headers = {
        'Authorization': f'Bearer {Config.OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.7
    }
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"OpenAI API error: {response.status_code}")


def generate_template_cover_letter(job_title, company_name):
    """Generate template-based cover letter"""
    
    profile = Config.CANDIDATE_PROFILE
    
    return f"""Dear Hiring Team at {company_name},

I am writing to express my strong interest in the {job_title} position at {company_name}. As a Computer Science student with hands-on experience in cybersecurity operations and full-stack development, I am excited about the opportunity to contribute to your team.

My technical foundation includes {', '.join(profile['skills'][:4])}, with {', '.join(profile['certifications'])} certifications. I recently developed {profile['key_project']}, which demonstrates my ability to build security-focused applications and my understanding of threat detection principles.

Through 500+ hours of practical labs and real-world project development, I have gained strong skills in threat analysis, incident response, and secure application design. I am particularly drawn to {company_name} because of your commitment to innovation in the cybersecurity space.

I am eager to bring my technical skills, security-first mindset, and enthusiasm to {company_name}. I am available to start immediately and would welcome the opportunity to discuss how I can contribute to your team's success.

Please feel free to contact me at {profile['email']} to schedule a discussion. I have attached my CV and portfolio for your review.

Thank you for considering my application.

Best regards,
{profile['name']}
{profile['email']}
{profile['github']}"""


def send_telegram_notification(message):
    """Send notification via Telegram"""
    
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False


def export_to_excel(jobs, filename='job_applications.xlsx'):
    """Export jobs to Excel file"""
    import pandas as pd
    from datetime import datetime
    
    try:
        data = []
        for job in jobs:
            data.append({
                'Title': job.title,
                'Company': job.company,
                'Location': job.location or 'N/A',
                'Status': job.status,
                'Source': job.source,
                'Relevance Score': job.relevance_score,
                'URL': job.url,
                'Found Date': job.found_date.strftime('%Y-%m-%d') if job.found_date else '',
                'Applied Date': job.applied_date.strftime('%Y-%m-%d') if job.applied_date else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create exports directory in app folder
        exports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'job_applications_{timestamp}.xlsx'
        filepath = os.path.join(exports_dir, filename)
        
        # Export to Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f"✅ Exported {len(jobs)} jobs to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Export error: {e}")
        raise


def get_daily_stats():
    """Get statistics for dashboard"""
    from app.models import Job, Application, Stats
    
    today = date.today()
    
    stats = {
        'total_jobs_found': Job.query.count(),
        'jobs_applied': Job.query.filter_by(status='Applied').count(),
        'pending_applications': Job.query.filter_by(status='Found').count(),
        'interviews_scheduled': Job.query.filter_by(status='Interview').count(),
        'offers_received': Job.query.filter_by(status='Offer').count(),
        'rejections': Job.query.filter_by(status='Rejected').count(),
        'high_relevance': Job.query.filter(Job.relevance_score >= 70).count(),
        'applications_today': Application.query.filter(
            Application.applied_date >= datetime.combine(today, datetime.min.time())
        ).count()
    }
    
    # Calculate response rate
    total_applied = stats['jobs_applied']
    total_responses = stats['interviews_scheduled'] + stats['rejections'] + stats['offers_received']
    stats['response_rate'] = round((total_responses / total_applied * 100) if total_applied > 0 else 0, 1)
    
    return stats


def get_weekly_trends():
    """Get weekly application trends"""
    from app.models import Stats
    from datetime import timedelta
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    stats = Stats.query.filter(Stats.date >= week_ago).order_by(Stats.date).all()
    
    return {
        'dates': [s.date.strftime('%m/%d') for s in stats],
        'jobs_found': [s.jobs_found for s in stats],
        'jobs_applied': [s.jobs_applied for s in stats],
        'interviews': [s.interviews_scheduled for s in stats]
    }