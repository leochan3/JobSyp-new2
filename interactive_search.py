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

def scrape_multiple_companies(companies, location, hours_old, results_wanted):
    """Scrape jobs for multiple companies and combine results"""
    all_jobs = []
    
    for i, company in enumerate(companies, 1):
        print(f"\n🔍 [{i}/{len(companies)}] Scraping {company} jobs in {location}...")
        if hours_old:
            print(f"   Time filter: Last {hours_old} hours")
        else:
            print("   Time filter: All time")
        
        try:
            jobs = scrape_jobs(
                site_name=['indeed'],
                indeed_company_id=company,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                verbose=1
            )
            
            # Add company info to track which company each job came from
            jobs['search_company'] = company
            
            print(f"   ✅ Found {len(jobs)} {company} jobs")
            
            # Check company accuracy
            company_jobs = jobs[jobs['company'].str.contains(company, case=False, na=False)]
            accuracy = len(company_jobs) / len(jobs) * 100 if len(jobs) > 0 else 0
            print(f"   📊 Accuracy: {accuracy:.1f}%")
            
            all_jobs.append(jobs)
            
        except Exception as e:
            print(f"   ❌ Error scraping {company}: {e}")
            continue
    
    # Combine all results
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        print(f"\n🎯 COMBINED RESULTS:")
        print(f"Total jobs from all companies: {len(combined_jobs)}")
        
        # Show breakdown by company
        print(f"\n📊 Jobs by company:")
        company_counts = combined_jobs['search_company'].value_counts()
        for company, count in company_counts.items():
            print(f"   {company}: {count} jobs")
        
        return combined_jobs
    else:
        print("❌ No jobs found for any company")
        return pd.DataFrame()

def main():
    print("🚀 Enhanced JobSpy Multi-Company Interactive Scraper")
    print("=" * 60)
    
    # Get user input
    companies_input = input("Enter company names (separate with commas, e.g., Amazon, Walmart, Lyft): ").strip()
    companies = [company.strip() for company in companies_input.split(',') if company.strip()]
    
    if not companies:
        print("❌ No companies entered. Exiting.")
        return
    
    location = input("Enter location (e.g., Seattle, WA, United States): ").strip()
    
    hours_old_input = input("Enter hours old (press Enter for all time): ").strip()
    hours_old = int(hours_old_input) if hours_old_input else None
    
    results_wanted_input = input("Enter number of results per company (press Enter for 1000): ").strip()
    results_wanted = int(results_wanted_input) if results_wanted_input else 1000
    
    print(f"\n🎯 SEARCH SUMMARY:")
    print(f"Companies: {', '.join(companies)}")
    print(f"Location: {location}")
    print(f"Results per company: {results_wanted}")
    if hours_old:
        print(f"Time filter: Last {hours_old} hours")
    else:
        print("Time filter: All time")
    
    # Scrape all companies
    combined_jobs = scrape_multiple_companies(companies, location, hours_old, results_wanted)
    
    if len(combined_jobs) > 0:
        # Show location breakdown
        print(f"\n📍 Location breakdown:")
        print(combined_jobs['location'].value_counts().head())
        
        # Analyze duplicates
        analyze_duplicates(combined_jobs)
        
        # Ask user if they want to export
        export_choice = input(f"\n💾 Do you want to export the combined data to CSV? (y/n): ").strip().lower()
        
        if export_choice in ['y', 'yes']:
            # Create unique filename with timestamp
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            companies_str = '_'.join([c.lower() for c in companies])
            filename = f"{companies_str}_{location.lower().replace(', ', '_').replace(' ', '_')}_{timestamp}.csv"
            
            combined_jobs.to_csv(filename, index=False)
            print(f"\n✅ Combined file exported: {filename}")
            print(f"   File size: {len(combined_jobs)} jobs, {len(combined_jobs.columns)} columns")
            print(f"   Companies included: {', '.join(companies)}")
        else:
            print("\n📝 Data not exported. You can run the script again to export later.")
        
        # Show sample of combined jobs
        print(f"\n🎯 Sample of combined jobs:")
        print(combined_jobs[['title', 'company', 'location', 'search_company', 'date_posted']].head())
        
    else:
        print("\n❌ No jobs found. Please check your inputs and try again.")

if __name__ == "__main__":
    main() 