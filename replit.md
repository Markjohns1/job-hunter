# Job Hunter - Automated Job Application System

## Overview
Job Hunter is an automated job application system that scrapes job listings from multiple sources, displays them in a dashboard, and automates the application process with AI-generated cover letters.

## Current Status
✅ Flask application running on port 5000
✅ Database configured (PostgreSQL in production, SQLite fallback)
✅ Web scraping configured (Adzuna API)
✅ Job dashboard UI working
✅ Cover letter generation (OpenAI + template fallback)
✅ Professional email sending with HTML formatting
✅ Automatic CV attachment support
✅ Excel export functionality
✅ Telegram notifications support
✅ Production deployment configured

## Project Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0
- **Database**: SQLAlchemy (PostgreSQL/SQLite)
- **Migrations**: Flask-Migrate
- **Host**: 0.0.0.0:5000 (configured for Replit proxy)

### Frontend
- **Templates**: Jinja2
- **Styling**: Custom CSS (main.css, dashboard.css, components.css)
- **JavaScript**: Vanilla JS (api.js, dashboard.js)

### Key Features
1. **Job Scraping**
   - Adzuna API integration (15+ countries)
   - Searches for remote jobs across multiple regions
   - Deduplication and relevance scoring
   - Optional AI validation with OpenAI

2. **Job Board Dashboard**
   - Filter by status (Found, Applied, Interview, Rejected, Offer)
   - Sort by relevance, date, or company
   - Real-time stats and trends
   - Export to Excel

3. **Automated Applications**
   - AI-generated cover letters (OpenAI GPT-3.5-turbo)
   - Template-based fallback
   - Professional HTML email sending
   - Automatic CV attachment
   - Application tracking

4. **Notifications**
   - Telegram bot integration
   - Real-time application updates

## Required Environment Variables

### Essential (for job scraping)
- `ADZUNA_APP_ID` - Get free API key at https://developer.adzuna.com/
- `ADZUNA_API_KEY` - Get free API key at https://developer.adzuna.com/

### Optional (for AI features)
- `OPENAI_API_KEY` - For AI-generated cover letters (falls back to templates)

### Optional (for email sending)
- `MAIL_SERVER` - SMTP server (default: smtp.gmail.com)
- `MAIL_PORT` - SMTP port (default: 587)
- `MAIL_USERNAME` - Email address
- `MAIL_PASSWORD` - Email password or app-specific password

**Recommended Email Service**: Use Brevo (formerly Sendinblue)
- Free tier: 300 emails/day
- Better deliverability than Gmail
- Get SMTP credentials at https://www.brevo.com/
- Set `MAIL_SERVER=smtp-relay.brevo.com`

### Optional (for notifications)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

### Database (auto-configured in Replit)
- `DATABASE_URL` - PostgreSQL connection string (automatically set by Replit)

### Security
- `SECRET_KEY` - Flask session secret (auto-generated in dev)

## File Structure

```
job-hunter/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models (Job, Application, Stats)
│   ├── routes.py             # API endpoints and views
│   ├── utils.py              # Cover letter generation, exports
│   ├── email_service.py      # Email sending (needs completion)
│   ├── scrapers/
│   │   ├── adzuna.py         # Adzuna API scraper
│   │   ├── ai_validator.py   # OpenAI job validation
│   │   └── manager.py        # Scraper orchestration
│   ├── static/
│   │   ├── css/              # Stylesheets
│   │   └── js/               # Frontend JavaScript
│   └── templates/
│       ├── base.html         # Base template
│       └── dashboard.html    # Main dashboard
├── uploads/                  # CV storage (create this folder)
├── exports/                  # Excel exports
├── config.py                 # Application configuration
├── run.py                    # Application entry point
└── requirements.txt          # Python dependencies
```

## How to Use

### 1. Set Up API Keys
1. Get Adzuna API credentials:
   - Visit https://developer.adzuna.com/
   - Sign up for free account
   - Get your APP_ID and API_KEY
   - Add to Replit Secrets: `ADZUNA_APP_ID` and `ADZUNA_API_KEY`

2. (Optional) Get OpenAI API key for AI cover letters:
   - Visit https://platform.openai.com/
   - Add to Replit Secrets: `OPENAI_API_KEY`

### 2. Upload Your CV
- Create an `uploads/` folder if it doesn't exist
- Upload your CV as `cv.pdf` in the `uploads/` folder

### 3. Customize Your Profile
Edit `config.py` to update your information:
- Name, email, phone
- Skills and certifications
- Education and projects
- GitHub and LinkedIn profiles

### 4. Scrape Jobs
- Click "Scrape Jobs" button in dashboard
- Or use API: `POST /api/scrape`
- Jobs will be automatically saved to database

### 5. Review and Apply
- Browse jobs in dashboard
- Click "Apply" on jobs you like
- System generates cover letter automatically
- Track application status

## Known Issues & To-Do

### ⚠️ OpenAI Rate Limiting
**Issue**: API rate limits when generating many cover letters
**Solution**: Add delays between requests (implemented in batch processing)

### ✅ Future Improvements
1. Add error handling and user feedback in UI
2. Improve cover letter customization options
3. Add more job sources beyond Adzuna (LinkedIn, Indeed, etc.)
4. Polish UI/styling and mobile responsiveness
5. Add user authentication for multi-user support
6. Implement application analytics dashboard
7. Add resume parsing and job matching scores

## API Endpoints

### Jobs
- `GET /` - Dashboard view
- `GET /api/jobs` - Get all jobs (with filters)
- `GET /api/job/<id>` - Get job details
- `POST /api/scrape` - Trigger job scraping
- `POST /api/apply/<id>` - Apply to job
- `PATCH /api/job/<id>/status` - Update job status
- `DELETE /api/job/<id>` - Delete job
- `POST /api/bulk-apply` - Apply to multiple jobs

### Stats & Export
- `GET /api/stats` - Get dashboard statistics
- `GET /api/export` - Export jobs to Excel

## Database Models

### Job
- Basic info: title, company, location, URL
- Status tracking: Found → Applied → Interview → Rejected/Offer
- Relevance scoring
- Source tracking (Adzuna, etc.)

### Application
- Cover letter storage
- Email sent status
- Response tracking
- Follow-up dates

### Stats
- Daily statistics
- Application trends
- Success metrics

## Deployment

The application is configured to run on Replit with:
- **Deployment Type**: VM (always-on for scraping and state management)
- **Port**: 5000 (webview enabled)
- **Host**: 0.0.0.0 (allows Replit proxy)
- **Database**: PostgreSQL (auto-configured, auto-initialized on deploy)
- **Production Server**: Gunicorn with 2 workers
- **Build Step**: Automatic database schema initialization

The deployment automatically initializes the database schema on first deploy, so no manual migration steps are needed.

## Security Notes

- Never commit API keys or secrets to git
- Use Replit Secrets for all sensitive data
- Database files are gitignored
- Uploads folder is gitignored (contains personal CVs)

## Support & Resources

- Adzuna API Docs: https://developer.adzuna.com/docs/search
- OpenAI API Docs: https://platform.openai.com/docs
- Brevo API Docs: https://developers.brevo.com/
- Flask Docs: https://flask.palletsprojects.com/

## Recent Changes
- 2025-11-23: Initial Replit setup completed
  - Installed Python 3.11 and all dependencies
  - Created uploads/ and exports/ directories
  - Configured Flask workflow on port 5000
  - Database initialized (PostgreSQL support added)
  - Application running successfully
