#!/usr/bin/env python3
"""
Test script for JobSpy Enhanced
"""

def test_import():
    try:
        from jobspy_enhanced import scrape_jobs
        print("✅ Import successful!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    try:
        from jobspy_enhanced import scrape_jobs
        
        print("🧪 Testing basic functionality...")
        jobs = scrape_jobs(
            site_name=['indeed'],
            indeed_company_id='Amazon',
            location='Seattle, WA',
            results_wanted=5,
            verbose=1
        )
        
        print(f"✅ Found {len(jobs)} jobs")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing JobSpy Enhanced...")
    
    if test_import():
        test_basic_functionality()
    else:
        print("\n💡 Try running: python install_enhanced.py") 