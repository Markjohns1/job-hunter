"""
Database models for JobHunterPro
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