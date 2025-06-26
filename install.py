#!/usr/bin/env python3
"""
Simple installation script for JobSpy Enhanced
Run this script to install the enhanced version with company-specific scraping
"""

import subprocess
import sys
import os

def install_enhanced_jobspy():
    """Install the enhanced JobSpy from GitHub"""
    print("🚀 Installing JobSpy Enhanced...")
    
    try:
        # Install from GitHub
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "git+https://github.com/leochan3/JobSyp-new2.git"
        ])
        
        print("✅ JobSpy Enhanced installed successfully!")
        print("\n📖 Usage example:")
        print("""
from jobspy import scrape_jobs

# Company-specific scraping (100% accuracy!)
uber_jobs = scrape_jobs(
    site_name=["indeed"],
    indeed_company_id="Uber",
    results_wanted=1000
)

print(f"Found {len(uber_jobs)} Uber jobs!")
        """)
        
        print("🔗 Documentation: https://github.com/leochan3/JobSyp-new2")
        print("📋 Company scraping guide: https://github.com/leochan3/JobSyp-new2/blob/main/COMPANY_SCRAPING_GUIDE.md")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print("\n💡 Alternative installation methods:")
        print("1. Clone the repository:")
        print("   git clone https://github.com/leochan3/JobSyp-new2.git")
        print("   cd JobSyp-new2")
        print("   pip install -e .")
        print("\n2. Or install manually:")
        print("   pip install git+https://github.com/leochan3/JobSyp-new2.git")

if __name__ == "__main__":
    install_enhanced_jobspy() 