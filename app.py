#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
from jobspy_enhanced import scrape_jobs
import pandas as pd
import os
from datetime import datetime
import json

app = Flask(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def scrape_multiple_companies(companies, location, hours_old, results_wanted):
    """Scrape jobs for multiple companies and combine results"""
    all_jobs = []
    
    for i, company in enumerate(companies, 1):
        try:
            jobs = scrape_jobs(
                site_name=['indeed'],
                indeed_company_id=company,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                verbose=0  # Reduce console output for web
            )
            
            # Add company info to track which company each job came from
            jobs['search_company'] = company
            all_jobs.append(jobs)
            
        except Exception as e:
            print(f"Error scraping {company}: {e}")
            continue
    
    # Combine all results
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        return combined_jobs
    else:
        return pd.DataFrame()

def analyze_duplicates(jobs_df):
    """Analyze duplicates without removing them"""
    url_duplicates = jobs_df[jobs_df.duplicated(subset=['job_url_direct'], keep=False)]
    title_location_duplicates = jobs_df[jobs_df.duplicated(subset=['title', 'location'], keep=False)]
    
    return {
        'url_duplicates': len(url_duplicates),
        'title_location_duplicates': len(title_location_duplicates),
        'total_duplicates': len(url_duplicates) + len(title_location_duplicates),
        'duplicate_rate': (len(url_duplicates) + len(title_location_duplicates)) / len(jobs_df) * 100 if len(jobs_df) > 0 else 0
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        # Get form data
        companies_input = request.form.get('companies', '').strip()
        companies = [company.strip() for company in companies_input.split(',') if company.strip()]
        
        if not companies:
            return jsonify({'error': 'No companies entered'})
        
        location = request.form.get('location', '').strip()
        if not location:
            return jsonify({'error': 'Location is required'})
        
        hours_old = request.form.get('hours_old', '').strip()
        hours_old = int(hours_old) if hours_old else None
        
        results_wanted = request.form.get('results_wanted', '1000').strip()
        results_wanted = int(results_wanted) if results_wanted else 1000
        
        # Scrape jobs
        combined_jobs = scrape_multiple_companies(companies, location, hours_old, results_wanted)
        
        if len(combined_jobs) == 0:
            return jsonify({'error': 'No jobs found for any company'})
        
        # Analyze duplicates
        duplicate_analysis = analyze_duplicates(combined_jobs)
        
        # Prepare results for display
        results = {
            'total_jobs': len(combined_jobs),
            'companies': companies,
            'location': location,
            'hours_old': hours_old,
            'results_wanted': results_wanted,
            'duplicate_analysis': duplicate_analysis,
            'company_breakdown': combined_jobs['search_company'].value_counts().to_dict(),
            'location_breakdown': combined_jobs['location'].value_counts().head(10).to_dict(),
            'sample_jobs': combined_jobs[['title', 'company', 'location', 'search_company', 'date_posted']].head(10).to_dict('records')
        }
        
        # Save to CSV if requested
        if request.form.get('export_csv') == 'true':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            companies_str = '_'.join([c.lower() for c in companies])
            filename = f"{companies_str}_{location.lower().replace(', ', '_').replace(' ', '_')}_{timestamp}.csv"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            combined_jobs.to_csv(filepath, index=False)
            results['csv_file'] = filename
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

@app.route('/download/<filename>')
def download(filename):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)
    except:
        return jsonify({'error': 'File not found'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 