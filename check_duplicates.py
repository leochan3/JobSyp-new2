#!/usr/bin/env python3
import pandas as pd

# Load the CSV file
df = pd.read_csv('uber_jobs.csv')

print('=== DUPLICATION ANALYSIS ===')
print(f'Total rows: {len(df)}')
print()

# 1. Check duplicates in job_url_direct (Column D)
print('1. Duplicates in job_url_direct (Column D):')
direct_dups = df['job_url_direct'].duplicated().sum()
unique_direct = df['job_url_direct'].nunique()
print(f'   Duplicate rows: {direct_dups}')
print(f'   Unique values: {unique_direct}')
print(f'   Duplication rate: {direct_dups/len(df)*100:.1f}%')

# Show some examples of duplicates
if direct_dups > 0:
    print('   Examples of duplicate job_url_direct:')
    duplicates = df[df['job_url_direct'].duplicated(keep=False)].sort_values('job_url_direct')
    for url in duplicates['job_url_direct'].unique():
        if pd.notna(url):
            dup_rows = duplicates[duplicates['job_url_direct'] == url]
            print(f'     URL: {url[:50]}...')
            print(f'     Count: {len(dup_rows)}')
            titles = list(dup_rows['title'].head(2))
            print(f'     Titles: {titles}')
            print()

print()

# 2. Check duplicates in title + location (Columns E + G)
print('2. Duplicates in title + location (Columns E + G):')
title_loc_dups = df.duplicated(subset=['title', 'location']).sum()
unique_combinations = df[['title', 'location']].drop_duplicates().shape[0]
print(f'   Duplicate rows: {title_loc_dups}')
print(f'   Unique combinations: {unique_combinations}')
print(f'   Duplication rate: {title_loc_dups/len(df)*100:.1f}%')

# Show some examples of duplicates
if title_loc_dups > 0:
    print('   Examples of duplicate title + location:')
    duplicates = df[df.duplicated(subset=['title', 'location'], keep=False)].sort_values(['title', 'location'])
    for _, group in duplicates.groupby(['title', 'location']):
        if len(group) > 1:
            print(f'     Title: {group.iloc[0]["title"][:50]}...')
            print(f'     Location: {group.iloc[0]["location"]}')
            print(f'     Count: {len(group)}')
            urls = list(group["job_url"].head(2))
            print(f'     Job URLs: {urls}')
            print()

print()

# 3. Additional analysis
print('3. Additional Analysis:')
print(f'   Total unique titles: {df["title"].nunique()}')
print(f'   Total unique locations: {df["location"].nunique()}')
print(f'   Jobs with salary info: {df["min_amount"].notna().sum()}')

# Check for exact duplicates across all columns
exact_dups = df.duplicated().sum()
print(f'   Exact duplicates (all columns): {exact_dups}')

print()
print('=== SUMMARY ===')
if direct_dups == 0 and title_loc_dups == 0:
    print('✅ No duplications found!')
else:
    print('⚠️  Some duplications detected:')
    if direct_dups > 0:
        print(f'   - {direct_dups} duplicate job_url_direct entries')
    if title_loc_dups > 0:
        print(f'   - {title_loc_dups} duplicate title+location combinations') 