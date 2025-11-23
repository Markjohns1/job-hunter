"""
Smart Adzuna API Scraper - Searches Multiple Countries
Automatically finds remote jobs from all supported regions
"""
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class AdzunaScraper:
    # All supported Adzuna countries
    SUPPORTED_COUNTRIES = {
        'gb': 'United Kingdom',
        'us': 'United States',
        'au': 'Australia',
        'ca': 'Canada',
        'de': 'Germany',
        'fr': 'France',
        'nl': 'Netherlands',
        'nz': 'New Zealand',
        'br': 'Brazil',
        'in': 'India',
        'pl': 'Poland',
        'za': 'South Africa',
        'at': 'Austria',
        'ch': 'Switzerland',
        'sg': 'Singapore'
    }
    
    def __init__(self, app_id=None, app_key=None):
        self.app_id = app_id or os.getenv('ADZUNA_APP_ID')
        self.app_key = app_key or os.getenv('ADZUNA_API_KEY')
        
        if not self.app_id or not self.app_key:
            print("WARNING: Adzuna API credentials not configured!")
            print("Get your free API key at: https://developer.adzuna.com/")
    
    def scrape(self, keywords=None, max_days_old=7, remote_only=True, max_jobs_per_country=5):
        """
        Smart scraper that searches multiple countries
        
        Args:
            keywords: List of job search terms
            max_days_old: Only get jobs posted within this many days
            remote_only: Focus on remote jobs
            max_jobs_per_country: Limit results per country to avoid duplicates
        """
        all_jobs = []
        seen_jobs = set()  # Track unique jobs by title+company
        
        if not self.app_id or not self.app_key:
            print("ERROR: Adzuna API credentials missing")
            return all_jobs
        
        if not keywords:
            keywords = [
                "python developer remote",
                "software engineer remote",
                "cybersecurity remote",
                "junior developer remote"
            ]
        
        print(f"Searching {len(self.SUPPORTED_COUNTRIES)} countries...")
        print("=" * 60)
        
        # Search each country
        for country_code, country_name in self.SUPPORTED_COUNTRIES.items():
            country_jobs = self._search_country(
                country_code, 
                country_name, 
                keywords, 
                max_days_old,
                max_jobs_per_country
            )
            
            # Add only unique jobs
            for job in country_jobs:
                job_key = f"{job['title']}|{job['company']}".lower()
                if job_key not in seen_jobs:
                    seen_jobs.add(job_key)
                    all_jobs.append(job)
        
        print("=" * 60)
        print(f"TOTAL: {len(all_jobs)} unique jobs found across all countries")
        return all_jobs
    
    def _search_country(self, country_code, country_name, keywords, max_days_old, max_results):
        """Search a single country"""
        base_url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search"
        jobs = []
        
        for keyword in keywords:
            if len(jobs) >= max_results:
                break
                
            try:
                params = {
                    'app_id': self.app_id,
                    'app_key': self.app_key,
                    'results_per_page': max_results,
                    'what': keyword,
                    'sort_by': 'date',
                    'max_days_old': max_days_old
                }
                
                response = requests.get(f"{base_url}/1", params=params, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    print(f"  {country_name}: Found {len(results)} jobs for '{keyword}'")
                
                for job in results:
                    if len(jobs) >= max_results:
                        break
                    
                    # Extract and clean job data
                    job_data = {
                        'title': job.get('title', ''),
                        'company': job.get('company', {}).get('display_name', 'Unknown'),
                        'location': self._format_location(job, country_name),
                        'description': self._clean_description(job.get('description', '')),
                        'url': job.get('redirect_url', ''),
                        'salary_min': job.get('salary_min'),
                        'salary_max': job.get('salary_max'),
                        'contract_type': job.get('contract_type', 'Full-time'),
                        'posted_date': job.get('created'),
                        'source': f'Adzuna ({country_code.upper()})',
                        'country': country_name
                    }
                    
                    jobs.append(job_data)
                
            except Exception as e:
                continue
        
        return jobs
    
    def _format_location(self, job, country_name):
        """Format location nicely"""
        location = job.get('location', {}).get('display_name', '')
        
        # If remote job, mark it clearly
        if 'remote' in location.lower() or 'anywhere' in location.lower():
            return f"Remote ({country_name})"
        
        return location if location else country_name
    
    def _clean_description(self, description):
        """Clean and truncate description"""
        if not description:
            return ""
        
        # Remove HTML tags
        import re
        clean = re.sub('<[^<]+?>', '', description)
        
        # Truncate to 1000 chars
        return clean[:1000].strip()
    
    def search_specific_countries(self, country_codes, keywords=None, max_days_old=7):
        """
        Search only specific countries
        
        Args:
            country_codes: List like ['us', 'gb', 'ca']
        """
        all_jobs = []
        
        if not keywords:
            keywords = [
                "python developer remote",
                "software engineer remote",
                "cybersecurity remote"
            ]
        
        for code in country_codes:
            if code in self.SUPPORTED_COUNTRIES:
                country_name = self.SUPPORTED_COUNTRIES[code]
                jobs = self._search_country(code, country_name, keywords, max_days_old, 10)
                all_jobs.extend(jobs)
        
        return all_jobs
    
    def get_remote_jobs_only(self, keywords=None, max_days_old=7, total_limit=50):
        """
        Get remote jobs that can be done from anywhere
        Focuses on countries with most remote opportunities
        """
        # Countries with most remote jobs
        priority_countries = ['us', 'gb', 'ca', 'de', 'nl', 'au']
        
        if not keywords:
            keywords = [
                "remote python developer",
                "remote software engineer",
                "remote cybersecurity",
                "work from home developer",
                "fully remote engineer"
            ]
        
        print("Searching for remote jobs across top countries...")
        all_jobs = []
        
        for country_code in priority_countries:
            if len(all_jobs) >= total_limit:
                break
            
            country_name = self.SUPPORTED_COUNTRIES[country_code]
            jobs = self._search_country(
                country_code, 
                country_name, 
                keywords, 
                max_days_old,
                10
            )
            all_jobs.extend(jobs)
        
        return all_jobs[:total_limit]