#!/opt/anaconda3/bin/python
from jobspy_enhanced import scrape_jobs
import pandas as pd

def analyze_duplicates(jobs_df):
    """Analyze duplicates without removing them"""
    print("\n🔍 DUPLICATE ANALYSIS:")
    
    # Check 1: Same job_url_direct
    url_duplicates = jobs_df[jobs_df.duplicated(subset=['job_url_direct'], keep=False)]
    print(f"📋 Duplicates by job_url_direct: {len(url_duplicates)} jobs")
    
    if len(url_duplicates) > 0:
        print("   Sample duplicate URLs:")
        for url in url_duplicates['job_url_direct'].unique()[:3]:
            print(f"   - {url}")
    
    # Check 2: Same title + same location
    title_location_duplicates = jobs_df[jobs_df.duplicated(subset=['title', 'location'], keep=False)]
    print(f"📋 Duplicates by title + location: {len(title_location_duplicates)} jobs")
    
    if len(title_location_duplicates) > 0:
        print("   Sample duplicate title+location combinations:")
        duplicates_grouped = title_location_duplicates.groupby(['title', 'location']).size()
        for (title, location), count in duplicates_grouped.head(3).items():
            print(f"   - '{title}' in {location} ({count} times)")
    
    # Show summary statistics
    total_duplicates = len(url_duplicates) + len(title_location_duplicates)
    print(f"\n📊 SUMMARY:")
    print(f"   Total jobs with duplicates: {total_duplicates}")
    print(f"   Duplicate rate: {total_duplicates/len(jobs_df)*100:.1f}%" if len(jobs_df) > 0 else "   No jobs found")

def main():
    print("🚀 Enhanced JobSpy Interactive Scraper")
    print("=" * 50)
    
    # Get user input
    company = input("Enter company name (e.g., Amazon, Walmart, Lyft): ").strip()
    location = input("Enter location (e.g., Seattle, WA, United States): ").strip()
    
    hours_old_input = input("Enter hours old (press Enter for all time): ").strip()
    hours_old = int(hours_old_input) if hours_old_input else None
    
    results_wanted_input = input("Enter number of results wanted (press Enter for 1000): ").strip()
    results_wanted = int(results_wanted_input) if results_wanted_input else 1000
    
    print(f"\n🔍 Scraping {company} jobs in {location}...")
    if hours_old:
        print(f"   Time filter: Last {hours_old} hours")
    else:
        print("   Time filter: All time")
    
    # Scrape jobs
    try:
        jobs = scrape_jobs(
            site_name=['indeed'],
            indeed_company_id=company,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            verbose=1
        )
        
        print(f"\n📊 RESULTS:")
        print(f"Total jobs found: {len(jobs)}")
        
        # Check company accuracy
        company_jobs = jobs[jobs['company'].str.contains(company, case=False, na=False)]
        accuracy = len(company_jobs) / len(jobs) * 100 if len(jobs) > 0 else 0
        print(f"Company accuracy: {accuracy:.1f}%")
        
        # Show location breakdown
        print(f"\n📍 Location breakdown:")
        print(jobs['location'].value_counts().head())
        
        # Analyze duplicates (without removing)
        analyze_duplicates(jobs)
        
        # Ask user if they want to export
        export_choice = input(f"\n💾 Do you want to export the data to CSV? (y/n): ").strip().lower()
        
        if export_choice in ['y', 'yes']:
            # Create unique filename with timestamp
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company.lower()}_{location.lower().replace(', ', '_').replace(' ', '_')}_{timestamp}.csv"
            
            jobs.to_csv(filename, index=False)
            print(f"\n✅ File exported: {filename}")
            print(f"   File size: {len(jobs)} jobs, {len(jobs.columns)} columns")
        else:
            print("\n📝 Data not exported. You can run the script again to export later.")
        
        # Show sample of jobs
        print(f"\n🎯 Sample of jobs:")
        print(jobs[['title', 'location', 'date_posted']].head())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your inputs and try again.")

if __name__ == "__main__":
    main() 