# Job Hunter - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Features & Functionality](#features--functionality)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Job Scraping System](#job-scraping-system)
9. [Email Integration](#email-integration)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)
12. [Development Guide](#development-guide)

---

## Overview

Job Hunter is an automated job application platform built with Flask that helps streamline the job search process. The system automatically scrapes job listings from multiple sources, displays them in an organized dashboard, generates customized cover letters using AI, and can automate the application submission process.

### Key Capabilities
- Multi-country job scraping via Adzuna API (15+ countries supported)
- Intelligent job deduplication and relevance scoring
- AI-powered cover letter generation with OpenAI integration
- Template-based cover letter fallback system
- Real-time application tracking and statistics
- Excel export functionality for job data
- Telegram notification system
- Responsive web dashboard interface

### Technology Stack
- Backend: Flask 3.0.0 (Python)
- Database: PostgreSQL (production) / SQLite (development)
- ORM: SQLAlchemy with Flask-Migrate
- Frontend: Vanilla JavaScript, HTML5, CSS3
- Production Server: Gunicorn
- External APIs: Adzuna, OpenAI, Telegram

---

## System Architecture

### Application Structure

```
job-hunter/
├── app/                          # Main application package
│   ├── __init__.py              # Flask application factory
│   ├── models.py                # Database models
│   ├── routes.py                # API endpoints and views
│   ├── utils.py                 # Utility functions
│   ├── email_service.py         # Email sending service
│   ├── scrapers/                # Job scraping modules
│   │   ├── __init__.py
│   │   ├── adzuna.py           # Adzuna API integration
│   │   ├── ai_validator.py     # OpenAI job validation
│   │   └── manager.py          # Scraper orchestration
│   ├── static/                  # Static assets
│   │   ├── css/
│   │   │   ├── main.css        # Global styles
│   │   │   ├── dashboard.css   # Dashboard-specific styles
│   │   │   └── components.css  # Component styles
│   │   └── js/
│   │       ├── api.js          # API client functions
│   │       └── dashboard.js    # Dashboard functionality
│   └── templates/               # Jinja2 templates
│       ├── base.html           # Base template
│       └── dashboard.html      # Main dashboard view
├── uploads/                     # CV and document storage
├── exports/                     # Generated Excel files
├── config.py                    # Application configuration
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── .replit                      # Replit configuration

```

### Data Flow

1. Job Scraping: Adzuna API -> ScraperManager -> Database
2. Job Validation: Database -> AIValidator -> Database (updated)
3. Application Flow: User -> Dashboard -> API -> CoverLetterGenerator -> EmailService
4. Notification Flow: Application Event -> Telegram API -> User

---

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL (optional, SQLite used as fallback)
- Adzuna API credentials (free tier available)
- OpenAI API key (optional, for AI cover letters)

### Local Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create required directories:
   ```bash
   mkdir -p uploads exports
   ```

4. Set up environment variables (see Configuration section)

5. Initialize database:
   ```bash
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. Run development server:
   ```bash
   python run.py
   ```

7. Access dashboard at http://localhost:5000

### Replit Setup

The application is pre-configured for Replit deployment:
- Python 3.11 module installed
- All dependencies in requirements.txt
- Workflow configured on port 5000
- Database auto-initialization on deploy
- Gunicorn production server ready

---

## Configuration

### Environment Variables

#### Required for Job Scraping
- `ADZUNA_APP_ID` - Application ID from Adzuna Developer Portal
- `ADZUNA_API_KEY` - API key from Adzuna Developer Portal

Get free credentials at: https://developer.adzuna.com/

#### Optional - AI Features
- `OPENAI_API_KEY` - OpenAI API key for AI-generated cover letters

If not provided, system falls back to template-based cover letters.

#### Optional - Email Sending
- `MAIL_SERVER` - SMTP server hostname (default: smtp.gmail.com)
- `MAIL_PORT` - SMTP port number (default: 587)
- `MAIL_USERNAME` - Email address for sending
- `MAIL_PASSWORD` - Email password or app-specific password

Recommended: Use Brevo (formerly Sendinblue) for better deliverability
- Free tier: 300 emails/day
- SMTP: smtp-relay.brevo.com
- Get API key at: https://www.brevo.com/

#### Optional - Notifications
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

#### Database
- `DATABASE_URL` - PostgreSQL connection string (auto-configured on Replit)

If not provided, uses SQLite: sqlite:///jobhunter.db

#### Security
- `SECRET_KEY` - Flask session secret key (auto-generated in development)

### Application Configuration (config.py)

#### Job Search Settings
```python
KEYWORDS = [
    'SOC Analyst', 'Security Analyst', 'Cybersecurity',
    'Junior Developer', 'DevSecOps', 'InfoSec',
    'Security Engineer', 'Threat Analyst', 'Python Developer',
    'Full Stack Developer', 'Backend Developer'
]

LOCATIONS = ['Kenya', 'Remote', 'Nairobi', 'East Africa']
```

#### Scraping Configuration
- `SCRAPE_INTERVAL` - Time between automatic scrapes (21600 seconds = 6 hours)
- `MAX_APPLICATIONS_PER_DAY` - Daily application limit (15)

#### Candidate Profile
Update your personal information in `config.py`:
```python
CANDIDATE_PROFILE = {
    'name': 'Your Name',
    'email': 'your.email@example.com',
    'phone': '+1-XXX-XXX-XXXX',
    'github': 'https://github.com/yourusername',
    'linkedin': 'https://linkedin.com/in/yourprofile',
    'skills': [...],
    'education': '...',
    'certifications': [...],
    'key_project': '...'
}
```

---

## Features & Functionality

### 1. Job Scraping System

#### Automated Job Discovery
- Searches 15+ countries simultaneously via Adzuna API
- Configurable search keywords and locations
- Date-based filtering (only recent postings)
- Remote job prioritization
- Automatic deduplication across regions

#### Supported Countries
United Kingdom, United States, Australia, Canada, Germany, France, Netherlands, New Zealand, Brazil, India, Poland, South Africa, Austria, Switzerland, Singapore

#### Scraping Methods
- **Full Scrape**: Search all supported countries
- **Targeted Scrape**: Search specific countries only
- **Remote-Only Scrape**: Focus on remote positions

### 2. Job Dashboard

#### Features
- Real-time job listing display
- Multi-criteria filtering:
  - Status (Found, Applied, Interview, Rejected, Offer)
  - Source (Adzuna regions)
  - Sort by relevance, date, or company
- Job statistics overview
- Trend visualization
- Bulk actions support

#### Statistics Tracked
- Total jobs found
- Applications sent
- Pending applications
- Interview invitations
- Job offers received
- Rejection count
- Response rate percentage
- High-relevance jobs

### 3. Cover Letter Generation

#### AI-Powered (OpenAI)
When OpenAI API key is configured:
- Customized cover letters using GPT-3.5-turbo
- Job-specific content tailored to description
- Integrates candidate profile information
- Professional tone and structure
- 300-word optimized length

#### Template-Based Fallback
When OpenAI is unavailable:
- Professional template with candidate details
- Dynamic job title and company insertion
- Skills and certification highlighting
- Consistent professional formatting

### 4. Application Tracking

#### Status Management
- **Found**: Newly discovered job
- **Applied**: Application submitted
- **Interview**: Interview scheduled
- **Rejected**: Application declined
- **Offer**: Job offer received

#### Application Data
- Cover letter storage
- Application timestamps
- Email sent status
- Follow-up scheduling
- Response tracking
- Notes and comments

### 5. Export Functionality

Generate Excel reports with:
- Job title and company
- Location and status
- Relevance scores
- Application URLs
- Date discovered and applied
- Source information

Export filtered subsets or complete job database.

### 6. Notification System

Telegram integration provides:
- Scraping completion alerts
- Application submission confirmations
- Real-time status updates
- Error notifications

---

## API Reference

### Job Endpoints

#### GET /
Dashboard home page view.

**Response**: HTML dashboard page

#### GET /api/jobs
Retrieve all jobs with optional filtering.

**Query Parameters**:
- `status` - Filter by status (all, Found, Applied, Interview, Rejected, Offer)
- `source` - Filter by source (all, or specific Adzuna region)
- `sort` - Sort order (relevance, date, company)
- `page` - Page number (default: 1)

**Response**:
```json
{
  "jobs": [...],
  "total": 150,
  "pages": 3,
  "current_page": 1
}
```

#### GET /api/job/<job_id>
Get detailed information for specific job.

**Response**:
```json
{
  "job": {...},
  "description": "Full job description",
  "salary": "50000-70000",
  "job_type": "Full-time",
  "application": {...},
  "cover_letter": "..."
}
```

#### POST /api/scrape
Trigger job scraping process.

**Response**:
```json
{
  "success": true,
  "jobs_found": 45,
  "message": "Successfully scraped 45 new jobs"
}
```

#### POST /api/apply/<job_id>
Apply to specific job.

**Request Body** (optional):
```json
{
  "send_email": true,
  "recipient_email": "hr@company.com"
}
```

**Response**:
```json
{
  "success": true,
  "email_sent": true,
  "cover_letter": "...",
  "message": "Application sent via email"
}
```

#### PATCH /api/job/<job_id>/status
Update job status.

**Request Body**:
```json
{
  "status": "Interview",
  "cover_letter": "..." (optional)
}
```

**Response**:
```json
{
  "success": true,
  "message": "Status updated successfully"
}
```

#### DELETE /api/job/<job_id>
Delete specific job.

**Response**:
```json
{
  "success": true
}
```

#### POST /api/bulk-apply
Apply to multiple jobs simultaneously.

**Request Body**:
```json
{
  "job_ids": [1, 2, 3, 4, 5]
}
```

**Response**:
```json
{
  "success": true,
  "applied": 5,
  "errors": []
}
```

### Statistics Endpoints

#### GET /api/stats
Retrieve dashboard statistics and trends.

**Response**:
```json
{
  "stats": {
    "total_jobs_found": 150,
    "jobs_applied": 23,
    "pending_applications": 127,
    "interviews_scheduled": 5,
    "offers_received": 2,
    "rejections": 8,
    "high_relevance": 45,
    "applications_today": 3,
    "response_rate": 65.2
  },
  "trends": {
    "dates": ["11/17", "11/18", "11/19", ...],
    "jobs_found": [12, 8, 15, ...],
    "jobs_applied": [2, 3, 4, ...],
    "interviews": [0, 1, 0, ...]
  }
}
```

#### GET /api/export
Export jobs to Excel file.

**Query Parameters**:
- `status` - Filter by status (optional)

**Response**: Excel file download

---

## Database Schema

### Job Model
Primary table for job listings.

**Fields**:
- `id` (Integer, PK) - Auto-incrementing ID
- `job_id` (String, Unique) - MD5 hash identifier
- `title` (String) - Job title
- `company` (String) - Company name
- `location` (String) - Job location
- `url` (String) - Application URL
- `description` (Text) - Full job description
- `source` (String) - Data source (e.g., "Adzuna (US)")
- `salary` (String) - Salary information
- `job_type` (String) - Employment type
- `status` (String) - Application status
- `relevance_score` (Float) - Match score (0-100)
- `posted_date` (DateTime) - Original posting date
- `found_date` (DateTime) - Discovery timestamp
- `applied_date` (DateTime) - Application timestamp

**Relationships**:
- One-to-one with Application model

### Application Model
Tracks application details.

**Fields**:
- `id` (Integer, PK) - Auto-incrementing ID
- `job_id` (Integer, FK) - References Job.id
- `cover_letter` (Text) - Generated cover letter
- `cv_version` (String) - CV version used
- `notes` (Text) - Application notes
- `email_sent` (Boolean) - Email status
- `follow_up_date` (DateTime) - Follow-up reminder
- `last_contact` (DateTime) - Last communication
- `response_received` (Boolean) - Response flag
- `response_date` (DateTime) - Response timestamp
- `response_type` (String) - Type of response
- `applied_date` (DateTime) - Application date
- `updated_date` (DateTime) - Last update

### Stats Model
Daily statistics tracking.

**Fields**:
- `id` (Integer, PK) - Auto-incrementing ID
- `date` (Date, Unique) - Statistics date
- `jobs_found` (Integer) - New jobs discovered
- `jobs_applied` (Integer) - Applications submitted
- `interviews_scheduled` (Integer) - Interviews booked
- `rejections_received` (Integer) - Rejections count
- `offers_received` (Integer) - Offers count
- `created_at` (DateTime) - Record creation

---

## Job Scraping System

### Adzuna Scraper Architecture

#### Initialization
```python
from app.scrapers.adzuna import AdzunaScraper

scraper = AdzunaScraper(
    app_id='your_app_id',
    app_key='your_api_key'
)
```

#### Scraping Methods

**Full Multi-Country Scrape**:
```python
jobs = scraper.scrape(
    keywords=['python developer', 'software engineer'],
    max_days_old=7,
    remote_only=True,
    max_jobs_per_country=5
)
```

**Specific Countries**:
```python
jobs = scraper.search_specific_countries(
    country_codes=['us', 'gb', 'ca'],
    keywords=['cybersecurity'],
    max_days_old=14
)
```

**Remote Jobs Only**:
```python
jobs = scraper.get_remote_jobs_only(
    keywords=['remote developer'],
    max_days_old=7,
    total_limit=50
)
```

#### Job Data Structure
```python
{
    'title': 'Senior Python Developer',
    'company': 'Tech Corp',
    'location': 'Remote (United States)',
    'description': 'Full job description...',
    'url': 'https://...',
    'salary_min': 80000,
    'salary_max': 120000,
    'contract_type': 'Full-time',
    'posted_date': '2025-11-20',
    'source': 'Adzuna (US)',
    'country': 'United States'
}
```

### AI Validation (Optional)

When OpenAI API key is configured:
- Validates job relevance using GPT models
- Scores jobs based on skill match
- Filters out irrelevant postings
- Batch processing support (max 20 jobs)

### Scraper Manager

Orchestrates all scraping operations:
- Executes Adzuna scraper
- Applies AI validation (if enabled)
- Handles deduplication
- Saves to database
- Updates statistics
- Sends notifications

**Usage**:
```python
from app.scrapers.manager import ScraperManager

manager = ScraperManager()
count = manager.scrape_all()
```

---

## Email Integration

### Current Status
Email sending functionality is fully implemented and ready to use.

### Features
- Professional HTML and plain text email formatting
- Automatic CV attachment support
- Uses candidate profile from config.py
- Retry logic with fallback to SSL (port 465)
- Connection testing capability
- Detailed error reporting

### Recommended Setup: Brevo

#### Advantages
- 300 emails/day free tier
- Better deliverability than Gmail
- SMTP authentication supported
- No 2FA complications
- Professional sending infrastructure

#### Configuration
1. Sign up at https://www.brevo.com/
2. Generate SMTP credentials
3. Set environment variables in Replit Secrets:
   ```
   MAIL_SERVER=smtp-relay.brevo.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-brevo-smtp-key
   ```

### Alternative: Gmail

If using Gmail (not recommended for high volume):
1. Enable 2-Factor Authentication
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Set environment variables:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

### Usage

#### Sending Applications
The email service is automatically called when you click "Apply" on a job and provide an email address.

**API Call Example**:
```javascript
fetch('/api/apply/123', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        send_email: true,
        recipient_email: 'hr@company.com'
    })
})
```

#### Testing Connection
```python
from app.email_service import EmailService

service = EmailService()
success, message = service.test_connection()
print(f"Connection: {message}")
```

#### Email Content
Each email includes:
- Professional HTML formatting with company branding
- Full cover letter text
- Your contact information with clickable links
- Attached CV (if available in uploads/ folder)
- Plain text fallback for email clients without HTML support

---

## Deployment Guide

### Replit Deployment

#### Configuration
The application is configured for Replit VM deployment:
- Deployment target: VM (always-on)
- Production server: Gunicorn with 2 workers
- Port: 5000 (automatically exposed)
- Host: 0.0.0.0 (allows Replit proxy)

#### Deployment Process
1. Configure environment variables in Replit Secrets
2. Click "Deploy" button in Replit
3. Build step automatically initializes database
4. Gunicorn starts application
5. Application accessible via provided URL

#### Build Command
Automatically runs on deployment:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```

#### Run Command
Production server command:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 run:app
```

### Manual Deployment

#### Using Gunicorn
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 run:app
```

#### Using uWSGI
```bash
uwsgi --http 0.0.0.0:5000 --wsgi-file run.py --callable app
```

### Database Migration

For production databases:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## Troubleshooting

### Common Issues

#### Job Scraping Fails
**Symptom**: No jobs found, API errors

**Solutions**:
- Verify ADZUNA_APP_ID and ADZUNA_API_KEY are set correctly
- Check API rate limits (free tier: 250 calls/month)
- Confirm internet connectivity
- Review error logs for API response codes

#### Cover Letters Not Generated
**Symptom**: Template fallback always used

**Solutions**:
- Verify OPENAI_API_KEY is configured
- Check OpenAI account has credits
- Review API rate limits
- Examine error logs for API failures

#### Database Errors
**Symptom**: Cannot save jobs, migration failures

**Solutions**:
- Check DATABASE_URL is valid
- Ensure PostgreSQL is running (if used)
- Verify database permissions
- Run: `db.create_all()` to initialize schema
- For migrations: `flask db upgrade`

#### Email Sending Blocked
**Symptom**: Emails fail to send

**Solutions**:
- Use cloud service (Brevo) instead of Gmail
- Verify SMTP credentials
- Check firewall/ISP restrictions
- Enable "Less secure app access" (Gmail only)
- Use app-specific passwords for 2FA accounts

#### Application Won't Start
**Symptom**: Workflow fails, import errors

**Solutions**:
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version (3.11+ required)
- Verify all environment variables
- Review startup logs for specific errors

#### Port Already in Use
**Symptom**: Cannot bind to port 5000

**Solutions**:
- Kill existing process: `lsof -ti:5000 | xargs kill`
- Change port in run.py
- Use different port for development

---

## Development Guide

### Project Structure Best Practices

#### Adding New Features
1. Create feature branch
2. Add route in `app/routes.py`
3. Update models if needed in `app/models.py`
4. Add utility functions in `app/utils.py`
5. Create frontend components in static/
6. Update documentation

#### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to all functions
- Keep functions focused and small
- Use meaningful variable names

#### Testing
Create test files in `tests/` directory:
- Unit tests for utilities
- Integration tests for API endpoints
- End-to-end tests for workflows

### Adding New Job Sources

1. Create scraper in `app/scrapers/`:
```python
class NewSourceScraper:
    def scrape(self, keywords):
        # Implementation
        return jobs_list
```

2. Register in `manager.py`:
```python
if self.new_source_enabled:
    scraper = NewSourceScraper()
    jobs = scraper.scrape()
    all_jobs.extend(jobs)
```

3. Update configuration for credentials

### Database Schema Changes

1. Update models in `app/models.py`
2. Create migration:
   ```bash
   flask db migrate -m "Description"
   ```
3. Review generated migration file
4. Apply migration:
   ```bash
   flask db upgrade
   ```

### Frontend Development

#### File Organization
- Global styles: `static/css/main.css`
- Page-specific: `static/css/[page].css`
- Components: `static/css/components.css`
- API calls: `static/js/api.js`
- Page logic: `static/js/[page].js`

#### API Integration
Use provided API client in `api.js`:
```javascript
api.getJobs(filters)
    .then(data => console.log(data))
    .catch(error => console.error(error));
```

### Security Considerations

#### Never Commit
- API keys or secrets
- Database credentials
- Personal information
- CV files
- Email passwords

#### Always Use
- Environment variables for secrets
- HTTPS in production
- Input validation
- SQL parameterization (SQLAlchemy handles this)
- CSRF protection (Flask handles this)

#### Rate Limiting
Implement for:
- API endpoints
- Email sending
- Job scraping
- Cover letter generation

### Performance Optimization

#### Database
- Add indexes for frequently queried fields
- Use pagination for large result sets
- Implement caching for statistics
- Archive old data periodically

#### API Responses
- Enable gzip compression
- Minimize JSON payload sizes
- Use ETags for caching
- Implement request debouncing

#### Frontend
- Minimize CSS/JS files
- Use CDN for static assets
- Lazy load job listings
- Cache API responses client-side

---

## Additional Resources

### External Documentation
- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Adzuna API: https://developer.adzuna.com/docs/search
- OpenAI API: https://platform.openai.com/docs
- Brevo API: https://developers.brevo.com/
- Telegram Bot API: https://core.telegram.org/bots/api

### Support
For issues and questions:
1. Check troubleshooting section
2. Review error logs
3. Consult API documentation
4. Search GitHub issues (if open source)

### Contributing
Follow development guide for code contributions.
Ensure all tests pass before submitting.
Update documentation for new features.

---

## Version History

### Current Version
- Initial Replit deployment complete
- Adzuna scraping functional
- Dashboard operational
- AI cover letter generation working
- Template fallback implemented
- Excel export available
- Telegram notifications ready
- Database schema finalized

### Pending Improvements
- Complete email sending implementation
- Add user authentication system
- Implement additional job sources
- Enhanced UI/UX design
- Mobile responsive improvements
- Advanced filtering options
- Application analytics dashboard
- CV parsing and matching

---

## License & Credits

This application uses the following open-source libraries:
- Flask and extensions (BSD License)
- SQLAlchemy (MIT License)
- BeautifulSoup4 (MIT License)
- Pandas (BSD License)
- Requests (Apache 2.0)

Third-party services:
- Adzuna (API Terms of Service)
- OpenAI (API Terms of Service)
- Brevo (Terms of Service)
- Telegram (Terms of Service)
