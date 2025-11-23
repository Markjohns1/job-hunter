"""
Job board scrapers for Job Hunter - FRESH JOBS ONLY
Focus: Quality over quantity - Fresh, legitimate, applicable jobs
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import hashlib
from app.models import Job, Stats, db
from config import Config

class JobScraper:
    """Base scraper class with filters"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.keywords = Config.KEYWORDS
        self.max_job_age_days = 14  # Only jobs from last 2 weeks
    
    def is_job_fresh(self, posted_date_str):
        """Check if job was posted recently"""
        if not posted_date_str:
            return True  # If no date, assume fresh
        
        try:
            # Parse common date formats
            posted_date_str = posted_date_str.lower().strip()
            
            # Handle relative dates
            if 'today' in posted_date_str or 'hours ago' in posted_date_str:
                return True
            
            if 'yesterday' in posted_date_str or '1 day ago' in posted_date_str:
                return True
            
            # Extract number of days
            days_match = re.search(r'(\d+)\s*days?\s*ago', posted_date_str)
            if days_match:
                days = int(days_match.group(1))
                return days <= self.max_job_age_days
            
            # Extract weeks
            weeks_match = re.search(r'(\d+)\s*weeks?\s*ago', posted_date_str)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return weeks <= 2
            
            return True  # Default to fresh if can't parse
            
        except Exception as e:
            return True  # Default to fresh on error
    
    def calculate_relevance(self, job_title, job_description='', company=''):
        """Calculate job relevance score (0-100)"""
        score = 0
        title_lower = job_title.lower()
        desc_lower = (job_description or '').lower()
        
        # High priority keywords in title (25 points each, max 75)
        priority_keywords = ['soc', 'security', 'cybersecurity', 'analyst', 'python', 'developer', 'engineer']
        for keyword in priority_keywords:
            if keyword in title_lower:
                score += 25
        
        # Junior/Entry level bonus (20 points)
        junior_keywords = ['junior', 'entry', 'associate', 'intern', 'graduate']
        if any(kw in title_lower for kw in junior_keywords):
            score += 20
        
        # Tech stack match (5 points each, max 25)
        tech_stack = ['python', 'javascript', 'react', 'flask', 'fastapi', 'linux', 'sql']
        for tech in tech_stack:
            if tech in desc_lower or tech in title_lower:
                score += 5
        
        # Negative indicators (heavy penalty)
        negative = ['senior', '5+ years', '7+ years', '10+ years', 'expert', 'lead', 'principal', 'manager', 'director', 'architect']
        for neg in negative:
            if neg in title_lower or neg in desc_lower:
                score -= 30
        
        return min(max(score, 0), 100)
    
    def is_relevant(self, job_title):
        """Check if job title matches keywords"""
        title_lower = job_title.lower()
        
        # Exclude non-tech jobs immediately
        exclude_keywords = ['sales', 'marketing', 'accounting', 'finance', 'hr', 'admin', 'receptionist', 'driver']
        if any(exc in title_lower for exc in exclude_keywords):
            return False
        
        # Check for tech job indicators
        tech_indicators = [
            'developer', 'engineer', 'analyst', 'security', 'software', 
            'programmer', 'soc', 'cybersecurity', 'devops', 'infosec',
            'python', 'javascript', 'react', 'full stack', 'backend', 'frontend'
        ]
        return any(indicator in title_lower for indicator in tech_indicators)
    
    def generate_job_id(self, title, company, url):
        """Generate unique job ID from URL hash"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title)[:30]
        clean_company = re.sub(r'[^a-zA-Z0-9]', '', company)[:20]
        return f"{clean_company}_{clean_title}_{url_hash}"


class BrighterMondayScraper(JobScraper):
    """Scraper for BrighterMonday Kenya - IMPROVED"""
    
    def scrape(self):
        """Scrape fresh jobs from BrighterMonday"""
        jobs = []
        print("\nScraping BrighterMonday Kenya (FRESH JOBS ONLY)...")
        
        try:
            # Target specific fresh job URLs
            urls = [
                "https://www.brightermonday.co.ke/jobs/technology-software?sort=date",
                "https://www.brightermonday.co.ke/jobs/it-computer?sort=date",
            ]
            
            for url in urls:
                try:
                    print(f"  Checking: {url}")
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Multiple selector strategies
                    job_cards = (
                        soup.select('article.search-result') or
                        soup.select('div[data-job-id]') or
                        soup.select('.job-card') or
                        soup.select('.search__results__item')
                    )
                    
                    print(f"  Found {len(job_cards)} job cards")
                    
                    for card in job_cards[:20]:
                        try:
                            # Extract title
                            title_elem = (
                                card.select_one('h2 a') or
                                card.select_one('.job-title a') or
                                card.select_one('a[href*="/job/"]')
                            )
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            job_url = title_elem.get('href', '')
                            
                            if not job_url.startswith('http'):
                                job_url = 'https://www.brightermonday.co.ke' + job_url
                            
                            # Extract company
                            company_elem = (
                                card.select_one('.company-name') or
                                card.select_one('[class*="company"]') or
                                card.select_one('p.company')
                            )
                            company = company_elem.get_text(strip=True) if company_elem else 'Kenya Tech Company'
                            
                            # Extract date
                            date_elem = (
                                card.select_one('.date') or
                                card.select_one('[class*="date"]') or
                                card.select_one('time')
                            )
                            date_str = date_elem.get_text(strip=True) if date_elem else ''
                            
                            # Check if job is fresh
                            if not self.is_job_fresh(date_str):
                                print(f" Skipping old job: {title} ({date_str})")
                                continue
                            
                            # Check relevance
                            if not self.is_relevant(title):
                                continue
                            
                            # Extract description
                            desc_elem = card.select_one('.description') or card.select_one('p')
                            description = desc_elem.get_text(strip=True)[:500] if desc_elem else ''
                            
                            # Create job
                            job_id = self.generate_job_id(title, company, job_url)
                            
                            # Check if exists
                            if Job.query.filter_by(job_id=job_id).first():
                                continue
                            
                            job_data = {
                                'job_id': job_id,
                                'title': title,
                                'company': company,
                                'url': job_url,
                                'description': description,
                                'source': 'BrighterMonday',
                                'location': 'Kenya',
                                'relevance_score': self.calculate_relevance(title, description, company),
                                'status': 'Found',
                                'posted_date': datetime.utcnow()
                            }
                            
                            jobs.append(job_data)
                            print(f"  {title} at {company} (Posted: {date_str})")
                            
                        except Exception as e:
                            continue
                    
                    if jobs:
                        break  # Got jobs, stop
                    
                    time.sleep(2)
                
                except Exception as e:
                    print(f"   URL error: {e}")
                    continue
            
            print(f"BrighterMonday: {len(jobs)} fresh jobs")
            return jobs
        
        except Exception as e:
            print(f"BrighterMonday error: {e}")
            return []


class FuzuScraper(JobScraper):
    """Scraper for Fuzu Kenya - Works well!"""
    
    def scrape(self):
        """Scrape jobs from Fuzu"""
        jobs = []
        print("\nScraping Fuzu Kenya...")
        
        try:
            url = "https://www.fuzu.com/kenya/jobs?q=developer"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.select('.job-item') or soup.select('[data-job]')
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.select_one('h3 a') or card.select_one('.job-title a')
                    company_elem = card.select_one('.company-name')
                    date_elem = card.select_one('.posted-date') or card.select_one('time')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    job_url = title_elem.get('href', '')
                    
                    if not job_url.startswith('http'):
                        job_url = 'https://www.fuzu.com' + job_url
                    
                    company = company_elem.get_text(strip=True) if company_elem else 'Kenya Company'
                    date_str = date_elem.get_text(strip=True) if date_elem else ''
                    
                    # Check freshness
                    if not self.is_job_fresh(date_str):
                        continue
                    
                    # Check relevance
                    if not self.is_relevant(title):
                        continue
                    
                    job_id = self.generate_job_id(title, company, job_url)
                    
                    if Job.query.filter_by(job_id=job_id).first():
                        continue
                    
                    job_data = {
                        'job_id': job_id,
                        'title': title,
                        'company': company,
                        'url': job_url,
                        'source': 'Fuzu',
                        'location': 'Kenya',
                        'relevance_score': self.calculate_relevance(title, '', company),
                        'status': 'Found'
                    }
                    
                    jobs.append(job_data)
                    print(f"  {title} at {company}")
                
                except Exception as e:
                    continue
            
            print(f"Fuzu: {len(jobs)} fresh jobs")
            return jobs
        
        except Exception as e:
            print(f"Fuzu error: {e}")
            return []


class IndeedKenyaScraper(JobScraper):
    """Scraper for Indeed Kenya"""
    
    def scrape(self):
        """Scrape jobs from Indeed Kenya"""
        jobs = []
        print("\nScraping Indeed Kenya...")
        
        try:
            queries = ['developer', 'cybersecurity', 'software+engineer']
            
            for query in queries:
                url = f"https://ke.indeed.com/jobs?q={query}&l=Kenya&sort=date"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = soup.select('.job_seen_beacon') or soup.select('[data-jk]')
                    
                    for card in job_cards[:10]:
                        try:
                            title_elem = card.select_one('h2 a') or card.select_one('.jobTitle')
                            company_elem = card.select_one('.companyName')
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            
                            # Get job URL
                            job_id_attr = card.get('data-jk', '')
                            if job_id_attr:
                                job_url = f"https://ke.indeed.com/viewjob?jk={job_id_attr}"
                            else:
                                job_url = title_elem.get('href', '')
                                if not job_url.startswith('http'):
                                    job_url = 'https://ke.indeed.com' + job_url
                            
                            company = company_elem.get_text(strip=True) if company_elem else 'Kenya Employer'
                            
                            # Check relevance
                            if not self.is_relevant(title):
                                continue
                            
                            job_id = self.generate_job_id(title, company, job_url)
                            
                            if Job.query.filter_by(job_id=job_id).first():
                                continue
                            
                            job_data = {
                                'job_id': job_id,
                                'title': title,
                                'company': company,
                                'url': job_url,
                                'source': 'Indeed Kenya',
                                'location': 'Kenya',
                                'relevance_score': self.calculate_relevance(title, '', company),
                                'status': 'Found'
                            }
                            
                            jobs.append(job_data)
                            print(f"  {title} at {company}")
                        
                        except Exception as e:
                            continue
                    
                    time.sleep(3)
                
                except Exception as e:
                    continue
            
            print(f"Indeed: {len(jobs)} fresh jobs")
            return jobs
        
        except Exception as e:
            print(f"Indeed error: {e}")
            return []


class RemoteJobScraper(JobScraper):
    """Scraper for remote job boards - FRESH ONLY"""
    
    def scrape(self):
        """Scrape remote jobs"""
        jobs = []
        print("\nScraping Remote Job Boards...")
        
        # WeWorkRemotely - Usually fresh
        try:
            url = "https://weworkremotely.com/remote-jobs/search?utf8=%E2%9C%93&term=developer"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_listings = soup.select('li.feature')
            
            for listing in job_listings[:8]:
                try:
                    title_elem = listing.select_one('.title')
                    company_elem = listing.select_one('.company')
                    url_elem = listing.select_one('a')
                    
                    if title_elem and url_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else 'Remote Company'
                        job_url = 'https://weworkremotely.com' + url_elem.get('href', '')
                        
                        if self.is_relevant(title):
                            job_id = self.generate_job_id(title, company, job_url)
                            
                            if not Job.query.filter_by(job_id=job_id).first():
                                job_data = {
                                    'job_id': job_id,
                                    'title': title,
                                    'company': company,
                                    'url': job_url,
                                    'source': 'WeWorkRemotely',
                                    'location': 'Remote',
                                    'job_type': 'Remote',
                                    'relevance_score': self.calculate_relevance(title, '', company),
                                    'status': 'Found'
                                }
                                jobs.append(job_data)
                                print(f"  Remote: {title}")
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"   WeWorkRemotely error: {e}")
        
        print(f"Remote Jobs: {len(jobs)} fresh jobs")
        return jobs


def run_all_scrapers():
    """Run all scrapers - QUALITY OVER QUANTITY"""
    print("\n" + "="*60)
    print("STARTING FRESH JOB SCRAPING")
    print("Strategy: 5 FRESH JOBS > 100 OLD JOBS")
    print("="*60)
    
    all_jobs = []
    
    # Run scrapers in priority order
    scrapers = [
        BrighterMondayScraper(),
        FuzuScraper(),
        IndeedKenyaScraper(),
        RemoteJobScraper(),
    ]
    
    for scraper in scrapers:
        try:
            jobs = scraper.scrape()
            all_jobs.extend(jobs)
            
            # Stop if we have enough quality jobs
            if len(all_jobs) >= 20:
                print(f"\nGot {len(all_jobs)} quality jobs - stopping")
                break
            
            time.sleep(3)
        
        except Exception as e:
            print(f"Scraper error: {e}")
    
    # Filter out low relevance jobs
    quality_jobs = [job for job in all_jobs if job['relevance_score'] >= 15]
    
    print(f"\nQuality Check:")
    print(f"  Total found: {len(all_jobs)}")
    print(f"  High quality (15%+): {len(quality_jobs)}")
    
    # Save to database
    saved_count = 0
    skipped_count = 0
    
    for job_data in quality_jobs:
        try:
            existing = Job.query.filter_by(job_id=job_data['job_id']).first()
            
            if existing:
                skipped_count += 1
                continue
            
            job = Job(**job_data)
            db.session.add(job)
            db.session.flush()
            saved_count += 1
            
        except Exception as e:
            db.session.rollback()
            continue
    
    try:
        db.session.commit()
        print(f"\n" + "="*60)
        print(f"SCRAPING COMPLETE")
        print(f"   New jobs saved: {saved_count}")
        print(f"   Duplicates skipped: {skipped_count}")
        print(f"   FRESH, QUALITY jobs ready to apply!")
        print("="*60)
        
        # Update stats
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today)
            db.session.add(stats)
        stats.jobs_found += saved_count
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
    
    return saved_count