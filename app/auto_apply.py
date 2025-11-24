"""
Auto-Apply Scheduler - app/auto_apply.py
Handles daily auto-applying to matching jobs
"""

import os
import re
from datetime import datetime
from app.models import Job, Application, AutoApplySettings, AutoApplyLog, Stats, db
from app.utils import generate_cover_letter, send_telegram_notification
from config import Config


class AutoApplyManager:
    """Manages automatic job applications"""
    
    def __init__(self):
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def run_daily_auto_apply(self):
        """Run auto-apply for the day"""
        settings = AutoApplySettings.query.filter_by(enabled=True).first()
        
        if not settings:
            print("Auto-apply disabled")
            return 0
        
        print("\n" + "="*60)
        print("AUTO-APPLY SCHEDULER RUNNING")
        print("="*60)
        
        # Find matching jobs
        matching_jobs = self._find_matching_jobs(settings)
        print(f"Found {len(matching_jobs)} matching jobs")
        
        if not matching_jobs:
            send_telegram_notification("🔍 Auto-Apply: No matching jobs found today")
            return 0
        
        # Apply to jobs (up to max per day)
        applied_count = 0
        for job in matching_jobs[:settings.max_applications_per_day]:
            result = self._apply_to_job(job, settings)
            if result:
                applied_count += 1
        
        # Update settings
        settings.last_run = datetime.utcnow()
        db.session.commit()
        
        print(f"Auto-applied to {applied_count} jobs")
        print("="*60)
        
        return applied_count
    
    def _find_matching_jobs(self, settings):
        """Find jobs matching user's criteria"""
        job_titles = settings.get_job_titles_list()
        locations = settings.get_locations_list()
        job_types = settings.get_job_types_list()
        
        # Query jobs that haven't been applied to yet
        query = Job.query.filter_by(status='Found')
        
        # Filter by title (case-insensitive)
        if job_titles:
            title_filters = [Job.title.ilike(f'%{title}%') for title in job_titles]
            query = query.filter(db.or_(*title_filters))
        
        # Filter by location (case-insensitive)
        if locations:
            location_filters = [Job.location.ilike(f'%{loc}%') for loc in locations]
            query = query.filter(db.or_(*location_filters))
        
        # Filter by job type (case-insensitive)
        if job_types:
            type_filters = [Job.job_type.ilike(f'%{jtype}%') for jtype in job_types]
            query = query.filter(db.or_(*type_filters))
        
        # Sort by relevance
        matching_jobs = query.order_by(Job.relevance_score.desc()).all()
        
        return matching_jobs
    
    def _apply_to_job(self, job, settings):
        """Apply to a single job"""
        try:
            # Check if already applied
            if job.application:
                log = AutoApplyLog(
                    job_id=job.id,
                    action='skipped',
                    reason='Already applied to this job'
                )
                db.session.add(log)
                db.session.commit()
                return False
            
            # Generate cover letter
            cover_letter = generate_cover_letter(
                job.title,
                job.company,
                job.description or ''
            )
            
            # Try to extract email from description
            recruiter_email = self._extract_email(job.description or '')
            
            if recruiter_email:
                # AUTO-APPLY: Send email
                success = self._send_application_email(
                    job=job,
                    recruiter_email=recruiter_email,
                    cover_letter=cover_letter
                )
                
                if success:
                    # Create application record
                    application = Application(
                        job_id=job.id,
                        cover_letter=cover_letter,
                        applied_date=datetime.utcnow(),
                        email_sent=True
                    )
                    job.status = 'Applied'
                    job.applied_date = datetime.utcnow()
                    
                    db.session.add(application)
                    
                    # Log action
                    log = AutoApplyLog(
                        job_id=job.id,
                        action='auto_applied',
                        reason='Email found and sent automatically',
                        recruiter_email=recruiter_email,
                        email_sent=True,
                        telegram_sent=False
                    )
                    db.session.add(log)
                    
                    # Send Telegram notification
                    self._send_telegram_success(job, recruiter_email, cover_letter)
                    log.telegram_sent = True
                    
                    db.session.commit()
                    settings.total_auto_applied += 1
                    
                    print(f"✅ Auto-applied: {job.title} at {job.company}")
                    return True
            else:
                # MANUAL: Need email from user
                application = Application(
                    job_id=job.id,
                    cover_letter=cover_letter,
                    applied_date=datetime.utcnow(),
                    email_sent=False
                )
                job.status = 'Found'  # Keep as Found until user confirms
                
                db.session.add(application)
                
                log = AutoApplyLog(
                    job_id=job.id,
                    action='manual_apply_needed',
                    reason='No recruiter email found - manual action needed',
                    email_sent=False,
                    telegram_sent=False
                )
                db.session.add(log)
                
                # Send Telegram guide
                self._send_telegram_manual_guide(job, cover_letter)
                log.telegram_sent = True
                
                db.session.commit()
                settings.total_auto_applied += 1
                
                print(f"⚠️ Manual needed: {job.title} at {job.company}")
                return True
        
        except Exception as e:
            print(f"Error applying to {job.title}: {e}")
            log = AutoApplyLog(
                job_id=job.id,
                action='error',
                reason=str(e)
            )
            db.session.add(log)
            db.session.commit()
            return False
    
    def _extract_email(self, description):
        """Extract email from job description"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, description)
        return matches[0] if matches else None
    
    def _send_application_email(self, job, recruiter_email, cover_letter):
        """Send application via Brevo"""
        try:
            from app.email_service import EmailService
            email_service = EmailService()
            
            cv_path = os.path.join('uploads', 'cv.pdf')
            
            email_service.send_application(
                to_email=recruiter_email,
                job_title=job.title,
                company=job.company,
                cover_letter=cover_letter,
                cv_path=cv_path if os.path.exists(cv_path) else None
            )
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
    
    def _send_telegram_success(self, job, recruiter_email, cover_letter):
        """Send success notification to Telegram"""
        message = f"""Application Sent Successfully

Job: {job.title}
Company: {job.company}
Location: {job.location}
Type: {job.job_type}

Sent to: {recruiter_email}

View on Dashboard: http://localhost:5000

Keep applying!"""
        
        send_telegram_notification(message)
    
    def _send_telegram_manual_guide(self, job, cover_letter):
        """Send manual application guide to Telegram"""
        message = f"""Manual Action Needed

Job: {job.title}
Company: {job.company}
Location: {job.location}

No recruiter email found in job posting

Quick Steps:
1. Click job link below
2. Go to company's Contact Us page
3. Find recruiter/hiring manager email
4. Copy the email address
5. Go to dashboard
6. Find this job and paste email
7. Click Send Application

Takes about 2 minutes

Job Link: {job.url}

Your cover letter is ready!
Dashboard: http://localhost:5000"""
        
        send_telegram_notification(message)