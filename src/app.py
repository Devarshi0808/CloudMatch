import streamlit as st
import pandas as pd
import os
import requests
import random
import sqlite3
from marketplace_matcher import MarketplaceMatcher
from utils.add_images import get_marketplace_logos_html, get_image_html
from utils.cache import get_from_cache_fuzzy, set_in_cache, cleanup_cache, get_cache_stats

# --- Dynamic Tips ---
TIPS = [
    "🔁 You can search multiple vendors separated by commas!",
    "🧠 Tip: Use fuzzy names like 'redhat' or 'adobe inc'.",
    "🚀 Over 1,000 marketplace listings indexed and matched!",
    "✅ 135 vendors matched in last 24 hours",
    "🔍 Example vendors: Red Hat, Adobe, Databricks",
    "💡 Tip: You can also try partial vendor names like 'RedHat' or 'Adobe Inc'",
    "📊 Top 3 searched vendors today: Red Hat, Adobe, Microsoft",
    "🚀 Try searching for a solution like 'Photoshop' or 'GitLab Ultimate'"
]

# --- Streamlit Page Config & Styles ---
st.set_page_config(page_title="CloudMatch", layout="wide")
st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(135deg, #fdf6e3 0%, #e3f0ff 100%, #fffbe5 100%) !important;
    min-height: 100vh;
    }
</style>
""", unsafe_allow_html=True)

# Add custom CSS for sidebar width and input spacing
st.markdown('''
<style>
/* Reduce sidebar width */
section[data-testid="stSidebar"] {
    min-width: 270px !important;
    max-width: 300px !important;
    width: 18vw !important;
}
/* Increase padding between input boxes */
section[data-testid="stSidebar"] .stTextInput, section[data-testid="stSidebar"] .stAlert, section[data-testid="stSidebar"] .stButton, section[data-testid="stSidebar"] .stCheckbox {
    margin-bottom: 1.2rem !important;
}

/* Center main content vertically */
.main-vertical-center {
    min-height: 80vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
</style>
''', unsafe_allow_html=True)

# Add custom CSS for the 'Search Marketplaces' button to use a blue-based gradient
st.markdown('''
<style>
.stButton > button {
    background: linear-gradient(90deg, #4285F4 0%, #1f77b4 100%) !important;
    color: #fff !important;
    border: none !important;
    font-weight: 700;
    font-size: 1.08rem;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px 0 rgba(30, 90, 180, 0.10);
    padding: 0.6rem 1.5rem;
    transition: background 0.18s, box-shadow 0.18s, transform 0.18s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #1f77b4 0%, #4285F4 100%) !important;
    box-shadow: 0 6px 18px 0 rgba(30, 90, 180, 0.18);
    transform: scale(1.04);
}
</style>
''', unsafe_allow_html=True)

@st.cache_resource
def load_matcher():
    """Load the marketplace matcher with Excel data"""
    matcher = MarketplaceMatcher()
    success = matcher.load_excel_data('../data/Vendors_and_Products.xlsx')
    return matcher if success else None

@st.cache_resource
def pre_cache_popular_searches():
    """Pre-cache popular vendor/solution combinations"""
    from utils.cache import get_cache
    matcher = load_matcher()
    if matcher:
        cache = get_cache()
        cache.pre_cache_popular(matcher, top_n=15)
    return True

def main():
    """
    Main Streamlit app logic and UI orchestration.
    
    This function handles:
    - Loading the marketplace matcher with Excel data
    - Pre-caching popular searches if cache is empty
    - Processing search requests from the sidebar
    - Displaying search results and cache management
    - Managing session state for search results
    """
    matcher = load_matcher()
    if not matcher:
        st.error("❌ Failed to load marketplace matcher. Please check your Excel file.")
        return
    
    # Only pre-cache if cache is empty
    cache_stats = get_cache_stats()
    if cache_stats['total_entries'] == 0:
        pre_cache_popular_searches()

    if st.session_state.get('trigger_search'):
        vendor = st.session_state.get('search_vendor', '')
        solution = st.session_state.get('search_solution', '')
        # Reset the trigger so it doesn't loop
        st.session_state['trigger_search'] = False

        # Run the same search logic as the sidebar button
        cache_result = get_from_cache_fuzzy(vendor, solution or "")
        if cache_result:
            st.session_state.search_results = cache_result['result']
            st.session_state.searched = True
            st.session_state.not_in_excel = False
            st.session_state.cache_hit = True
            st.session_state.cache_stats = cache_result
        else:
            with st.spinner('⏳ Please wait, your results are being scraped...'):
                in_excel = matcher.is_in_excel(vendor, solution)
                if in_excel:
                    results = matcher.search_marketplaces(vendor, solution or "")
                    # Cache the result
                    set_in_cache(vendor, solution or "", results, 'excel_match')
                    st.session_state.search_results = results
                    st.session_state.searched = True
                    st.session_state.not_in_excel = False
                    st.session_state.cache_hit = False
                else:
                    mapped_vendor, vendor_score = matcher.map_vendor_to_closest(vendor)
                    if vendor_score >= 80:
                        results = matcher.search_marketplaces(mapped_vendor, solution or "")
                        # Cache the result
                        set_in_cache(vendor, solution or "", results, 'fuzzy_match')
                        st.session_state.search_results = results
                        st.session_state.searched = True
                        st.session_state.not_in_excel = False
                        st.session_state.cache_hit = False
                    else:
                        st.session_state.not_in_excel = True
                        aws_results = matcher.scrape_aws_marketplace(f"{vendor} {solution}")
                        azure_results = matcher.scrape_azure_marketplace(f"{vendor} {solution}")
                        gcp_results = matcher.scrape_gcp_marketplace(f"{vendor} {solution}")
                        st.session_state.aws_results = aws_results
                        st.session_state.azure_results = azure_results
                        st.session_state.gcp_results = gcp_results
                        if matcher.excel_data is not None:
                            all_products = matcher.excel_data['solution_name'].unique().tolist()
                        else:
                            all_products = []
                        st.session_state.llm_alternatives = suggest_alternatives_with_llm(f"{vendor} {solution}", all_products, n=3)
                        st.session_state.user_query = f"{vendor} {solution}"
                        st.session_state.searched = True
                        st.session_state.cache_hit = False
                        # Cache the direct scrape results
                        direct_results = {
                            'aws_results': aws_results,
                            'azure_results': azure_results,
                            'gcp_results': gcp_results,
                            'vendor': vendor,
                            'solution': solution,
                            'type': 'direct_scrape',
                            'llm_alternatives': st.session_state.llm_alternatives
                        }
                        st.session_state.search_results = direct_results
                        set_in_cache(vendor, solution or "", direct_results, 'direct_scrape')

    # --- CloudMatch Landing Section ---
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: 2.5rem;">
        <h1 style="font-size: 2.7rem; font-weight: 900; letter-spacing: -1px; margin-bottom: 0.3rem;">
            ☁️ CloudMatch 🔍
        </h1>
        <div style="font-size: 1.18rem; color: #444; margin-bottom: 1.2rem; font-weight: 500;">
            One search | All cloud marketplaces | Smarter vendor discovery
        </div>
        <ul style="margin: 0 0 1.2rem 0; font-size: 1.08rem; color: #222; text-align: left; max-width: 420px;">
            <li>🔍 Fuzzy & advanced matching</li>
            <li>🏷️ Confidence scoring</li>
            <li>💡 Smart suggestions</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- Marketplace Logos (real logos, clickable) ---
    st.markdown(get_marketplace_logos_html(), unsafe_allow_html=True)

    # --- Dynamic tip at the bottom ---
    tip = random.choice(TIPS)
    st.markdown(f"<div style='text-align:center; margin-top:1.5rem; font-size:1.1rem;'>💡 <i>{tip}</i></div>", unsafe_allow_html=True)
    
    # Sidebar for search
    st.sidebar.markdown("## 🔍 Search Configuration")
    vendor = st.sidebar.text_input("Vendor Name", placeholder="e.g., Microsoft, Adobe, GitLab")
    solution = st.sidebar.text_input("Solution/Product Name", placeholder="e.g., Office 365, Photoshop, GitLab Ultimate")
    if not solution:
        st.sidebar.info("💡 **Tip:** Leave solution blank to search for all products by this vendor across marketplaces.")

    if st.sidebar.button("🔍 Search Marketplaces", type="primary"):
        if not vendor:
            st.error("Please enter a vendor name.")
            return
        
        # Check cache first
        cache_result = get_from_cache_fuzzy(vendor, solution or "")
        if cache_result:
            st.session_state.search_results = cache_result['result']
            st.session_state.searched = True
            st.session_state.not_in_excel = False
            st.session_state.cache_hit = True
            st.session_state.cache_stats = cache_result
        else:
            with st.spinner('⏳ Please wait, your results are being scraped...'):
                in_excel = matcher.is_in_excel(vendor, solution)
                if in_excel:
                    results = matcher.search_marketplaces(vendor, solution or "")
                    # Cache the result
                    set_in_cache(vendor, solution or "", results, 'excel_match')
                    st.session_state.search_results = results
                    st.session_state.searched = True
                    st.session_state.not_in_excel = False
                    st.session_state.cache_hit = False
                else:
                    mapped_vendor, vendor_score = matcher.map_vendor_to_closest(vendor)
                    if vendor_score >= 80:
                        results = matcher.search_marketplaces(mapped_vendor, solution or "")
                        # Cache the result
                        set_in_cache(vendor, solution or "", results, 'fuzzy_match')
                        st.session_state.search_results = results
                        st.session_state.searched = True
                        st.session_state.not_in_excel = False
                        st.session_state.cache_hit = False
                    else:
                        st.session_state.not_in_excel = True
                        aws_results = matcher.scrape_aws_marketplace(f"{vendor} {solution}")
                        azure_results = matcher.scrape_azure_marketplace(f"{vendor} {solution}")
                        gcp_results = matcher.scrape_gcp_marketplace(f"{vendor} {solution}")
                        st.session_state.aws_results = aws_results
                        st.session_state.azure_results = azure_results
                        st.session_state.gcp_results = gcp_results
                        if matcher.excel_data is not None:
                            all_products = matcher.excel_data['solution_name'].unique().tolist()
                        else:
                            all_products = []
                        st.session_state.llm_alternatives = suggest_alternatives_with_llm(f"{vendor} {solution}", all_products, n=3)
                        st.session_state.user_query = f"{vendor} {solution}"
                        st.session_state.searched = True
                        st.session_state.cache_hit = False
                        # Cache the direct scrape results
                        direct_results = {
                            'aws_results': aws_results,
                            'azure_results': azure_results,
                            'gcp_results': gcp_results,
                            'vendor': vendor,
                            'solution': solution,
                            'type': 'direct_scrape',
                            'llm_alternatives': st.session_state.llm_alternatives
                        }
                        st.session_state.search_results = direct_results
                        set_in_cache(vendor, solution or "", direct_results, 'direct_scrape')

    if hasattr(st.session_state, 'searched') and st.session_state.searched and hasattr(st.session_state, 'search_results'):
        results = st.session_state.search_results
        # If result is a direct scrape (not Excel/fuzzy match), show not-in-excel UI
        if (
            (hasattr(st.session_state, 'not_in_excel') and st.session_state.not_in_excel)
            or (results and results.get('type') == 'direct_scrape')
            or ('vendor_match_score' not in results)
        ):
            display_not_in_excel_results()
        else:
            display_results(results)

    if st.sidebar.checkbox("📊 Show Sample Data"):
        display_sample_data(matcher)

    # Cache management section
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🗄️ Cache Management")
    
    # Show cache stats
    cache_stats = get_cache_stats()
    st.sidebar.metric("Cached Searches", cache_stats['total_entries'])
    st.sidebar.metric("Avg Access Count", cache_stats['avg_access_count'])
    
    # Cache cleanup button
    if st.sidebar.button("🧹 Clean Expired Cache"):
        cleanup_cache()
        st.sidebar.success("Cache cleaned!")
        st.experimental_rerun()
    
    # Show cache hit indicator if applicable
    if hasattr(st.session_state, 'cache_hit') and st.session_state.cache_hit:
        st.sidebar.success("✅ Result from cache!")
        if hasattr(st.session_state, 'cache_stats'):
            st.sidebar.info(f"Cache hits: {st.session_state.cache_stats['access_count']}")

def display_results(results):
    """Display marketplace search results with mapping information, availability overview, and detailed product listings."""
    if not results:
        st.error("No results to display.")
        return
    st.markdown("---")
    
    # Show search results header using mapped vendor/solution for clarity
    mapped_vendor = results.get('mapped_vendor', results.get('original_vendor', ''))
    mapped_solution = results.get('mapped_solution', results.get('original_solution', ''))
    
    if not mapped_solution:
        st.markdown(f"## 📋 Search Results for: <b>{mapped_vendor}</b>", unsafe_allow_html=True)
    else:
        st.markdown(f"## 📋 Search Results for: <b>{mapped_vendor}</b> - <b>{mapped_solution}</b>", unsafe_allow_html=True)

    
    # Show mapping information
    if results['vendor_match_score'] > 0 or results['solution_match_score'] > 0:
        st.markdown("### 🔄 Mapping Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if results['vendor_match_score'] > 0:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2ca02c15, #2ca02c05); 
                    border: 2px solid #2ca02c; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                    <p style="margin: 0; font-weight: bold; color: #2ca02c;">Vendor Mapped</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        <strong>{results['original_vendor']}</strong> → <strong>{results['mapped_vendor']}</strong>
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #666;">({results['vendor_match_score']:.1f}% match)</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ff7f0e15, #ff7f0e05); 
                    border: 2px solid #ff7f0e; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">ℹ️</div>
                    <p style="margin: 0; font-weight: bold; color: #ff7f0e;">Vendor Not Found</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        <strong>{results['original_vendor']}</strong>
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #666;">Searching directly</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if results['solution_match_score'] > 0:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2ca02c15, #2ca02c05); 
                    border: 2px solid #2ca02c; 
                    border-radius: 10px; 
                    padding: 1rem; 
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                    <p style="margin: 0; font-weight: bold; color: #2ca02c;">Solution Mapped</p>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        <strong>{results['original_solution']}</strong> → <strong>{results['mapped_solution']}</strong>
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #666;">({results['solution_match_score']:.1f}% match)</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    border: 2.5px solid #d62728;
                    border-radius: 15px;
                    padding: 1.2rem;
                    text-align: center;
                    background: linear-gradient(135deg, #d6272808, #fff0);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.08);
                    width: 100%;
                    margin: 0 auto;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                ">
                    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">❗</div>
                    <h3 style="color: #d62728; margin: 0.2rem 0 0.1rem 0; font-size: 1.3rem; font-weight: bold;">Oops! Solution Input Missing</h3>
                </div>
                """, unsafe_allow_html=True)
    
    # FIXED: Marketplace Availability Overview with proper container sizing
    st.markdown("### 🏪 Marketplace Availability")
    
    # Create marketplace availability cards with improved responsive styling
    marketplaces = [
        ("AWS Marketplace", "AWS", results['aws_results'], len(results['aws_results']), "#FF9900"),
        ("Azure Marketplace", "Azure", results['azure_results'], len(results['azure_results']), "#0078D4"),
        ("Google Cloud Platform", "GCP", results['gcp_results'], len(results['gcp_results']), "#4285F4")
    ]
    
    # Add a container div to control the overall layout
    st.markdown("""
    <div style="
        display: flex; 
        flex-wrap: wrap; 
        gap: 1rem; 
        justify-content: space-between; 
        margin: 1rem 0;
        width: 100%;
        box-sizing: border-box;
    ">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    for i, (name, key, results_list, count, color) in enumerate(marketplaces):
        with [col1, col2, col3][i]:
            logo_html = get_marketplace_logo_html(key, width=120, height=80)
            gradient = "linear-gradient(135deg, #e3f0ff 0%, #ffe5c2 100%)"
            if count > 0:
                st.markdown(f"""
                <div style="
                    border: 2px solid {color}; 
                    border-radius: 15px; 
                    padding: 1.5rem 1rem 1rem 1rem; 
                    text-align: center; 
                    background: {gradient};
                    box-shadow: 0 4px 6px rgba(0,0,0,0.08);
                    width: 100%;
                    max-width: 100%;
                    height: 170px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                    align-items: center;
                    box-sizing: border-box;
                    overflow: hidden;
                ">
                    <div style="margin-bottom: 0.5rem; margin-top: 0.2rem; flex-shrink: 0; display: flex; justify-content: center; align-items: center;">{logo_html}</div>
                    <h3 style="color: {color}; margin: 0.2rem 0 0.1rem 0; font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;">{name}</h3>
                    <h2 style="color: {color}; margin: 0.1rem 0 0.1rem 0; font-size: 1.3rem; flex-shrink: 0;">{count} products</h2>
                    <p style="color: #2ca02c; font-weight: bold; margin: 0; font-size: 1.05rem; flex-shrink: 0;">✅ Available</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    border: 2px solid #d62728; 
                    border-radius: 15px; 
                    padding: 1.5rem 1rem 1rem 1rem; 
                    text-align: center; 
                    background: {gradient};
                    box-shadow: 0 4px 6px rgba(0,0,0,0.08);
                    width: 100%;
                    max-width: 100%;
                    height: 170px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                    align-items: center;
                    box-sizing: border-box;
                    overflow: hidden;
                ">
                    <div style="margin-bottom: 0.5rem; margin-top: 0.2rem; flex-shrink: 0; display: flex; justify-content: center; align-items: center;">{logo_html}</div>
                    <h3 style="color: {color}; margin: 0.2rem 0 0.1rem 0; font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;">{name}</h3>
                    <h2 style="color: #d62728; margin: 0.1rem 0 0.1rem 0; font-size: 1.3rem; flex-shrink: 0;">0 products</h2>
                    <p style="color: #d62728; font-weight: bold; margin: 0; font-size: 1.05rem; flex-shrink: 0;">❌ Not found</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Close the container div
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Best matches summary with score breakdown
    summary = results['summary']
    if summary['best_matches']:
        st.markdown("### 🎯 Best Matches")
        for match in summary['best_matches'][:3]:  # Show top 3
            confidence_class = get_confidence_class(match['confidence'])
            
            # Get marketplace color
            marketplace_colors = {
                'AWS': '#FF9900',
                'Azure': '#0078D4', 
                'GCP': '#4285F4'
            }
            color = marketplace_colors.get(match['marketplace'], '#1f77b4')
            
            # Create the main card
            st.markdown(f"""
            <div class="result-card {confidence_class}" style="
                border-left: 4px solid {color}; 
                border-radius: 8px; 
                padding: 1.5rem; 
                margin-bottom: 1rem; 
                background: linear-gradient(135deg, {color}08, {color}02);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex; align-items: center; gap: 1rem;
                width: 100%;
                box-sizing: border-box;
                overflow: hidden;
            ">
                <div style="flex-shrink:0;">{get_marketplace_logo_html(match['marketplace'])}</div>
                <div style="flex:1; min-width: 0;">
                    <h4 style="color: {color}; margin-bottom: 0.5rem; display:inline; vertical-align:middle; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{match['title']}</h4>
                    <p style="margin-bottom: 0.5rem;"><strong>Marketplace:</strong> {match['marketplace']} | 
                <strong>Confidence:</strong> {match['confidence']:.1f}%</p>
                    <a href="{match['link']}" target="_blank" style="color: {color}; text-decoration: none; font-weight: bold;">
                        🔗 View on {match['marketplace']}
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show score breakdown in an expander
            if 'score_breakdown' in match:
                with st.expander(f"Score Breakdown for: {match['title']}"):
                    breakdown = match['score_breakdown']
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Fuzzy Match (60%)", f"{breakdown['fuzzy']:.1f}%")
                    with col2:
                        st.metric("TF-IDF (40%)", f"{breakdown['tfidf']:.1f}%")
    
    # Marketplace Selection for Detailed View
    st.markdown("### 🔍 Detailed Marketplace Results")
    
    # Create tabs for each marketplace that has results
    available_marketplaces = []
    for name, key, results_list, count, color in marketplaces:
        if count > 0:
            available_marketplaces.append((name, key, results_list, color))
    
    if available_marketplaces:
        # Use tabs for marketplace selection
        tab_names = [name for name, key, _, _ in available_marketplaces]
        tabs = st.tabs(tab_names)
        
        for i, (name, key, results_list, color) in enumerate(available_marketplaces):
            with tabs[i]:
                st.markdown(f"#### {name} - {len(results_list)} Products")
                display_marketplace_results(results_list, color)
    else:
        st.warning("⚠️ No products found on any marketplace. Consider trying different search terms or checking alternative product names.")
        suggest_alternatives(results['original_vendor'], results['original_solution'])

def display_marketplace_results(results, color):
    """Display results for a specific marketplace"""
    if not results:
        st.info("No products found on this marketplace.")
        return
    
    # Show summary stats
    st.metric("Total Products", len(results))
    
    st.markdown("---")
    
    # Sort results by confidence (highest first)
    sorted_results = sorted(results, key=lambda x: x['confidence'], reverse=True)
    
    for i, result in enumerate(sorted_results[:10]):  # Show top 10 results
        confidence_class = get_confidence_class(result['confidence'])
        
        # Create a card for each result
        st.markdown(f"""
        <div class="result-card {confidence_class}" style="
            margin-bottom: 1rem; 
            border-left: 4px solid {color}; 
            border-radius: 8px; 
            padding: 1rem; 
            background: linear-gradient(135deg, {color}08, {color}02);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex; align-items: center; gap: 1rem;"
        >
            <div style="flex-shrink:0;">{get_marketplace_logo_html(result['marketplace'])}</div>
            <div style="flex:1;">
                <h4 style="color: {color}; margin-bottom: 0.5rem; display:inline; vertical-align:middle;">#{i+1} - {result['title']}</h4>
                <p style="margin-bottom: 0.5rem;"><strong>Confidence:</strong> {result['confidence']:.1f}% | 
            <strong>Marketplace:</strong> {result['marketplace']}</p>
                <a href="{result['link']}" target="_blank" style="color: {color}; text-decoration: none; font-weight: bold;">
                🔗 View on {result['marketplace']}
            </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show score breakdown in an expander
        with st.expander(f"Score Breakdown for: {result['title']}"):
            breakdown = result['score_breakdown']
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Fuzzy Match (60%)", f"{breakdown['fuzzy']:.1f}%")
            with col2:
                st.metric("TF-IDF (40%)", f"{breakdown['tfidf']:.1f}%")
            
            # Show vendor info if available
            if result.get('vendor'):
                st.markdown(f"**Vendor:** {result['vendor']}")
            
            # Show description if available
            if result.get('description'):
                st.markdown(f"**Description:** {result['description'][:200]}...")
    
    # Show "View More" if there are more results
    if len(results) > 10:
        st.info(f"Showing top 10 of {len(results)} results. Use the search function to see more specific results.")

def get_confidence_class(confidence):
    """Get CSS class based on confidence level"""
    if confidence >= 70:
        return "high-confidence"
    elif confidence >= 50:
        return "medium-confidence"
    else:
        return "low-confidence"

def suggest_alternatives(vendor, solution):
    """Suggest alternatives when no matches are found"""
    st.markdown("### 💡 Alternative Suggestions")
    
    # Simple category-based suggestions
    suggestions = {
        'Adobe': ['Creative Cloud alternatives', 'Design software', 'Creative tools'],
        'Salesforce': ['CRM alternatives', 'Sales automation', 'Customer management'],
        'ServiceNow': ['ITSM alternatives', 'Service management', 'IT operations'],
        'Atlassian': ['Project management alternatives', 'Development tools', 'Team collaboration'],
        'Microsoft': ['Office alternatives', 'Productivity tools', 'Business software']
    }
    
    if vendor in suggestions:
        st.markdown(f"**For {vendor} {solution}, consider searching for:**")
        for suggestion in suggestions[vendor]:
            st.markdown(f"- {suggestion}")
    
    st.markdown("**General tips:**")
    st.markdown("- Try searching with just the vendor name")
    st.markdown("- Use different product name variations")
    st.markdown("- Check for alternative product names")

def display_sample_data(matcher):
    """Display only vendors with multiple products, with each product as a clickable link to trigger a search."""
    st.markdown("---")
    st.markdown("## 📊 Vendors with Multiple Products")
    
    vendors_with_multiple = []
    for vendor in matcher.vendors:
        solutions = matcher.get_solutions_for_vendor(vendor)
        unique_solutions = list(dict.fromkeys(solutions))  # Deduplicate, preserve order
        if len(unique_solutions) > 1:
            vendors_with_multiple.append({
                'vendor': vendor,
                'product_count': len(unique_solutions),
                'solutions': unique_solutions
            })
    
    if vendors_with_multiple:
        for vendor_data in vendors_with_multiple[:10]:  # Show top 10
            with st.expander(f"{vendor_data['vendor']} ({vendor_data['product_count']} products)"):
                for solution in vendor_data['solutions']:
                    # Use a button for each product to trigger a search
                    if st.button(f"{solution}", key=f"{vendor_data['vendor']}_{solution}"):
                        st.session_state['search_vendor'] = vendor_data['vendor']
                        st.session_state['search_solution'] = solution
                        st.session_state['trigger_search'] = True
                        st.experimental_rerun()

def get_marketplace_logo_html(marketplace, width=64, height=44):
    """Return the HTML for the marketplace logo (slightly smaller for better fit)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "images")
    logo_map = {
        'AWS': ("aws-logo.png", "AWS"),
        'Azure': ("azure-logo.png", "Azure"),
        'GCP': ("gcp-logo.png", "Google Cloud")
    }
    if marketplace in logo_map:
        img_file, alt = logo_map[marketplace]
        img_path = os.path.join(images_dir, img_file)
        return get_image_html(img_path, alt, width=width, height=height)
    return ""

def suggest_alternatives_with_llm(user_query, product_list, n=3):
    prompt = (
        f"A user searched for {user_query}, which is not in our product list. "
        f"From the following list, suggest {n} alternatives that are most similar in function or domain. "
        f"For each alternative, provide a one-sentence reason why it is a good alternative. "
        f"Format your response as: 1. Alternative Name: Reason. 2. ... 3. ... List: {', '.join(product_list)}"
    )
    print(f"[LLM] Prompt: {prompt}")
    print(f"[LLM] Product list length: {len(product_list)}")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.ok:
            text = response.json()["response"]
            print(f"[LLM] Raw response: {text}")
            # Parse numbered list: 1. Name: Reason. 2. ...
            alternatives = []
            for line in text.split("\n"):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, n+1)):
                    # Remove number and split at first colon
                    _, rest = line.split(".", 1)
                    if ":" in rest:
                        name, reason = rest.split(":", 1)
                        alternatives.append((name.strip(), reason.strip()))
                    else:
                        alternatives.append((rest.strip(), ""))
            return alternatives[:n]
        else:
            print(f"[LLM] LLM request failed: {response.status_code} {response.text}")
            return []
    except Exception as e:
        print(f"LLM alternative suggestion error: {e}")
        return []

def display_not_in_excel_results():
    st.markdown("---")
    st.markdown(f"## ❌ Product Not Found in Our List")
    # Show LLM-powered alternative suggestions first
    st.markdown("### 💡 Alternative Suggestions from Our List")
    results = getattr(st.session_state, 'search_results', {})
    alternatives = results.get('llm_alternatives', [])
    user_query = getattr(st.session_state, 'user_query', '').strip()
    if alternatives:
        st.markdown(f"Since {user_query} is not in our list, consider these alternatives:")
        for idx, (alt, reason) in enumerate(alternatives, 1):
            st.markdown(f"{idx}. {alt}")
            if reason:
                st.markdown(f"<span style='color:#888;font-size:0.95rem;'>{reason}</span>", unsafe_allow_html=True)
    else:
        st.markdown("_No alternatives found by LLM._")
    # Show info message below alternatives
    st.info("This product is not in our curated list. Here are direct marketplace results for your query.")
    # Show marketplace results (if any, top 3 only)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### AWS Marketplace")
        aws_results = results.get('aws_results', [])[:3]
        if aws_results:
            for r in aws_results:
                st.markdown(f"- [{r['title']}]({r['link']})")
        else:
            st.markdown("_No results found._")
    with col2:
        st.markdown("### Azure Marketplace")
        azure_results = results.get('azure_results', [])[:3]
        if azure_results:
            for r in azure_results:
                st.markdown(f"- [{r['title']}]({r['link']})")
        else:
            st.markdown("_No results found._")
    with col3:
        st.markdown("### Google Cloud Platform")
        gcp_results = results.get('gcp_results', [])[:3]
        if gcp_results:
            for r in gcp_results:
                st.markdown(f"- [{r['title']}]({r['link']})")
        else:
            st.markdown("_No results found._")

if __name__ == "__main__":
    main() 