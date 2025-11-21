"""
Job board scrapers for JobHunterPro - UPDATED & WORKING
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import hashlib
from app.models import Job, Stats, db
from config import Config

class JobScraper:
    """Base scraper class"""
    
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
        self.locations = Config.LOCATIONS
    
    def calculate_relevance(self, job_title, job_description='', company=''):
        """Calculate job relevance score (0-100)"""
        score = 0
        title_lower = job_title.lower()
        desc_lower = (job_description or '').lower()
        company_lower = (company or '').lower()
        
        # High priority keywords in title (20 points each)
        priority_keywords = ['soc', 'security', 'cybersecurity', 'analyst', 'infosec', 'python', 'developer']
        for keyword in priority_keywords:
            if keyword in title_lower:
                score += 20
        
        # Medium priority in title (15 points)
        medium_keywords = ['junior', 'entry', 'associate', 'engineer', 'specialist']
        for keyword in medium_keywords:
            if keyword in title_lower:
                score += 15
        
        # Keywords in description (5 points each, max 30)
        desc_score = 0
        for keyword in self.keywords:
            if keyword.lower() in desc_lower:
                desc_score += 5
        score += min(desc_score, 30)
        
        # Positive location indicators (10 points)
        location_keywords = ['kenya', 'remote', 'nairobi', 'work from home']
        for loc in location_keywords:
            if loc in desc_lower or loc in title_lower:
                score += 10
                break
        
        # Negative keywords (reduce score)
        negative_keywords = ['senior', '5+ years', '7+ years', '10+ years', 'expert', 'lead', 'principal', 'manager', 'director']
        for keyword in negative_keywords:
            if keyword in title_lower or keyword in desc_lower:
                score -= 20
        
        return min(max(score, 0), 100)
    
    def is_relevant(self, job_title):
        """Check if job title matches keywords"""
        title_lower = job_title.lower()
        
        # Check for exact keyword matches
        for keyword in self.keywords:
            if keyword.lower() in title_lower:
                return True
        
        # Check for tech job indicators
        tech_indicators = ['developer', 'engineer', 'analyst', 'security', 'software', 'programmer', 'it ', 'tech']
        return any(indicator in title_lower for indicator in tech_indicators)
    
    def generate_job_id(self, title, company, url):
        """Generate unique job ID"""
        # Create hash from URL (most unique identifier)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        # Clean title and company
        clean_title = re.sub(r'[^a-zA-Z0-9]', '', title)[:30]
        clean_company = re.sub(r'[^a-zA-Z0-9]', '', company)[:20]
        return f"{clean_company}_{clean_title}_{url_hash}"


class BrighterMondayScraper(JobScraper):
    """Scraper for BrighterMonday Kenya - UPDATED"""
    
    def scrape(self):
        """Scrape jobs from BrighterMonday"""
        jobs = []
        print("\n🔍 Scraping BrighterMonday Kenya...")
        
        try:
            # Try multiple category URLs
            urls = [
                "https://www.brightermonday.co.ke/jobs/technology-software",
                "https://www.brightermonday.co.ke/jobs/it-computer",
                "https://www.brightermonday.co.ke/jobs?q=developer",
                "https://www.brightermonday.co.ke/jobs?q=security+analyst",
                "https://www.brightermonday.co.ke/jobs?q=cybersecurity"
            ]
            
            for url in urls:
                try:
                    print(f"  Trying: {url}")
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code != 200:
                        print(f" Status code: {response.status_code}")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors (BrighterMonday changes their HTML)
                    job_cards = (
                        soup.find_all('article', class_='search-result') or
                        soup.find_all('div', class_='job-item') or
                        soup.find_all('div', class_='search__results__item') or
                        soup.find_all('div', {'data-job-id': True}) or
                        soup.find_all('li', class_='search-result') or
                        soup.select('.search-results article') or
                        soup.select('[data-testid="job-card"]')
                    )
                    
                    print(f"  Found {len(job_cards)} job cards")
                    
                    for card in job_cards[:15]:
                        try:
                            # Try different selectors for title
                            title_elem = (
                                card.find('h2') or 
                                card.find('h3') or
                                card.find('a', class_='job-title') or
                                card.find('div', class_='job-title') or
                                card.select_one('[data-testid="job-title"]') or
                                card.find('a', href=lambda x: x and '/job/' in x)
                            )
                            
                            # Try different selectors for company
                            company_elem = (
                                card.find('span', class_='company') or
                                card.find('div', class_='company-name') or
                                card.find('p', class_='company') or
                                card.select_one('[data-testid="company-name"]')
                            )
                            
                            # Try different selectors for URL
                            url_elem = (
                                card.find('a', href=lambda x: x and '/job/' in x) or
                                card.find('a', href=True)
                            )
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            company = company_elem.get_text(strip=True) if company_elem else 'Company in Kenya'
                            job_url = url_elem['href'] if url_elem else url
                            
                            if not job_url.startswith('http'):
                                job_url = 'https://www.brightermonday.co.ke' + job_url
                            
                            # Get description if available
                            desc_elem = card.find('div', class_='description') or card.find('p')
                            description = desc_elem.get_text(strip=True) if desc_elem else ''
                            
                            # Check relevance
                            if self.is_relevant(title):
                                job_id = self.generate_job_id(title, company, job_url)
                                
                                # Check if already exists
                                existing = Job.query.filter_by(job_id=job_id).first()
                                if not existing:
                                    job_data = {
                                        'job_id': job_id,
                                        'title': title,
                                        'company': company,
                                        'url': job_url,
                                        'description': description[:500],
                                        'source': 'BrighterMonday',
                                        'location': 'Kenya',
                                        'relevance_score': self.calculate_relevance(title, description, company),
                                        'status': 'Found',
                                        'posted_date': datetime.utcnow()
                                    }
                                    jobs.append(job_data)
                                    print(f" Found: {title} at {company}")
                        
                        except Exception as e:
                            continue
                    
                    if jobs:
                        break  # Stop if we found jobs
                    
                    time.sleep(2)  # Be respectful
                
                except Exception as e:
                    print(f"  Error with URL: {e}")
                    continue
            
            print(f"BrighterMonday: Found {len(jobs)} relevant jobs")
            return jobs
        
        except Exception as e:
            print(f"BrighterMonday scraper error: {e}")
            return []


class MyJobMagScraper(JobScraper):
    """Scraper for MyJobMag Kenya"""
    
    def scrape(self):
        """Scrape jobs from MyJobMag"""
        jobs = []
        print("\n🔍 Scraping MyJobMag Kenya...")
        
        try:
            urls = [
                "https://www.myjobmag.co.ke/jobs-by-field/information-communication-technology-ict",
                "https://www.myjobmag.co.ke/jobs-by-field/software-development",
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, headers=self.headers, timeout=15)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = soup.find_all('div', class_='job-list-item') or soup.find_all('article')
                    
                    for card in job_cards[:10]:
                        try:
                            title_elem = card.find('h2') or card.find('h3') or card.find('a')
                            company_elem = card.find('span', class_='company') or card.find('p')
                            url_elem = card.find('a', href=True)
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            company = company_elem.get_text(strip=True) if company_elem else 'Kenya Company'
                            job_url = url_elem['href'] if url_elem else url
                            
                            if not job_url.startswith('http'):
                                job_url = 'https://www.myjobmag.co.ke' + job_url
                            
                            if self.is_relevant(title):
                                job_id = f"MJM_{company}_{title}".replace(' ', '_')[:200]
                                
                                existing = Job.query.filter_by(job_id=job_id).first()
                                if not existing:
                                    job_data = {
                                        'job_id': job_id,
                                        'title': title,
                                        'company': company,
                                        'url': job_url,
                                        'source': 'MyJobMag',
                                        'location': 'Kenya',
                                        'relevance_score': self.calculate_relevance(title, '', company),
                                        'status': 'Found'
                                    }
                                    jobs.append(job_data)
                                    print(f" Found: {title}")
                        
                        except Exception as e:
                            continue
                
                except Exception as e:
                    continue
            
            print(f"MyJobMag: Found {len(jobs)} relevant jobs")
            return jobs
        
        except Exception as e:
            print(f"MyJobMag error: {e}")
            return []


class RemoteJobScraper(JobScraper):
    """Scraper for remote job boards"""
    
    def scrape(self):
        """Scrape remote job boards"""
        jobs = []
        print("\nScraping Remote Job Boards...")
        
        # We Work Remotely
        try:
            url = "https://weworkremotely.com/categories/remote-programming-jobs"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_listings = soup.find_all('li', class_='feature') or soup.find_all('li', {'data-feature-id': True})
            
            for listing in job_listings[:10]:
                try:
                    title_elem = listing.find('span', class_='title')
                    company_elem = listing.find('span', class_='company')
                    url_elem = listing.find('a', href=True)
                    
                    if title_elem and url_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else 'Remote Company'
                        job_url = 'https://weworkremotely.com' + url_elem['href'] if not url_elem['href'].startswith('http') else url_elem['href']
                        
                        if self.is_relevant(title):
                            job_id = f"WWR_{company}_{title}".replace(' ', '_')[:200]
                            
                            existing = Job.query.filter_by(job_id=job_id).first()
                            if not existing:
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
                                print(f" Remote: {title}")
                
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f" WeWorkRemotely error: {e}")
        
        # RemoteOK
        try:
            url = "https://remoteok.com/remote-developer-jobs"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_rows = soup.find_all('tr', class_='job')
            
            for row in job_rows[:10]:
                try:
                    title_elem = row.find('h2', itemprop='title')
                    company_elem = row.find('h3', itemprop='name')
                    url_elem = row.find('a', itemprop='url')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else 'Remote Tech Company'
                        job_url = 'https://remoteok.com' + url_elem['href'] if url_elem and not url_elem['href'].startswith('http') else url
                        
                        if self.is_relevant(title):
                            job_id = f"ROK_{company}_{title}".replace(' ', '_')[:200]
                            
                            existing = Job.query.filter_by(job_id=job_id).first()
                            if not existing:
                                job_data = {
                                    'job_id': job_id,
                                    'title': title,
                                    'company': company,
                                    'url': job_url,
                                    'source': 'RemoteOK',
                                    'location': 'Remote',
                                    'job_type': 'Remote',
                                    'relevance_score': self.calculate_relevance(title, '', company),
                                    'status': 'Found'
                                }
                                jobs.append(job_data)
                                print(f"Remote: {title}")
                
                except Exception as e:
                    continue
        
        except Exception as e:
            print(f"RemoteOK error: {e}")
        
        print(f" Remote Jobs: Found {len(jobs)} relevant jobs")
        return jobs


class GenericJobScraper(JobScraper):
    """Generic scraper for any job board - FALLBACK"""
    
    def scrape_url(self, url, source_name):
        """Generic scraping method"""
        jobs = []
        
        try:
            print(f"\n🔍 Scraping {source_name}...")
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                try:
                    text = link.get_text(strip=True)
                    
                    # Check if link text looks like a job title
                    if len(text) > 10 and len(text) < 150 and self.is_relevant(text):
                        title = text
                        job_url = link['href']
                        
                        if not job_url.startswith('http'):
                            from urllib.parse import urljoin
                            job_url = urljoin(url, job_url)
                        
                        # Try to find company nearby
                        parent = link.find_parent()
                        company = 'Tech Company'
                        
                        job_id = f"{source_name}_{title}".replace(' ', '_')[:200]
                        
                        existing = Job.query.filter_by(job_id=job_id).first()
                        if not existing:
                            job_data = {
                                'job_id': job_id,
                                'title': title,
                                'company': company,
                                'url': job_url,
                                'source': source_name,
                                'location': 'Kenya/Remote',
                                'relevance_score': self.calculate_relevance(title, '', company),
                                'status': 'Found'
                            }
                            jobs.append(job_data)
                            
                            if len(jobs) >= 10:
                                break
                
                except Exception as e:
                    continue
            
            print(f"{source_name}: Found {len(jobs)} jobs")
            return jobs
        
        except Exception as e:
            print(f"❌ {source_name} error: {e}")
            return []


def run_all_scrapers():
    """Run all scrapers and save to database"""
    print("\n" + "="*60)
    print("STARTING JOB SCRAPING")
    print("="*60)
    
    all_jobs = []
    
    scrapers = [
        BrighterMondayScraper(),
        MyJobMagScraper(),
        RemoteJobScraper(),
    ]
    
    for scraper in scrapers:
        try:
            jobs = scraper.scrape()
            all_jobs.extend(jobs)
            time.sleep(3)  # Be respectful between scrapers
        except Exception as e:
            print(f"❌ Error with scraper {scraper.__class__.__name__}: {e}")
    
    # Try generic scraper as fallback
    if len(all_jobs) < 5:
        print("\n⚠️ Few jobs found, trying additional sources...")
        generic = GenericJobScraper()
        fallback_urls = [
            ("https://www.fuzu.com/kenya/jobs", "Fuzu"),
            ("https://ke.linkedin.com/jobs/search?keywords=developer&location=Kenya", "LinkedIn"),
        ]
        
        for url, name in fallback_urls:
            try:
                jobs = generic.scrape_url(url, name)
                all_jobs.extend(jobs)
            except:
                continue
    
    # Save to database (with duplicate handling)
    saved_count = 0
    skipped_count = 0
    
    for job_data in all_jobs:
        try:
            # Check if job already exists
            existing = Job.query.filter_by(job_id=job_data['job_id']).first()
            
            if existing:
                skipped_count += 1
                print(f" Skipping duplicate: {job_data['title']}")
                continue
            
            # Save new job
            job = Job(**job_data)
            db.session.add(job)
            db.session.flush()  # Flush to catch errors before commit
            saved_count += 1
            
        except Exception as e:
            print(f" Error saving job '{job_data.get('title', 'Unknown')}': {e}")
            db.session.rollback()
            continue
    
    try:
        db.session.commit()
        print(f"\n" + "="*60)
        print(f" SCRAPING COMPLETE")
        print(f"   New jobs saved: {saved_count}")
        print(f"   Duplicates skipped: {skipped_count}")
        print("="*60)
        
        # Update daily stats
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today)
            db.session.add(stats)
        stats.jobs_found += saved_count
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f" Database error: {e}")
    
    return saved_count