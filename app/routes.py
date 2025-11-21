"""
Flask routes for JobHunterPro
"""
import os
from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime
from app.models import Job, Application, Stats, db
from app.scrapers import run_all_scrapers
from app.utils import (
    generate_cover_letter, 
    export_to_excel, 
    get_daily_stats, 
    get_weekly_trends,
    send_telegram_notification
)

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Main dashboard"""
    stats = get_daily_stats()
    return render_template('dashboard.html', stats=stats)


@main.route('/api/jobs')
def get_jobs():
    """Get all jobs with filters"""
    status = request.args.get('status', 'all')
    source = request.args.get('source', 'all')
    sort_by = request.args.get('sort', 'relevance')
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Increased from 20
    
    query = Job.query
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    if source != 'all':
        query = query.filter_by(source=source)
    
    # Apply sorting
    if sort_by == 'relevance':
        query = query.order_by(Job.relevance_score.desc())
    elif sort_by == 'date':
        query = query.order_by(Job.found_date.desc())
    elif sort_by == 'company':
        query = query.order_by(Job.company)
    
    # Get all jobs for now (no pagination issues)
    jobs = query.all()
    
    print(f"API: Returning {len(jobs)} jobs")  # Debug print
    
    return jsonify({
        'jobs': [job.to_dict() for job in jobs],
        'total': len(jobs),
        'pages': 1,
        'current_page': 1
    })


@main.route('/api/job/<int:job_id>')
def get_job_details(job_id):
    """Get detailed job information"""
    job = Job.query.get_or_404(job_id)
    
    response = {
        'job': job.to_dict(),
        'description': job.description,
        'salary': job.salary,
        'job_type': job.job_type
    }
    
    if job.application:
        response['application'] = job.application.to_dict()
        response['cover_letter'] = job.application.cover_letter
    
    return jsonify(response)


@main.route('/api/scrape', methods=['POST'])
def scrape_jobs():
    """Trigger job scraping"""
    try:
        count = run_all_scrapers()
        
        # Send notification
        send_telegram_notification(
            f"<b>Job Scraping Complete</b>\n\n"
            f"Found {count} new jobs!\n"
            f"Check your dashboard: http://localhost:5000"
        )
        
        return jsonify({
            'success': True,
            'jobs_found': count,
            'message': f'Successfully scraped {count} new jobs'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/apply/<int:job_id>', methods=['POST'])
def apply_to_job(job_id):
    """Apply to a specific job"""
    job = Job.query.get_or_404(job_id)
    
    try:
        # Generate cover letter
        cover_letter = generate_cover_letter(
            job.title, 
            job.company, 
            job.description or ''
        )
        
        # Create application record
        application = Application(
            job_id=job.id,
            cover_letter=cover_letter,
            applied_date=datetime.utcnow(),
            email_sent=False  # Will be True when email sending is implemented
        )
        
        # Update job status
        job.status = 'Applied'
        job.applied_date = datetime.utcnow()
        
        db.session.add(application)
        db.session.commit()
        
        # Update daily stats
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today)
            db.session.add(stats)
        stats.jobs_applied += 1
        db.session.commit()
        
        # Send notification
        send_telegram_notification(
            f"<b>Application Sent!</b>\n\n"
            f"Job: {job.title}\n"
            f"Company: {job.company}\n"
            f"URL: {job.url}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'cover_letter': cover_letter
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/job/<int:job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """Update job status"""
    job = Job.query.get_or_404(job_id)
    data = request.get_json()
    
    new_status = data.get('status')
    if new_status:
        job.status = new_status
        
        # Update stats
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today)
            db.session.add(stats)
        
        if new_status == 'Interview':
            stats.interviews_scheduled += 1
        elif new_status == 'Rejected':
            stats.rejections_received += 1
        elif new_status == 'Offer':
            stats.offers_received += 1
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'No status provided'}), 400


@main.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    stats = get_daily_stats()
    trends = get_weekly_trends()
    
    return jsonify({
        'stats': stats,
        'trends': trends
    })


@main.route('/api/export')
def export_jobs():
    """Export jobs to Excel"""
    status = request.args.get('status', 'all')
    
    query = Job.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    jobs = query.all()
    
    if not jobs:
        return jsonify({'error': 'No jobs to export'}), 404
    
    try:
        filepath = export_to_excel(jobs)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500


@main.route('/api/bulk-apply', methods=['POST'])
def bulk_apply():
    """Apply to multiple jobs at once"""
    data = request.get_json()
    job_ids = data.get('job_ids', [])
    
    if not job_ids:
        return jsonify({'error': 'No jobs selected'}), 400
    
    applied = 0
    errors = []
    
    for job_id in job_ids:
        try:
            job = Job.query.get(job_id)
            if job and job.status == 'Found':
                cover_letter = generate_cover_letter(job.title, job.company)
                
                application = Application(
                    job_id=job.id,
                    cover_letter=cover_letter,
                    applied_date=datetime.utcnow()
                )
                
                job.status = 'Applied'
                job.applied_date = datetime.utcnow()
                
                db.session.add(application)
                applied += 1
        
        except Exception as e:
            errors.append(f"Job {job_id}: {str(e)}")
    
    try:
        db.session.commit()
        
        # Update stats
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today)
            db.session.add(stats)
        stats.jobs_applied += applied
        db.session.commit()
        
        return jsonify({
            'success': True,
            'applied': applied,
            'errors': errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500