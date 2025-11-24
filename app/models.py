"""
Database models for Job Hunter
"""

from datetime import datetime
from app import db

class Job(db.Model):
    """Job listing model"""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(50))  # BrighterMonday, LinkedIn, etc.
    salary = db.Column(db.String(100))
    job_type = db.Column(db.String(50))  # Full-time, Contract, Remote
    
    # Status tracking
    status = db.Column(db.String(50), default='Found')  # Found, Applied, Interview, Rejected, Offer
    relevance_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    posted_date = db.Column(db.DateTime)
    found_date = db.Column(db.DateTime, default=datetime.utcnow)
    applied_date = db.Column(db.DateTime)
    
    # Relationships
    application = db.relationship('Application', backref='job', uselist=False, cascade='all, delete-orphan')
    auto_apply_logs = db.relationship('AutoApplyLog', backref='job', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'source': self.source,
            'status': self.status,
            'relevance_score': self.relevance_score,
            'found_date': self.found_date.strftime('%Y-%m-%d %H:%M') if self.found_date else None,
            'applied_date': self.applied_date.strftime('%Y-%m-%d %H:%M') if self.applied_date else None
        }


class Application(db.Model):
    """Job application tracking"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Application details
    cover_letter = db.Column(db.Text)
    cv_version = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    # Communication tracking
    email_sent = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    last_contact = db.Column(db.DateTime)
    
    # Response tracking
    response_received = db.Column(db.Boolean, default=False)
    response_date = db.Column(db.DateTime)
    response_type = db.Column(db.String(50))  # Interview, Rejection, Request for info
    
    # Timestamps
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Application for Job {self.job_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'applied_date': self.applied_date.strftime('%Y-%m-%d %H:%M'),
            'email_sent': self.email_sent,
            'response_received': self.response_received,
            'response_type': self.response_type
        }


class Stats(db.Model):
    """Daily statistics tracking"""
    __tablename__ = 'stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, default=datetime.utcnow().date)
    
    jobs_found = db.Column(db.Integer, default=0)
    jobs_applied = db.Column(db.Integer, default=0)
    interviews_scheduled = db.Column(db.Integer, default=0)
    rejections_received = db.Column(db.Integer, default=0)
    offers_received = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Stats {self.date}>'
    
    def to_dict(self):
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'jobs_found': self.jobs_found,
            'jobs_applied': self.jobs_applied,
            'interviews': self.interviews_scheduled,
            'rejections': self.rejections_received,
            'offers': self.offers_received
        }


class AutoApplySettings(db.Model):
    """User's auto-apply preferences"""
    __tablename__ = 'auto_apply_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Enable/disable auto-apply
    enabled = db.Column(db.Boolean, default=False)
    
    # Filters (comma-separated)
    job_titles = db.Column(db.Text)  # "Python Developer, Network Admin, Data Analyst"
    locations = db.Column(db.Text)   # "Kenya, Remote, East Africa"
    job_types = db.Column(db.Text)   # "Full-time, Contract, Remote"
    
    # Settings
    max_applications_per_day = db.Column(db.Integer, default=5)
    auto_apply_time = db.Column(db.String(5), default='09:00')  # HH:MM format
    
    # Tracking
    total_auto_applied = db.Column(db.Integer, default=0)
    last_run = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AutoApplySettings enabled={self.enabled}>'
    
    def get_job_titles_list(self):
        """Parse comma-separated job titles"""
        if not self.job_titles:
            return []
        return [title.strip() for title in self.job_titles.split(',')]
    
    def get_locations_list(self):
        """Parse comma-separated locations"""
        if not self.locations:
            return []
        return [loc.strip() for loc in self.locations.split(',')]
    
    def get_job_types_list(self):
        """Parse comma-separated job types"""
        if not self.job_types:
            return []
        return [jtype.strip() for jtype in self.job_types.split(',')]
    
    def to_dict(self):
        return {
            'id': self.id,
            'enabled': self.enabled,
            'job_titles': self.get_job_titles_list(),
            'locations': self.get_locations_list(),
            'job_types': self.get_job_types_list(),
            'max_applications_per_day': self.max_applications_per_day,
            'auto_apply_time': self.auto_apply_time,
            'total_auto_applied': self.total_auto_applied,
            'last_run': self.last_run.strftime('%Y-%m-%d %H:%M') if self.last_run else None
        }


class AutoApplyLog(db.Model):
    """Track each auto-apply action"""
    __tablename__ = 'auto_apply_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    
    # Action taken
    action = db.Column(db.String(50))  # "auto_applied", "manual_apply_needed", "skipped"
    reason = db.Column(db.Text)  # Why skipped or action details
    
    # Email info
    recruiter_email = db.Column(db.String(200))
    email_sent = db.Column(db.Boolean, default=False)
    
    # Telegram notification
    telegram_sent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AutoApplyLog job_id={self.job_id} action={self.action}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'action': self.action,
            'reason': self.reason,
            'recruiter_email': self.recruiter_email,
            'email_sent': self.email_sent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }