#!/usr/bin/env python3
"""
Simple installation script for JobSpy Enhanced
This script installs the enhanced version without conflicts
"""

import os
import sys
import subprocess
import shutil

def install_enhanced():
    print("🚀 Installing JobSpy Enhanced...")
    
    # Check if jobspy_enhanced directory exists
    if not os.path.exists('jobspy_enhanced'):
        print("❌ jobspy_enhanced directory not found!")
        return False
    
    # Install using pip
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'])
        print("✅ JobSpy Enhanced installed successfully!")
        print("\n📖 Usage:")
        print("from jobspy_enhanced import scrape_jobs")
        print("\n🎯 Example:")
        print("jobs = scrape_jobs(")
        print("    site_name=['indeed'],")
        print("    indeed_company_id='Amazon',")
        print("    location='Seattle, WA',")
        print("    results_wanted=1000,")
        print("    verbose=1")
        print(")")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

if __name__ == "__main__":
    install_enhanced() 