#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from jobspy_enhanced import scrape_jobs
from datetime import datetime
import os
from fuzzywuzzy import fuzz, process
import openai

# Page configuration
st.set_page_config(
    page_title="JobSpy Enhanced - Job Scraper",
    page_icon="🚀",
    layout="wide"
)

# Create uploads directory
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def create_job_synonyms():
    """Create a mapping of job title synonyms and related terms"""
    synonyms = {
        # Product/Program Management
        'product manager': ['product manager', 'program manager', 'product owner', 'pm'],
        'program manager': ['program manager', 'product manager', 'project manager', 'pm'],
        'project manager': ['project manager', 'program manager', 'product manager', 'pm'],
        
        # Software Engineering
        'software engineer': ['software engineer', 'developer', 'programmer', 'software developer', 'engineer'],
        'developer': ['developer', 'software engineer', 'programmer', 'software developer', 'engineer'],
        'programmer': ['programmer', 'developer', 'software engineer', 'software developer'],
        'engineer': ['engineer', 'software engineer', 'developer', 'programmer'],
        
        # Data roles
        'data scientist': ['data scientist', 'data analyst', 'analytics', 'data engineer'],
        'data analyst': ['data analyst', 'data scientist', 'analytics', 'business analyst'],
        'data engineer': ['data engineer', 'data scientist', 'analytics engineer'],
        
        # Design roles
        'designer': ['designer', 'ux designer', 'ui designer', 'product designer', 'graphic designer'],
        'ux designer': ['ux designer', 'ui designer', 'product designer', 'designer'],
        'ui designer': ['ui designer', 'ux designer', 'product designer', 'designer'],
        
        # Marketing roles
        'marketing manager': ['marketing manager', 'marketing', 'digital marketing', 'marketing specialist'],
        'marketing': ['marketing', 'marketing manager', 'digital marketing', 'marketing specialist'],
        
        # Sales roles
        'sales': ['sales', 'account manager', 'sales manager', 'sales representative'],
        'account manager': ['account manager', 'sales', 'sales manager', 'customer success'],
        
        # Operations roles
        'operations': ['operations', 'ops', 'operations manager', 'business operations'],
        'ops': ['ops', 'operations', 'operations manager', 'business operations'],
        
        # Finance roles
        'analyst': ['analyst', 'financial analyst', 'business analyst', 'data analyst'],
        'financial analyst': ['financial analyst', 'analyst', 'finance', 'business analyst'],
        
        # HR roles
        'hr': ['hr', 'human resources', 'recruiter', 'talent acquisition'],
        'recruiter': ['recruiter', 'hr', 'human resources', 'talent acquisition'],
        
        # Customer roles
        'customer success': ['customer success', 'account manager', 'customer support'],
        'customer support': ['customer support', 'customer success', 'support'],
    }
    return synonyms

def smart_job_search(jobs_df, search_query, threshold=60):
    """
    Smart job search using fuzzy matching and synonyms
    Returns jobs that match the search query with relevance scoring
    """
    if not search_query or search_query.strip() == "":
        return jobs_df
    
    search_query = search_query.lower().strip()
    search_words = search_query.split()
    
    # Simple but effective approach: filter jobs that contain the search terms
    filtered_jobs = []
    
    for idx, job in jobs_df.iterrows():
        job_title = str(job['title']).lower()
        
        # For exact phrase search
        if search_query in job_title:
            filtered_jobs.append(job)
        # For multi-word search, require ALL words to be present
        elif len(search_words) > 1 and all(word in job_title for word in search_words):
            filtered_jobs.append(job)
        # For single word search
        elif len(search_words) == 1 and search_words[0] in job_title:
            filtered_jobs.append(job)
    
    # Return filtered dataframe
    if filtered_jobs:
        return pd.DataFrame(filtered_jobs).reset_index(drop=True)
    else:
        return pd.DataFrame(columns=jobs_df.columns)

def ai_filter_jobs(jobs_df, user_target, min_score=50):
    """
    AI-powered job filtering with matching scores (0-100) using OpenAI GPT-4.1-nano
    Analyzes job titles, descriptions, company, and location for comprehensive relevance scoring
    """
    if not user_target or user_target.strip() == "":
        return jobs_df
    
    import openai
    import re
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = "gpt-4.1-nano"
    scored_jobs = []
    
    # Live log placeholder
    log_placeholder = st.empty()
    log_lines = ["🤖 AI is analyzing job titles and descriptions with matching scores..."]
    
    with st.spinner("🤖 AI is analyzing job titles and descriptions for relevance..."):
        for idx, job in jobs_df.iterrows():
            job_title = str(job['title'])
            company = str(job.get('company', 'Unknown'))
            location = str(job.get('location', 'Unknown'))
            job_description = str(job.get('description', ''))
            
            # Truncate description if too long (to avoid token limits)
            if len(job_description) > 2000:
                job_description = job_description[:2000] + "..."
            
            # Enhanced prompt for comprehensive scoring
            prompt = f"""
You are an expert job matching AI. Analyze this job comprehensively for relevance to the user's interests.

USER INTEREST: {user_target}

JOB INFORMATION:
- Title: {job_title}
- Company: {company}
- Location: {location}
- Description: {job_description}

Analyze the job description for:
1. Required skills and technologies
2. Job responsibilities and duties
3. Experience level and qualifications
4. Industry and domain focus
5. Team and role context

Provide a detailed analysis and score this job's relevance from 0-100, where:
- 0-20: Completely irrelevant (e.g., retail manager for data scientist)
- 21-40: Slightly relevant (e.g., business analyst for data scientist)
- 41-60: Moderately relevant (e.g., data analyst for data scientist)
- 61-80: Highly relevant (e.g., ML engineer for data scientist)
- 81-100: Perfect match (e.g., data scientist for data scientist)

Consider both the job title AND the detailed description content.

Respond in this exact format:
SCORE: [0-100]
CONFIDENCE: [HIGH/MEDIUM/LOW]
REASONING: [2-3 sentences explaining the score based on title and description analysis]

Example:
SCORE: 85
CONFIDENCE: HIGH
REASONING: This is a direct match for data science role. The title "Senior Data Scientist" and description mentioning "machine learning, Python, statistical analysis" directly align with the user's interest in data science positions.
"""
            
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.1
                )
                ai_response = response.choices[0].message.content.strip()
                
                # Parse the structured response
                score_match = re.search(r'SCORE:\s*(\d+)', ai_response)
                confidence_match = re.search(r'CONFIDENCE:\s*(HIGH|MEDIUM|LOW)', ai_response)
                reasoning_match = re.search(r'REASONING:\s*(.+)', ai_response, re.DOTALL)
                
                if score_match and confidence_match and reasoning_match:
                    score = int(score_match.group(1))
                    confidence = confidence_match.group(1)
                    reasoning = reasoning_match.group(1).strip()
                    
                    # Add score and metadata to job
                    job_with_score = job.copy()
                    job_with_score['ai_score'] = score
                    job_with_score['ai_confidence'] = confidence
                    job_with_score['ai_reasoning'] = reasoning
                    
                    # Color coding based on score
                    if score >= 80:
                        color = "limegreen"
                        status = "PERFECT MATCH"
                    elif score >= 60:
                        color = "green"
                        status = "HIGHLY RELEVANT"
                    elif score >= 40:
                        color = "orange"
                        status = "MODERATELY RELEVANT"
                    elif score >= 20:
                        color = "yellow"
                        status = "SLIGHTLY RELEVANT"
                    else:
                        color = "#ff6666"
                        status = "NOT RELEVANT"
                    
                    log_lines.append(f"<span style='color:{color}'><b>{job_title}</b> — Score: <b>{score}/100</b> ({status})<br>Confidence: {confidence} | {reasoning}</span>")
                    
                    # Only keep jobs above minimum score
                    if score >= min_score:
                        scored_jobs.append(job_with_score)
                else:
                    # Fallback parsing if structured format fails
                    log_lines.append(f"<span style='color:orange'>Job: <b>{job_title}</b> — AI parsing error, using fallback</span>")
                    # Try to extract any number as score
                    number_match = re.search(r'(\d+)', ai_response)
                    if number_match:
                        score = min(100, max(0, int(number_match.group(1))))
                        job_with_score = job.copy()
                        job_with_score['ai_score'] = score
                        job_with_score['ai_confidence'] = 'LOW'
                        job_with_score['ai_reasoning'] = 'Fallback parsing used'
                        if score >= min_score:
                            scored_jobs.append(job_with_score)
                            
            except Exception as e:
                log_lines.append(f"<span style='color:orange'>Job: <b>{job_title}</b> — AI error: {str(e)[:50]}...</span>")
                continue
            
            # Update the log live
            log_placeholder.markdown("<br>".join(log_lines), unsafe_allow_html=True)
    
    # Final log update
    log_placeholder.markdown("<br>".join(log_lines), unsafe_allow_html=True)
    
    if scored_jobs:
        # Sort by score (highest first)
        scored_df = pd.DataFrame(scored_jobs)
        scored_df = scored_df.sort_values('ai_score', ascending=False).reset_index(drop=True)
        
        # Show summary statistics
        avg_score = scored_df['ai_score'].mean()
        high_score_count = len(scored_df[scored_df['ai_score'] >= 80])
        st.success(f"🎯 AI Analysis Complete: {len(scored_df)} jobs kept (avg score: {avg_score:.1f}/100, {high_score_count} perfect matches)")
        
        return scored_df
    else:
        return pd.DataFrame(columns=jobs_df.columns)

def get_related_terms(keyword):
    """
    Simple related terms mapping for demo
    In production, this would use more sophisticated AI/NLP
    """
    related_map = {
        'data': ['analyst', 'science', 'scientist', 'analytics', 'engineer'],
        'software': ['developer', 'engineer', 'programming', 'coding', 'development'],
        'product': ['manager', 'management', 'owner', 'lead'],
        'machine': ['learning', 'ml', 'ai', 'artificial'],
        'python': ['programming', 'developer', 'engineer', 'coding'],
        'marketing': ['digital', 'growth', 'brand', 'campaign'],
        'sales': ['business', 'development', 'account', 'revenue'],
        'design': ['ui', 'ux', 'graphic', 'visual', 'creative'],
        'finance': ['financial', 'accounting', 'analyst', 'investment'],
        'operations': ['ops', 'operational', 'logistics', 'supply']
    }
    
    return related_map.get(keyword, [])

def scrape_multiple_companies(companies, location, hours_old, results_wanted):
    """Scrape jobs for multiple companies with smart time-based splitting for high-volume companies"""
    all_jobs = []
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, company in enumerate(companies):
        status_text.text(f"Scraping {company}... ({i+1}/{len(companies)})")
        
        try:
            # First, try a regular search to detect if company has many jobs
            initial_jobs = scrape_jobs(
                site_name=['indeed'],
                indeed_company_id=company,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                verbose=0
            )
            
            # If we got close to 1000 jobs, this company likely has more jobs available
            # Use time-based splitting to get comprehensive results
            if len(initial_jobs) >= 950:  # Close to 1000 indicates more jobs available
                st.info(f"🔄 {company} has many jobs ({len(initial_jobs)}), using time-based search for comprehensive results...")
                
                # Time-based splitting with 24-hour windows up to 2 weeks
                time_ranges = [
                    (None, 24, "Last 24 hours"),
                    (24, 48, "24-48 hours"),
                    (48, 72, "48-72 hours"),
                    (72, 96, "72-96 hours"),
                    (96, 120, "96-120 hours"),
                    (120, 144, "120-144 hours"),
                    (144, 168, "144-168 hours"),
                    (168, 192, "168-192 hours"),
                    (192, 216, "192-216 hours"),
                    (216, 240, "216-240 hours"),
                    (240, 264, "240-264 hours"),
                    (264, 288, "264-288 hours"),
                    (288, 312, "288-312 hours"),
                    (312, 336, "312-336 hours (2 weeks)"),
                    (336, None, "Older than 2 weeks")
                ]
                
                company_jobs = []
                # Create a compact progress display
                progress_placeholder = st.empty()
                detailed_progress = st.expander(f"📊 Detailed Progress for {company}", expanded=False)
                
                completed_ranges = 0
                total_ranges = len(time_ranges)
                
                for start_hours, end_hours, range_name in time_ranges:
                    try:
                        # Update compact progress
                        progress_placeholder.text(f"⏳ Searching {range_name}... ({completed_ranges + 1}/{total_ranges})")
                        
                        range_jobs = scrape_jobs(
                            site_name=['indeed'],
                            indeed_company_id=company,
                            location=location,
                            results_wanted=results_wanted,
                            hours_old=end_hours,
                            verbose=0
                        )
                        if len(range_jobs) > 0:
                            range_jobs['time_range'] = range_name
                            company_jobs.append(range_jobs)
                            # Show detailed progress in expander
                            with detailed_progress:
                                st.write(f"  📅 {range_name}: {len(range_jobs)} jobs")
                        else:
                            with detailed_progress:
                                st.write(f"  📅 {range_name}: 0 jobs")
                                
                        completed_ranges += 1
                        
                    except Exception as e:
                        with detailed_progress:
                            st.warning(f"  ⚠️ Error in {range_name}: {e}")
                        completed_ranges += 1
                        continue
                
                # Clear the progress text
                progress_placeholder.empty()
                
                if company_jobs:
                    # Combine and deduplicate
                    combined_company_jobs = pd.concat(company_jobs, ignore_index=True)
                    # Remove duplicates within this company's results
                    combined_company_jobs = combined_company_jobs.drop_duplicates(subset=['job_url', 'title'], keep='first')
                    combined_company_jobs['search_company'] = company
                    
                    total_jobs = len(combined_company_jobs)
                    st.success(f"✅ {company}: {total_jobs} jobs (time-based search)")
                    all_jobs.append(combined_company_jobs)
                else:
                    # Fallback to initial results if time-based search failed
                    initial_jobs['search_company'] = company
                    company_jobs = initial_jobs[initial_jobs['company'].str.contains(company, case=False, na=False)]
                    accuracy = len(company_jobs) / len(initial_jobs) * 100 if len(initial_jobs) > 0 else 0
                    st.success(f"✅ {company}: {len(initial_jobs)} jobs (fallback, Accuracy: {accuracy:.1f}%)")
                    all_jobs.append(initial_jobs)
            else:
                # Company has fewer jobs, use the simple single search result
                initial_jobs['search_company'] = company
                company_jobs = initial_jobs[initial_jobs['company'].str.contains(company, case=False, na=False)]
                accuracy = len(company_jobs) / len(initial_jobs) * 100 if len(initial_jobs) > 0 else 0
                st.success(f"✅ {company}: {len(initial_jobs)} jobs (simple search, Accuracy: {accuracy:.1f}%)")
                all_jobs.append(initial_jobs)
                
        except Exception as e:
            st.error(f"❌ Error scraping {company}: {e}")
            continue
        
        progress_bar.progress((i + 1) / len(companies))
    
    progress_bar.empty()
    status_text.empty()
    
    # Combine all results
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
        
        # Remove duplicates across all companies
        total_before_dedup = len(combined_jobs)
        combined_jobs = combined_jobs.drop_duplicates(subset=['job_url', 'title'], keep='first')
        total_after_dedup = len(combined_jobs)
        duplicates_removed = total_before_dedup - total_after_dedup
        
        # Show compact summary
        if duplicates_removed > 0:
            st.success(f"✅ **{total_after_dedup} unique jobs found** ({duplicates_removed} duplicates removed from {total_before_dedup} total)")
        else:
            st.success(f"✅ **{total_after_dedup} unique jobs found** (no duplicates)")
        
        # Sort by date posted (newest first)
        combined_jobs['date_posted'] = pd.to_datetime(combined_jobs['date_posted'], errors='coerce')
        combined_jobs = combined_jobs.sort_values('date_posted', ascending=False)
        
        return combined_jobs
    else:
        return pd.DataFrame()

def format_salary(row):
    """Format salary information from multiple columns"""
    if pd.notna(row.get('min_amount')) and pd.notna(row.get('max_amount')):
        return f"&#36;{row['min_amount']:,.0f} - &#36;{row['max_amount']:,.0f}"
    elif pd.notna(row.get('min_amount')):
        return f"&#36;{row['min_amount']:,.0f}+"
    elif pd.notna(row.get('max_amount')):
        return f"Up to &#36;{row['max_amount']:,.0f}"
    else:
        return "Not specified"

def truncate_title(title, max_length=60):
    """Truncate job title if too long"""
    if len(title) > max_length:
        return title[:max_length] + "..."
    return title

def display_job_data_table(jobs_df, jobs_per_page=15):
    total_jobs = len(jobs_df)
    
    # Initialize session state for current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Initialize selected job state
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    
    # Initialize sorting state
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = 'date_posted'
    if 'sort_ascending' not in st.session_state:
        st.session_state.sort_ascending = False
    
    # Check if we need to scroll to top (for bottom pagination)
    if 'scroll_to_top' not in st.session_state:
        st.session_state.scroll_to_top = False
    
    # Create two columns: main table and job details sidebar
    main_col, detail_col = st.columns([3, 1])
    
    with main_col:
        # Filters section
        st.markdown("### 🔍 Filters & Sorting")
        
        # Add search bar at the top
        search_query = st.text_input(
            "🔍 Search Job Titles", 
            placeholder="e.g., product manager, software engineer, data scientist",
            help="Smart search with synonyms (e.g., 'developer' finds 'engineer' jobs)",
            key="job_title_search"
        )
        
        # Add AI-powered job filtering
        ai_target = st.text_input(
            "🤖 AI Job Filter (Enhanced)", 
            placeholder="e.g., I want data science roles with Python and machine learning",
            help="Describe your ideal job - AI will analyze job titles AND descriptions to filter and rank jobs based on relevance to your target",
            key="ai_target_input"
        )
        
        # AI Filter controls
        if ai_target and ai_target.strip():
            ai_col1, ai_col2, ai_col3, ai_col4 = st.columns([1, 1, 2, 2])
            with ai_col1:
                if st.button("🤖 Apply AI Filter", key="apply_ai_filter"):
                    st.session_state.ai_filter_applied = True
                    st.session_state.ai_target = ai_target.strip()
                    st.rerun()
            with ai_col2:
                if st.button("Clear AI Filter", key="clear_ai_filter"):
                    st.session_state.ai_filter_applied = False
                    st.session_state.ai_target = ""
                    st.rerun()
            with ai_col3:
                min_score = st.slider(
                    "Minimum Score", 
                    min_value=0, 
                    max_value=100, 
                    value=50, 
                    step=5,
                    help="Only show jobs with AI relevance score above this threshold (0-100)"
                )
            with ai_col4:
                st.markdown(f"**Score Guide:**")
                st.markdown("• 80-100: Perfect match")
                st.markdown("• 60-79: Highly relevant") 
                st.markdown("• 40-59: Moderately relevant")
                st.markdown("• 20-39: Slightly relevant")
                st.markdown("• 0-19: Not relevant")
        
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        
        # Use a reset flag for all filters
        reset_filters = st.session_state.get('clear_filters_flag', False)

        with filter_col1:
            # Handle NaN values in company column
            company_values = jobs_df['company'].fillna('Unknown').unique().tolist()
            company_options = ['All'] + sorted([str(c) for c in company_values])
            selected_company = st.selectbox(
                "Company", company_options,
                index=0 if reset_filters else company_options.index(st.session_state.get('company_filter', 'All')),
                key="company_filter"
            )
        with filter_col2:
            # Handle NaN values in location column
            location_values = jobs_df['location'].fillna('Unknown').unique().tolist()
            location_options = ['All'] + sorted([str(l) for l in location_values])
            selected_location = st.selectbox(
                "Location", location_options,
                index=0 if reset_filters else location_options.index(st.session_state.get('location_filter', 'All')),
                key="location_filter"
            )
        with filter_col3:
            date_options = ['All', 'Last 7 days', 'Last 14 days', 'Last 30 days']
            selected_date = st.selectbox(
                "Date Posted", date_options,
                index=0 if reset_filters else date_options.index(st.session_state.get('date_filter', 'All')),
                key="date_filter"
            )
        with filter_col4:
            salary_options = ['All', 'Has Salary', 'No Salary Specified']
            selected_salary = st.selectbox(
                "Salary", salary_options,
                index=0 if reset_filters else salary_options.index(st.session_state.get('salary_filter', 'All')),
                key="salary_filter"
            )
        # Remove Clear Filters from filter_col5
        # with filter_col5:
        #     if st.button("Clear Filters", key="clear_filters"):
        #         st.session_state.clear_filters_flag = True
        #         st.rerun()
        # After widgets, clear the flag
        if reset_filters:
            st.session_state.clear_filters_flag = False
        # Place Clear Filters button below filters, left-aligned
        filter_action_col1, filter_action_col2, filter_action_col3 = st.columns([1, 1, 4])
        
        with filter_action_col1:
            if st.button("Clear Filters", key="clear_filters"):
                st.session_state.clear_filters_flag = True
                st.rerun()
        
        with filter_action_col2:
            # Prepare CSV data for download (before filtering for full dataset option)
            csv_data = jobs_df.copy()
            # Add formatted salary column for CSV
            csv_data['formatted_salary'] = csv_data.apply(format_salary, axis=1)
            # Format date for CSV
            csv_data['date_posted_formatted'] = pd.to_datetime(csv_data['date_posted']).dt.strftime('%Y-%m-%d')
            
            # Select relevant columns for CSV export
            csv_columns = ['title', 'company', 'location', 'date_posted_formatted', 'formatted_salary', 
                          'job_type', 'description', 'job_url_direct']
            csv_export = csv_data[csv_columns].copy()
            csv_export.columns = ['Job Title', 'Company', 'Location', 'Date Posted', 'Salary', 
                                 'Job Type', 'Description', 'Job URL']
            
            # Convert to CSV
            csv_string = csv_export.to_csv(index=False)
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_export_{timestamp}.csv"
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_string,
                file_name=filename,
                mime="text/csv",
                help="Download all jobs as CSV file"
            )
        
        # Apply filters
        filtered_df = jobs_df.copy()
        
        # Apply smart search first if query exists
        if search_query and search_query.strip():
            filtered_df = smart_job_search(filtered_df, search_query)
            if len(filtered_df) == 0:
                st.warning(f"No jobs found matching '{search_query}'. Try different keywords or check spelling.")
                return
        
        # AI filter caching logic
        ai_active = st.session_state.get('ai_filter_applied', False) and st.session_state.get('ai_target', '')
        ai_target = st.session_state.get('ai_target', '')
        ai_cache_key = f"ai_filtered_jobs_{hash(ai_target)}"

        # Reset AI cache if filter is cleared or target changes
        if not ai_active:
            st.session_state.pop('ai_filtered_jobs', None)
            st.session_state.pop('ai_cache_key', None)
        elif st.session_state.get('ai_cache_key', None) != ai_cache_key:
            st.session_state.pop('ai_filtered_jobs', None)

        # Use cached AI results if available
        if ai_active:
            if 'ai_filtered_jobs' in st.session_state:
                filtered_df = st.session_state['ai_filtered_jobs']
            else:
                with st.spinner("🤖 AI is analyzing job titles for relevance..."):
                    filtered_df = ai_filter_jobs(filtered_df, ai_target, min_score)
                    st.session_state['ai_filtered_jobs'] = filtered_df
                    st.session_state['ai_cache_key'] = ai_cache_key
                if len(filtered_df) == 0:
                    st.warning(f"🤖 No jobs found matching your AI target: '{ai_target}'. Try different keywords or clear the AI filter.")
                    return
                else:
                    st.info(f"🤖 AI filtered {len(filtered_df)} relevant jobs based on: '{ai_target}'")

        if selected_company != 'All':
            filtered_df = filtered_df[filtered_df['company'] == selected_company]
        
        if selected_location != 'All':
            filtered_df = filtered_df[filtered_df['location'] == selected_location]
        
        if selected_date != 'All':
            from datetime import datetime, timedelta
            today = datetime.now()
            if selected_date == 'Last 7 days':
                cutoff = today - timedelta(days=7)
            elif selected_date == 'Last 14 days':
                cutoff = today - timedelta(days=14)
            elif selected_date == 'Last 30 days':
                cutoff = today - timedelta(days=30)
            
            filtered_df['date_posted_dt'] = pd.to_datetime(filtered_df['date_posted'])
            filtered_df = filtered_df[filtered_df['date_posted_dt'] >= cutoff]
            filtered_df = filtered_df.drop('date_posted_dt', axis=1)
        
        if selected_salary == 'Has Salary':
            filtered_df = filtered_df[
                (pd.notna(filtered_df['min_amount']) | pd.notna(filtered_df['max_amount']))
            ]
        elif selected_salary == 'No Salary Specified':
            filtered_df = filtered_df[
                (pd.isna(filtered_df['min_amount']) & pd.isna(filtered_df['max_amount']))
            ]
        
        # Apply sorting
        if not filtered_df.empty:
            if st.session_state.sort_column in filtered_df.columns:
                filtered_df = filtered_df.sort_values(
                    by=st.session_state.sort_column, 
                    ascending=st.session_state.sort_ascending
                ).reset_index(drop=True)
        
        # Update total after filtering
        total_filtered_jobs = len(filtered_df)
        total_pages = (total_filtered_jobs + jobs_per_page - 1) // jobs_per_page if total_filtered_jobs > 0 else 1
        
        # Reset page if it's beyond the new total pages
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = 1
        
        st.markdown("---")
        
        # Show filter results
        if total_filtered_jobs != total_jobs:
            search_info = f" matching '{search_query}'" if search_query and search_query.strip() else ""
            st.info(f"Showing {total_filtered_jobs} jobs{search_info} (filtered from {total_jobs} total)")
        
        # Pagination controls with Previous/Next buttons and Go to input (top)
        pag1, pag2, pag3, pag4, pag5, pag6 = st.columns([1, 0.6, 1.5, 1, 0.4, 1])
        with pag1:
            if st.button("◀ Previous", key="prev_top", disabled=st.session_state.current_page <= 1):
                st.session_state.current_page = max(1, st.session_state.current_page - 1)
                st.rerun()
        with pag2:
            st.markdown(f"<div style='display: flex; align-items: center; height: 38px;'>Page {st.session_state.current_page}</div>", unsafe_allow_html=True)
        with pag3:
            st.markdown(f"<div style='display: flex; align-items: center; height: 38px;'>of {total_pages} ({total_filtered_jobs} total jobs)</div>", unsafe_allow_html=True)
        with pag4:
            if st.button("Next ▶", key="next_top", disabled=st.session_state.current_page >= total_pages):
                st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                st.rerun()
        with pag5:
            st.markdown("<div style='display: flex; align-items: center; height: 38px;'>Go to</div>", unsafe_allow_html=True)
        with pag6:
            jump_page = st.number_input(" ", min_value=1, max_value=total_pages, value=st.session_state.current_page, key="jump_page", label_visibility="collapsed")
            if jump_page != st.session_state.current_page:
                st.session_state.current_page = jump_page
                st.rerun()
        
        if total_filtered_jobs == 0:
            st.warning("No jobs match your current filters. Try adjusting the filter criteria.")
            return
        
        start_idx = (st.session_state.current_page - 1) * jobs_per_page
        end_idx = min(start_idx + jobs_per_page, total_filtered_jobs)
        page_data = filtered_df.iloc[start_idx:end_idx].copy().reset_index(drop=True)
        
        # Format data for display
        page_data['formatted_salary'] = page_data.apply(format_salary, axis=1)
        page_data['truncated_title'] = [truncate_title(title) for title in page_data['title']]
        
        # Add custom CSS for job row borders and compactness
        st.markdown("""
        <style>
        .job-row {
            border-bottom: 2px solid #444;
            margin-bottom: 0px;
            padding-bottom: 0.1rem;
            padding-top: 0.1rem;
        }
        .job-row [data-testid="column"] > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            line-height: 1.2 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            font-weight: normal !important;
        }
        .job-row button, .job-row .stButton > button {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display job table with sortable headers
        # Check if AI filtering is active to show score columns
        ai_active = st.session_state.get('ai_filter_applied', False)
        
        if ai_active and 'ai_score' in filtered_df.columns:
            # AI filtering is active - show score columns
            cols = st.columns([3, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
            sort_columns = ['ai_score', 'title', 'company', 'location', 'date_posted', 'min_amount', None]
            column_names = ['AI Score', 'Job Title', 'Company', 'Location', 'Date', 'Salary', 'JD']
        else:
            # Normal table without AI scores
            cols = st.columns([4, 1.5, 2, 1.5, 2.5, 1])
            sort_columns = ['title', 'company', 'location', 'date_posted', 'min_amount', None]
            column_names = ['Job Title', 'Company', 'Location', 'Date', 'Salary', 'JD']
        
        for i, (col_name, sort_col) in enumerate(zip(column_names, sort_columns)):
            if sort_col:
                # Add sorting indicator
                indicator = ""
                if st.session_state.sort_column == sort_col:
                    indicator = " ↑" if st.session_state.sort_ascending else " ↓"
                
                if cols[i].button(f"**{col_name}{indicator}**", key=f"sort_{sort_col}", use_container_width=True):
                    if st.session_state.sort_column == sort_col:
                        st.session_state.sort_ascending = not st.session_state.sort_ascending
                    else:
                        st.session_state.sort_column = sort_col
                        st.session_state.sort_ascending = True
                    st.rerun()
            else:
                cols[i].write("")
        
        # Display each job row
        for idx, (_, job) in enumerate(page_data.iterrows()):
            st.markdown('<div class="job-row">', unsafe_allow_html=True)
            
            if ai_active and 'ai_score' in job:
                # AI filtering is active - show score columns
                cols = st.columns([3, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
                
                # AI Score column with color coding
                score = job.get('ai_score', 0)
                confidence = job.get('ai_confidence', 'LOW')
                if score >= 80:
                    score_color = "limegreen"
                    score_emoji = "🎯"
                elif score >= 60:
                    score_color = "green"
                    score_emoji = "✅"
                elif score >= 40:
                    score_color = "orange"
                    score_emoji = "⚠️"
                elif score >= 20:
                    score_color = "yellow"
                    score_emoji = "🤔"
                else:
                    score_color = "#ff6666"
                    score_emoji = "❌"
                
                cols[0].markdown(f"<span style='color:{score_color}; font-weight:bold;'>{score_emoji} {score}/100</span><br><small>{confidence}</small>", unsafe_allow_html=True)
                cols[1].write(job['truncated_title'])
                cols[2].write(job['company'])
                cols[3].write(job['location'])
                date_str = pd.to_datetime(job['date_posted']).strftime('%Y-%m-%d') if pd.notna(job['date_posted']) else 'N/A'
                cols[4].write(date_str)
                cols[5].markdown(f"<span style='font-family: inherit;'>{job['formatted_salary']}</span>", unsafe_allow_html=True)
            else:
                # Normal table without AI scores
                cols = st.columns([4, 1.5, 2, 1.5, 2.5, 1])
                cols[0].write(job['truncated_title'])
                cols[1].write(job['company'])
                cols[2].write(job['location'])
                date_str = pd.to_datetime(job['date_posted']).strftime('%Y-%m-%d') if pd.notna(job['date_posted']) else 'N/A'
                cols[3].write(date_str)
                cols[4].markdown(f"<span style='font-family: inherit;'>{job['formatted_salary']}</span>", unsafe_allow_html=True)
            
            # Check if this job is currently selected
            is_selected = (st.session_state.selected_job is not None and 
                          st.session_state.selected_job.get('title') == job['title'] and
                          st.session_state.selected_job.get('company') == job['company'] and
                          st.session_state.selected_job.get('location') == job['location'])
            
            # Style the button based on selection state
            if is_selected:
                # Selected button - red background
                if cols[-1].button("View", key=f"view_{start_idx + idx}", type="primary"):
                    # If already selected, clicking again will close it
                    st.session_state.selected_job = None
                    st.rerun()
            else:
                # Normal button
                if cols[-1].button("View", key=f"view_{start_idx + idx}"):
                    # Include AI data in selected job if available
                    selected_job_data = {
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'date_posted': job['date_posted'],
                        'job_type': job.get('job_type', 'Not specified'),
                        'salary': job['formatted_salary'],
                        'description': job.get('description', 'No description available'),
                        'job_url': job.get('job_url_direct', None)
                    }
                    
                    # Add AI data if available
                    if ai_active and 'ai_score' in job:
                        selected_job_data['ai_score'] = job.get('ai_score', 0)
                        selected_job_data['ai_confidence'] = job.get('ai_confidence', 'LOW')
                        selected_job_data['ai_reasoning'] = job.get('ai_reasoning', 'No reasoning available')
                    
                    st.session_state.selected_job = selected_job_data
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.caption(f"Showing jobs {start_idx+1} to {end_idx} of {total_filtered_jobs}")
        
        # Pagination controls (bottom)
        st.markdown("---")
        pag1b, pag2b, pag3b, pag4b, pag5b, pag6b = st.columns([1, 0.6, 1.5, 1, 0.4, 1])
        with pag1b:
            if st.button("◀ Previous", key="prev_bottom", disabled=st.session_state.current_page <= 1):
                st.session_state.current_page = max(1, st.session_state.current_page - 1)
                st.session_state.scroll_to_top = True
                st.rerun()
        with pag2b:
            st.markdown(f"<div style='display: flex; align-items: center; height: 38px;'>Page {st.session_state.current_page}</div>", unsafe_allow_html=True)
        with pag3b:
            st.markdown(f"<div style='display: flex; align-items: center; height: 38px;'>of {total_pages} ({total_filtered_jobs} total jobs)</div>", unsafe_allow_html=True)
        with pag4b:
            if st.button("Next ▶", key="next_bottom", disabled=st.session_state.current_page >= total_pages):
                st.session_state.current_page = min(total_pages, st.session_state.current_page + 1)
                st.session_state.scroll_to_top = True
                st.rerun()
        with pag5b:
            st.markdown("<div style='display: flex; align-items: center; height: 38px;'>Go to</div>", unsafe_allow_html=True)
        with pag6b:
            jump_page_b = st.number_input("  ", min_value=1, max_value=total_pages, value=st.session_state.current_page, key="jump_page_b", label_visibility="collapsed")
            if jump_page_b != st.session_state.current_page:
                st.session_state.current_page = jump_page_b
                st.session_state.scroll_to_top = True
                st.rerun()
    
    # Auto-scroll to top if triggered by bottom pagination
    if st.session_state.scroll_to_top:
        st.markdown("""
        <script>
        setTimeout(function() {
            window.scrollTo(0, 0);
            var mainElement = window.parent.document.querySelector('.main');
            if (mainElement) {
                mainElement.scrollTo(0, 0);
            }
        }, 50);
        </script>
        """, unsafe_allow_html=True)
        st.session_state.scroll_to_top = False
    
    # Job details sidebar (LinkedIn style)
    with detail_col:
        if st.session_state.selected_job is not None:
            job = st.session_state.selected_job
            st.markdown("### 📄 Job Details")
            st.markdown("---")
            st.markdown(f"**{job['title']}**")
            st.markdown(f"🏢 **{job['company']}**")
            
            # Display AI score information if available
            if 'ai_score' in job:
                score = job['ai_score']
                confidence = job['ai_confidence']
                reasoning = job['ai_reasoning']
                
                # Color coding for score
                if score >= 80:
                    score_color = "limegreen"
                    score_emoji = "🎯"
                    score_label = "Perfect Match"
                elif score >= 60:
                    score_color = "green"
                    score_emoji = "✅"
                    score_label = "Highly Relevant"
                elif score >= 40:
                    score_color = "orange"
                    score_emoji = "⚠️"
                    score_label = "Moderately Relevant"
                elif score >= 20:
                    score_color = "yellow"
                    score_emoji = "🤔"
                    score_label = "Slightly Relevant"
                else:
                    score_color = "#ff6666"
                    score_emoji = "❌"
                    score_label = "Not Relevant"
                
                st.markdown("---")
                st.markdown("### 🤖 AI Analysis")
                st.markdown(f"<span style='color:{score_color}; font-size: 1.2em; font-weight: bold;'>{score_emoji} {score}/100 - {score_label}</span>", unsafe_allow_html=True)
                st.markdown(f"**Confidence:** {confidence}")
                st.markdown("**AI Reasoning:**")
                st.markdown(f"*{reasoning}*")
                st.markdown("---")
            
            if job['job_url']:
                st.markdown(f'<a href="{job["job_url"]}" target="_blank"><button style="background-color:#1f77b4;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;width:100%;">🔗 Link to apply</button></a>', unsafe_allow_html=True)
            st.markdown('<p style="margin-top: 0.5rem; margin-bottom: 0.5rem; font-weight: bold;">📝 Job Description:</p>', unsafe_allow_html=True)
            desc = str(job['description']).replace('<', '').replace('>', '').strip() if job['description'] and job['description'] != 'No description available' else "No description available for this job."
            # Use a simple container with no special styling to blend with theme
            with st.container():
                st.markdown(f"""
                <div style='padding: 1rem; min-height: 400px; max-height: 70vh; overflow-y: auto; border: 1px solid rgba(250, 250, 250, 0.1); border-radius: 0.5rem;'>
                {desc}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("### 📄 Job Details")
            st.markdown("---")
            st.info("👈 Click **View** button next to any job to see details here")
            st.markdown("""
            **Tips:**
            - Click View to see full job details
            - Click column headers to sort
            - Use filters to narrow down results
            - Click Link to apply to go to the job page
            - Use pagination to browse all jobs
            - Use AI Filter to get relevance scores
            """)

# Main app
def main():
    st.title("🚀 JobSpy Enhanced - Job Scraper")
    st.markdown("---")
    
    # Custom CSS to make the right panel sticky and scrollable
    st.markdown("""
    <style>
    /* Make the job details panel sticky */
    .stColumn:nth-child(2) {
        position: sticky;
        top: 1rem;
        height: fit-content;
        max-height: calc(100vh - 2rem);
    }
    
    /* Target the second column in the main content area */
    .main .block-container > div > div > div:nth-child(2) {
        position: sticky;
        top: 1rem;
        height: fit-content;
        max-height: calc(100vh - 2rem);
        overflow-y: visible;
    }
    
    /* Alternative approach using data attributes */
    div[data-testid="column"]:nth-child(2) {
        position: sticky;
        top: 1rem;
        height: fit-content;
        max-height: calc(100vh - 2rem);
    }
    
    /* Ensure main content doesn't get affected */
    .main .block-container {
        padding-top: 1rem;
    }
    
    /* Make sidebar collapse button always visible */
    .css-1d391kg {
        opacity: 1 !important;
    }
    
    /* Alternative selector for sidebar collapse button */
    [data-testid="collapsedControl"] {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Sidebar button visibility */
    .css-1oe5cao {
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📋 Search Parameters")
        
        # Company input
        companies_input = st.text_area(
            "Companies (separate with commas)",
            placeholder="Amazon, Walmart, Lyft, Google",
            help="Enter company names separated by commas"
        )
        
        # Location input
        location = st.text_input(
            "Location",
            placeholder="Seattle, WA or United States",
            help="Enter city, state or country"
        )
        
        # Time filter
        hours_old = st.number_input(
            "Hours old (0 for all time)",
            min_value=0,
            value=0,
            help="Filter jobs by posting age"
        )
        hours_old = None if hours_old == 0 else hours_old
        
        # Results limit (hidden from user, set to high default)
        results_wanted = 5000
        
        # Search button
        search_button = st.button("🔍 Start Search", type="primary")
    
    # Main content area
    if search_button:
        # Reset pagination, selected job, and filters when starting new search
        st.session_state.current_page = 1
        st.session_state.selected_job = None
        # Clear any existing job title search filter
        if 'job_title_search' in st.session_state:
            del st.session_state.job_title_search
        
        if not companies_input.strip():
            st.error("❌ Please enter at least one company")
            return
        
        if not location.strip():
            st.error("❌ Please enter a location")
            return
        
        # Parse companies
        companies = [company.strip() for company in companies_input.split(',') if company.strip()]
        
        # Display search summary (compact)
        st.markdown(f"**🎯 Search:** {len(companies)} companies in {location} | {f'{hours_old}h old' if hours_old else 'All time'} | Searching all available jobs")
        
        # Start scraping with progress indicator
        with st.spinner("🔍 Scraping jobs..."):
            jobs = scrape_multiple_companies(companies, location, hours_old, results_wanted)
        
        if len(jobs) == 0:
            st.error("❌ No jobs found for any company")
            return
        
        # Store jobs in session state for pagination
        st.session_state.jobs_data = jobs
        
        # Calculate average accuracy
        accuracies = []
        for company in companies:
            company_jobs = jobs[jobs['search_company'] == company]
            if len(company_jobs) > 0:
                accurate_jobs = company_jobs[company_jobs['company'].str.contains(company, case=False, na=False)]
                accuracy = len(accurate_jobs) / len(company_jobs) * 100
                accuracies.append(accuracy)
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        # Create collapsible search summary
        with st.expander("📊 Search Summary", expanded=False):
            st.success(f"**📊 Found {len(jobs)} jobs** from {len(jobs['search_company'].unique())} companies across {len(jobs['location'].unique())} locations (Accuracy: {avg_accuracy:.1f}%)")
        
        # Show main result briefly
        st.success(f"✅ **Search Complete: {len(jobs)} jobs found**")
        
        # Job data section with pagination
        st.header("📋 Job Data")
        display_job_data_table(jobs)
    
    elif 'jobs_data' in st.session_state:
        # Show existing data if available
        st.header("📋 Job Data")
        display_job_data_table(st.session_state.jobs_data)
    
    else:
        # Welcome message
        st.header("Welcome to JobSpy Enhanced! 🚀")
        st.markdown("""
        This tool helps you scrape job postings from Indeed with company-specific filtering.
        
        **Features:**
        - ✅ Company-specific job filtering (100% accuracy)
        - ✅ Multi-company search
        - ✅ Time-based filtering
        - ✅ Searches all available jobs (up to 5000 per company)
        - ✅ Clean paginated job table
        - ✅ LinkedIn-style job details sidebar
        - ✅ Proper salary formatting
        - 🤖 **NEW: AI-powered job filtering and ranking**
        
        **How to use:**
        1. Enter company names (separated by commas)
        2. Specify location
        3. Set time filter (optional)
        4. Click "Start Search"
        5. Browse through job results with Previous/Next
        6. **NEW:** Use AI Job Filter to find jobs matching your target profile
        7. Click "View" to see job details in right panel
        
        **Example:**
        - Companies: `Amazon, Walmart, Lyft`
        - Location: `Seattle, WA`
        - Hours old: `24` (for recent jobs)
        - AI Filter: `I want data science roles with Python and machine learning`
        """)

if __name__ == "__main__":
    main() 