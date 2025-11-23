"""
AI Job Validator using OpenAI
Validates freshness, extracts data, calculates relevance
"""

import requests
import json
from datetime import datetime

class AIJobValidator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def validate_job(self, job_data):
        """
        Use GPT to validate and enrich job data
        Returns enhanced job_data or None if invalid
        """
        
        prompt = f"""Analyze this job posting and return JSON ONLY (no markdown, no preamble):

Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Description: {job_data.get('description', '')[:500]}

Return:
{{
    "is_tech_job": true/false,
    "is_entry_level": true/false,
    "relevance_score": 0-100,
    "key_skills": ["skill1", "skill2"],
    "is_legitimate": true/false
}}

Criteria:
- Tech job: software, security, IT roles
- Entry level: junior, entry, 0-3 years experience
- Relevance: match for Python/React/Cybersecurity skills
- Legitimate: real job, not scam"""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 200
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return job_data
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Remove markdown formatting if present
            content = content.replace('```json', '').replace('```', '').strip()
            
            validation = json.loads(content)
            
            # Only keep legitimate tech jobs
            if not validation.get('is_legitimate') or not validation.get('is_tech_job'):
                return None
            
            # Enhance job data
            job_data['relevance_score'] = validation.get('relevance_score', 0)
            job_data['key_skills'] = validation.get('key_skills', [])
            job_data['is_entry_level'] = validation.get('is_entry_level', False)
            
            return job_data
            
        except Exception as e:
            print(f"  AI validation error: {e}")
            return job_data
    
    def batch_validate(self, jobs, max_jobs=20):
        """Validate multiple jobs, return only good ones"""
        validated = []
        
        for i, job in enumerate(jobs[:max_jobs]):
            print(f"  Validating {i+1}/{len(jobs[:max_jobs])}: {job.get('title')}")
            
            result = self.validate_job(job)
            
            if result and result.get('relevance_score', 0) >= 30:
                validated.append(result)
        
        print(f"AI Validator: {len(validated)}/{len(jobs[:max_jobs])} jobs passed")
        return validated