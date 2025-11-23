"""
Flask routes for Job Hunter
"""

import os
from flask import Blueprint, render_template, jsonify, request, send_file
from datetime import datetime
from app.models import Job, Application, Stats, db
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
    per_page = 50
    
    query = Job.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    if source != 'all':
        query = query.filter_by(source=source)
    
    if sort_by == 'relevance':
        query = query.order_by(Job.relevance_score.desc())
    elif sort_by == 'date':
        query = query.order_by(Job.found_date.desc())
    elif sort_by == 'company':
        query = query.order_by(Job.company)
    
    jobs = query.all()
    
    print(f"API: Returning {len(jobs)} jobs")
    
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
        from app.scrapers.manager import ScraperManager
        
        manager = ScraperManager()
        count = manager.scrape_all()
        
        send_telegram_notification(
            f"Job Scraping Complete\n\n"
            f"Found {count} new jobs!\n"
            f"Check your dashboard: http://localhost:5000"
        )
        
        return jsonify({
            'success': True,
            'jobs_found': count,
            'message': f'Successfully scraped {count} new jobs'
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Scraping error: {error_details}")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details
        }), 500


@main.route('/api/apply/<int:job_id>', methods=['POST'])
def apply_to_job(job_id):
    """Apply to a specific job with email support"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.get_json() or {}
        
        cover_letter = generate_cover_letter(
            job.title, 
            job.company, 
            job.description or ''
        )
        
        send_email = data.get('send_email', False)
        recipient_email = data.get('recipient_email')
        
        if send_email and recipient_email:
            try:
                from app.email_service import EmailService
                email_service = EmailService()
                
                cv_path = os.path.join('uploads', 'cv.pdf')
                
                email_service.send_application(
                    to_email=recipient_email,
                    job_title=job.title,
                    company=job.company,
                    cover_letter=cover_letter,
                    cv_path=cv_path if os.path.exists(cv_path) else None
                )
                
                return jsonify({
                    'success': True,
                    'email_sent': True,
                    'message': 'Application sent via email',
                    'cover_letter': cover_letter
                })
                
            except Exception as e:
                print(f"Email error: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Email failed: {str(e)}'
                }), 500
        
        return jsonify({
            'success': True,
            'email_sent': False,
            'cover_letter': cover_letter,
            'job': job.to_dict()
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Apply error: {error_details}")
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/api/job/<int:job_id>/status', methods=['PATCH', 'PUT'])
def update_job_status(job_id):
    """Update job status"""
    try:
        job = Job.query.get_or_404(job_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        new_status = data.get('status')
        cover_letter = data.get('cover_letter')
        
        if new_status:
            job.status = new_status
            
            if new_status == 'Applied':
                if cover_letter:
                    if job.application:
                        job.application.cover_letter = cover_letter
                        job.application.applied_date = datetime.utcnow()
                    else:
                        application = Application(
                            job_id=job.id,
                            cover_letter=cover_letter,
                            applied_date=datetime.utcnow(),
                            email_sent=False
                        )
                        db.session.add(application)
                
                job.applied_date = datetime.utcnow()
            
            today = datetime.utcnow().date()
            stats = Stats.query.filter_by(date=today).first()
            if not stats:
                stats = Stats(date=today, jobs_found=0)
                db.session.add(stats)
            
            if new_status == 'Applied':
                stats.jobs_applied += 1
            elif new_status == 'Interview':
                stats.interviews_scheduled += 1
            elif new_status == 'Rejected':
                stats.rejections_received += 1
            elif new_status == 'Offer':
                stats.offers_received += 1
            
            db.session.commit()
            
            if new_status == 'Applied':
                send_telegram_notification(
                    f"Application Sent\n\n"
                    f"Job: {job.title}\n"
                    f"Company: {job.company}\n"
                    f"URL: {job.url}"
                )
            
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        
        return jsonify({'success': False, 'error': 'No status provided'}), 400
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error updating job status: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main.route('/api/job/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job"""
    try:
        job = Job.query.get_or_404(job_id)
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


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
                cover_letter = generate_cover_letter(job.title, job.company, job.description or '')
                
                application = Application(
                    job_id=job.id,
                    cover_letter=cover_letter,
                    applied_date=datetime.utcnow(),
                    email_sent=False
                )
                
                job.status = 'Applied'
                job.applied_date = datetime.utcnow()
                
                db.session.add(application)
                applied += 1
        
        except Exception as e:
            errors.append(f"Job {job_id}: {str(e)}")
    
    try:
        db.session.commit()
        
        today = datetime.utcnow().date()
        stats = Stats.query.filter_by(date=today).first()
        if not stats:
            stats = Stats(date=today, jobs_found=0)
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