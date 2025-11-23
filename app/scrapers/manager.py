"""
Scraper Manager - Clean automated job scraping
"""

import os
import hashlib
from datetime import datetime
from app.models import Job, Stats, db

class ScraperManager:
    def __init__(self):
        self.adzuna_app_id = os.getenv('ADZUNA_APP_ID')
        self.adzuna_app_key = os.getenv('ADZUNA_APP_KEY')
    
    def generate_job_id(self, title, company, url):
        """Generate unique job ID"""
        unique_string = f"{url}_{title}_{company}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def scrape_all(self):
        """Run Adzuna scraper"""
        print("\n" + "="*60)
        print("AUTOMATED JOB SCRAPING")
        print("="*60)
        
        all_jobs = []
        
        # Get fresh jobs from Adzuna
        if self.adzuna_app_id and self.adzuna_app_key:
            try:
                from app.scrapers.adzuna import AdzunaScraper
                scraper = AdzunaScraper(self.adzuna_app_id, self.adzuna_app_key)
                jobs = scraper.scrape()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"Adzuna error: {e}")
        else:
            print("Adzuna API not configured")
        
        print(f"\nTotal: {len(all_jobs)} jobs")
        
        saved = self.save_jobs(all_jobs)
        
        print("\n" + "="*60)
        print(f"SAVED: {saved} new jobs")
        print("="*60)
        
        return saved
    
    def save_jobs(self, jobs):
        """Save jobs to database"""
        saved_count = 0
        
        for job_data in jobs:
            try:
                job_id = self.generate_job_id(
                    job_data.get('title', ''),
                    job_data.get('company', ''),
                    job_data.get('url', '')
                )
                
                if Job.query.filter_by(job_id=job_id).first():
                    continue
                
                job = Job(
                    job_id=job_id,
                    title=job_data.get('title'),
                    company=job_data.get('company'),
                    location=job_data.get('location'),
                    url=job_data.get('url'),
                    description=job_data.get('description'),
                    source=job_data.get('source'),
                    relevance_score=job_data.get('relevance_score', 50),
                    status='Found',
                    salary=job_data.get('salary_min'),
                    job_type=job_data.get('contract_type')
                )
                
                db.session.add(job)
                saved_count += 1
                
            except Exception as e:
                print(f"Save error: {e}")
                continue
        
        try:
            db.session.commit()
            
            # Update stats
            today = datetime.utcnow().date()
            stats = Stats.query.filter_by(date=today).first()
            if not stats:
                stats = Stats(date=today, jobs_found=0)
                db.session.add(stats)
            stats.jobs_found += saved_count
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
        
        return saved_count