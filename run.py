"""
JobHunterPro - Professional Job Application Automation Platform
Main entry point for the application
"""

from app import create_app
from app.models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
        print("Job Hunter is starting...")
        print("Dashboard: http://localhost:5000")
        print("Ready to hunt jobs!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)