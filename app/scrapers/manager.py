"""
Scraper Manager - Clean automated job scraping from multiple sources
"""
import os
import hashlib
import requests
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
        """Run all scrapers - Adzuna + RemoteOK"""
        print("\n" + "="*60)
        print("AUTOMATED JOB SCRAPING - Multiple Sources")
        print("="*60)
        
        all_jobs = []
        
        if self.adzuna_app_id and self.adzuna_app_key:
            try:
                from app.scrapers.adzuna import AdzunaScraper
                scraper = AdzunaScraper(self.adzuna_app_id, self.adzuna_app_key)
                adzuna_jobs = scraper.scrape()
                all_jobs.extend(adzuna_jobs)
                print(f"✓ Adzuna: {len(adzuna_jobs)} jobs")
            except Exception as e:
                print(f"✗ Adzuna error: {e}")
        else:
            print("✗ Adzuna API not configured")
        
        try:
            remoteok_jobs = self._scrape_remoteok()
            all_jobs.extend(remoteok_jobs)
            print(f"✓ RemoteOK: {len(remoteok_jobs)} jobs")
        except Exception as e:
            print(f"✗ RemoteOK error: {e}")
        
        print(f"\nTotal scraped: {len(all_jobs)} jobs")
        
        saved = self.save_jobs(all_jobs)
        
        print("="*60)
        print(f"Saved: {saved} new jobs to database")
        print("="*60 + "\n")
        
        return saved
    
    def _scrape_remoteok(self, keywords=None):
        """Scrape RemoteOK for remote jobs"""
        jobs = []
        seen = set()
        
        if not keywords:
            keywords = [
                "python", "developer", "engineer", "data",
                "junior", "full stack", "backend", "devops", "security",
                "software", "tech", "programmer", "analyst",
                "flask", "data recording", "it support", "network",
                "administrator", "technician", "cybersecurity", "database",
                "frontend", "api", "cloud", "linux", "windows",
                "helpdesk", "infrastructure", "support", "it"
            ]
        
        try:
            response = requests.get(
                "https://remoteok.com/api",
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                params={'limit': 500}
            )
            
            if response.status_code != 200:
                print(f"RemoteOK HTTP {response.status_code}")
                return jobs
            
            if not response.text:
                print("RemoteOK returned empty response")
                return jobs
            
            all_remoteok_jobs = response.json()
            if not isinstance(all_remoteok_jobs, list):
                print(f"RemoteOK response is not a list: {type(all_remoteok_jobs)}")
                return jobs
            
            print(f"RemoteOK API returned {len(all_remoteok_jobs)} total jobs")
            
            for i, job in enumerate(all_remoteok_jobs[:50]):
                if len(jobs) >= 30:
                    break
                
                title = job.get('title', '').lower()
                company = job.get('company', '').lower()
                
                matches_keyword = any(kw.lower() in title or kw.lower() in company for kw in keywords)
                
                if matches_keyword and title.strip():  # Only if title exists
                    job_key = f"{job.get('title')}|{job.get('company')}".lower()
                    
                    if job_key not in seen:
                        seen.add(job_key)
                        
                        job_data = {
                            'title': job.get('title', 'Unknown').strip(),
                            'company': job.get('company', 'Unknown').strip(),
                            'location': job.get('location', 'Remote'),
                            'url': job.get('url') or job.get('apply_url', ''),
                            'description': job.get('description', '')[:500],
                            'source': 'RemoteOK',
                            'relevance_score': 65,
                            'contract_type': 'Remote',
                            'salary_min': None
                        }
                        
                        jobs.append(job_data)
                        print(f"  RemoteOK: {job.get('title')}")
            
            print(f"RemoteOK: Saved {len(jobs)} jobs")
        
        except requests.Timeout:
            print("RemoteOK timeout")
        except requests.ConnectionError:
            print("RemoteOK connection error")
        except Exception as e:
            print(f"RemoteOK error: {type(e).__name__}: {e}")
        
        return jobs
    
    def save_jobs(self, jobs):
        """Save jobs to database, avoiding duplicates"""
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