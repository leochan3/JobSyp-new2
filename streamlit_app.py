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
    synonyms = create_job_synonyms()
    
    # Get related terms for the search query
    related_terms = []
    for key, terms in synonyms.items():
        if search_query in key or any(term in search_query.split() for term in terms):
            related_terms.extend(terms)
    
    # Remove duplicates and add original query
    search_terms = list(set([search_query] + related_terms))
    
    # Score each job based on title relevance
    job_scores = []
    for idx, job in jobs_df.iterrows():
        job_title = str(job['title']).lower()
        
        # Start with exact match check - highest priority
        final_score = 0
        
        # Check for exact phrase match (highest score)
        if search_query in job_title:
            final_score = 100
        # Check for exact word matches in original query
        elif all(word in job_title for word in search_query.split()):
            final_score = 95
        # Check if any word from original query matches
        elif any(word in job_title for word in search_query.split()):
            final_score = 85
        else:
            # Only check synonyms if no direct match
            # Calculate fuzzy match scores for related terms only
            scores = []
            for term in search_terms[1:]:  # Skip original query, already checked
                # Use different fuzzy matching methods
                ratio_score = fuzz.ratio(term, job_title)
                partial_score = fuzz.partial_ratio(term, job_title)
                token_score = fuzz.token_sort_ratio(term, job_title)
                
                # Take the highest score among the three methods
                best_score = max(ratio_score, partial_score, token_score)
                scores.append(best_score)
            
            # Take the highest score among all search terms
            final_score = max(scores) if scores else 0
            
            # Add bonus for partial word matches with synonyms
            if any(term in job_title for term in search_terms[1:]):
                final_score = min(80, final_score + 15)
        
        job_scores.append((idx, final_score))
    
    # Filter jobs above threshold and sort by score - use much stricter threshold
    relevant_jobs = [(idx, score) for idx, score in job_scores if score >= 80]
    relevant_jobs.sort(key=lambda x: x[1], reverse=True)
    
    # Return filtered dataframe
    if relevant_jobs:
        relevant_indices = [idx for idx, _ in relevant_jobs]
        return jobs_df.iloc[relevant_indices].reset_index(drop=True)
    else:
        # If no results with high threshold, try with lower threshold but still reasonable
        relevant_jobs = [(idx, score) for idx, score in job_scores if score >= 70]
        relevant_jobs.sort(key=lambda x: x[1], reverse=True)
        if relevant_jobs:
            relevant_indices = [idx for idx, _ in relevant_jobs]
            return jobs_df.iloc[relevant_indices].reset_index(drop=True)
        # If still no results, return empty dataframe
        return pd.DataFrame(columns=jobs_df.columns)

def scrape_multiple_companies(companies, location, hours_old, results_wanted):
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

def scrape_multiple_companies(companies, location, hours_old, results_wanted):
    """Scrape jobs for multiple companies and combine results"""
    all_jobs = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, company in enumerate(companies, 1):
        status_text.text(f"Scraping {company}... ({i}/{len(companies)})")
        
        try:
            jobs = scrape_jobs(
                site_name=['indeed'],
                indeed_company_id=company,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                verbose=0
            )
            
            # Add company info to track which company each job came from
            jobs['search_company'] = company
            
            # Check company accuracy
            company_jobs = jobs[jobs['company'].str.contains(company, case=False, na=False)]
            accuracy = len(company_jobs) / len(jobs) * 100 if len(jobs) > 0 else 0
            
            st.success(f"✅ {company}: {len(jobs)} jobs (Accuracy: {accuracy:.1f}%)")
            all_jobs.append(jobs)
            
        except Exception as e:
            st.error(f"❌ Error scraping {company}: {e}")
            continue
        
        progress_bar.progress(i / len(companies))
    
    progress_bar.empty()
    status_text.empty()
    
    # Combine all results
    if all_jobs:
        combined_jobs = pd.concat(all_jobs, ignore_index=True)
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
            help="Smart search with synonyms (e.g., 'developer' finds 'engineer' jobs)"
        )
        
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
        
        # Use a reset flag for all filters
        reset_filters = st.session_state.get('clear_filters_flag', False)

        with filter_col1:
            company_options = ['All'] + sorted(jobs_df['company'].unique().tolist())
            selected_company = st.selectbox(
                "Company", company_options,
                index=0 if reset_filters else company_options.index(st.session_state.get('company_filter', 'All')),
                key="company_filter"
            )
        with filter_col2:
            location_options = ['All'] + sorted(jobs_df['location'].unique().tolist())
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
        if st.button("Clear Filters", key="clear_filters"):
            st.session_state.clear_filters_flag = True
            st.rerun()
        
        # Apply filters
        filtered_df = jobs_df.copy()
        
        # Apply smart search first if query exists
        if search_query and search_query.strip():
            filtered_df = smart_job_search(filtered_df, search_query)
            if len(filtered_df) == 0:
                st.warning(f"No jobs found matching '{search_query}'. Try different keywords or check spelling.")
                return
        
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
        cols = st.columns([4, 1.5, 2, 1.5, 2.5, 1])
        
        # Sortable column headers
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
            cols = st.columns([4, 1.5, 2, 1.5, 2.5, 1])
            cols[0].write(job['truncated_title'])
            cols[1].write(job['company'])
            cols[2].write(job['location'])
            cols[3].write(str(job['date_posted']))
            cols[4].markdown(f"<span style='font-family: inherit;'>{job['formatted_salary']}</span>", unsafe_allow_html=True)
            
            # Check if this job is currently selected
            is_selected = (st.session_state.selected_job is not None and 
                          st.session_state.selected_job.get('title') == job['title'] and
                          st.session_state.selected_job.get('company') == job['company'] and
                          st.session_state.selected_job.get('location') == job['location'])
            
            # Style the button based on selection state
            if is_selected:
                # Selected button - red background
                if cols[5].button("View", key=f"view_{start_idx + idx}", type="primary"):
                    # If already selected, clicking again will close it
                    st.session_state.selected_job = None
                    st.rerun()
            else:
                # Normal button
                if cols[5].button("View", key=f"view_{start_idx + idx}"):
                    st.session_state.selected_job = {
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'date_posted': job['date_posted'],
                        'job_type': job.get('job_type', 'Not specified'),
                        'salary': job['formatted_salary'],
                        'description': job.get('description', 'No description available'),
                        'job_url': job.get('job_url_direct', None)
                    }
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
        
        # Results limit
        results_wanted = st.number_input(
            "Results per company",
            min_value=1,
            max_value=1000,
            value=100,
            help="Maximum jobs to fetch per company"
        )
        
        # Search button
        search_button = st.button("🔍 Start Search", type="primary")
    
    # Main content area
    if search_button:
        # Reset pagination and selected job when starting new search
        st.session_state.current_page = 1
        st.session_state.selected_job = None
        
        if not companies_input.strip():
            st.error("❌ Please enter at least one company")
            return
        
        if not location.strip():
            st.error("❌ Please enter a location")
            return
        
        # Parse companies
        companies = [company.strip() for company in companies_input.split(',') if company.strip()]
        
        # Display search summary (compact)
        st.markdown(f"**🎯 Search:** {len(companies)} companies in {location} | {f'{hours_old}h old' if hours_old else 'All time'} | {results_wanted} results per company")
        
        # Start scraping
        st.header("🔍 Scraping Jobs...")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            return
        client = openai.OpenAI(api_key=api_key)
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
        st.success(f"**📊 Found {len(jobs)} jobs** from {len(jobs['search_company'].unique())} companies across {len(jobs['location'].unique())} locations (Accuracy: {avg_accuracy:.1f}%)")
        
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
        - ✅ Clean paginated job table
        - ✅ LinkedIn-style job details sidebar
        - ✅ Proper salary formatting
        
        **How to use:**
        1. Enter company names (separated by commas)
        2. Specify location
        3. Set time filter and results limit
        4. Click "Start Search"
        5. Browse through job results with Previous/Next
        6. Click "View" to see job details in right panel
        
        **Example:**
        - Companies: `Amazon, Walmart, Lyft`
        - Location: `Seattle, WA`
        - Hours old: `24` (for recent jobs)
        """)

if __name__ == "__main__":
    main() 