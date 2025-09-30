import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_all_meetings, delete_meeting, search_meetings

def meeting_history_component():
    """Component for viewing and managing meeting history."""
    
    st.header("📚 Meeting History")
    
    # Search functionality
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search meetings", placeholder="Search by filename or content...")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        search_button = st.button("Search", type="primary")
    
    # Get meetings based on search
    if search_query and search_button:
        meetings = search_meetings(search_query)
        if meetings:
            st.success(f"Found {len(meetings)} meeting(s) matching '{search_query}'")
        else:
            st.warning(f"No meetings found matching '{search_query}'")
    else:
        meetings = get_all_meetings()
    
    if not meetings:
        st.info("📭 No meetings found. Upload a meeting recording to get started!")
        return
    
    # Filter and sort options
    st.subheader("🔧 Filter & Sort")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        date_range = None
        if meetings:
            dates = [datetime.strptime(m['upload_date'].split()[0], '%Y-%m-%d').date() for m in meetings]
            min_date = min(dates)
            max_date = max(dates)
            
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
    
    with col2:
        # Category filter
        categories = set()
        for meeting in meetings:
            if meeting.get('summary') and meeting['summary'].get('meeting_category'):
                categories.add(meeting['summary']['meeting_category'])
        
        if categories:
            selected_categories = st.multiselect(
                "Categories",
                options=list(categories),
                default=list(categories)
            )
        else:
            selected_categories = []
    
    with col3:
        # Sort options
        sort_options = {
            "Date (Newest First)": ("upload_date", False),
            "Date (Oldest First)": ("upload_date", True),
            "Filename (A-Z)": ("filename", True),
            "Filename (Z-A)": ("filename", False),
            "Duration (Longest First)": ("duration", False),
            "Duration (Shortest First)": ("duration", True)
        }
        
        sort_choice = st.selectbox("Sort by", options=list(sort_options.keys()))
        sort_key, sort_ascending = sort_options[sort_choice]
    
    # Apply filters
    filtered_meetings = filter_meetings(meetings, date_range, selected_categories)
    
    # Sort meetings
    if sort_key == "upload_date":
        filtered_meetings.sort(key=lambda x: x['upload_date'], reverse=not sort_ascending)
    elif sort_key == "filename":
        filtered_meetings.sort(key=lambda x: x['filename'].lower(), reverse=not sort_ascending)
    elif sort_key == "duration":
        filtered_meetings.sort(key=lambda x: x.get('duration', 0), reverse=not sort_ascending)
    
    # Display results count
    st.markdown(f"**Showing {len(filtered_meetings)} of {len(meetings)} meetings**")
    
    # Meeting list
    st.subheader("📋 Meetings")
    
    if filtered_meetings:
        display_meeting_list(filtered_meetings)
    else:
        st.info("No meetings match the current filters.")

def filter_meetings(meetings, date_range, selected_categories):
    """Filter meetings based on date range and categories."""
    filtered = []
    
    for meeting in meetings:
        # Date filter
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            meeting_date = datetime.strptime(meeting['upload_date'].split()[0], '%Y-%m-%d').date()
            if not (date_range[0] <= meeting_date <= date_range[1]):
                continue
        
        # Category filter
        if selected_categories:
            meeting_category = None
            if meeting.get('summary') and meeting['summary'].get('meeting_category'):
                meeting_category = meeting['summary']['meeting_category']
            
            if meeting_category not in selected_categories:
                continue
        
        filtered.append(meeting)
    
    return filtered

def display_meeting_list(meetings):
    """Display a list of meetings with details and actions."""
    
    for meeting in meetings:
        with st.expander(f"📁 {meeting['filename']} - {meeting['upload_date']}"):
            display_meeting_summary_card(meeting)

def display_meeting_summary_card(meeting):
    """Display a summary card for a meeting."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Basic info
        st.markdown(f"**📅 Date:** {meeting['upload_date']}")
        st.markdown(f"**⏱️ Duration:** {meeting.get('duration', 0)/60:.1f} minutes")
        st.markdown(f"**💾 File Size:** {meeting.get('file_size', 0)/(1024*1024):.1f} MB")
        
        # Category
        if meeting.get('summary') and meeting['summary'].get('meeting_category'):
            st.markdown(f"**📂 Category:** {meeting['summary']['meeting_category']}")
        
        # Executive summary preview
        if meeting.get('summary') and meeting['summary'].get('executive_summary'):
            summary_preview = meeting['summary']['executive_summary'][:150]
            if len(meeting['summary']['executive_summary']) > 150:
                summary_preview += "..."
            st.markdown(f"**📋 Summary:** {summary_preview}")
        
        # Key metrics
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
        
        with col_metrics1:
            # Action items count
            action_items_count = 0
            if meeting.get('summary') and meeting['summary'].get('action_items'):
                action_items_count = len(meeting['summary']['action_items'])
            st.metric("Action Items", action_items_count)
        
        with col_metrics2:
            # Sentiment
            sentiment_label = "N/A"
            if meeting.get('sentiment') and meeting['sentiment'].get('textblob'):
                sentiment_label = meeting['sentiment']['textblob'].get('label', 'N/A')
            st.metric("Sentiment", sentiment_label)
        
        with col_metrics3:
            # Topics count
            topics_count = 0
            if meeting.get('topics'):
                topics_count = len(meeting['topics'])
            st.metric("Topics", topics_count)
    
    with col2:
        # Action buttons
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        
        # View details button
        if st.button(f"👁️ View Details", key=f"view_{meeting['id']}"):
            st.session_state['selected_meeting_id'] = meeting['id']
            st.success("Meeting selected! Switch to Dashboard to view details.")
        
        # Download transcription
        if meeting.get('transcription'):
            transcript_text = meeting['transcription'].get('text', meeting['transcription']) if isinstance(meeting['transcription'], dict) else meeting['transcription']
            st.download_button(
                label="📥 Download",
                data=transcript_text,
                file_name=f"{meeting['filename']}_transcription.txt",
                mime="text/plain",
                key=f"download_{meeting['id']}"
            )
        
        # Delete button
        if st.button(f"🗑️ Delete", key=f"delete_{meeting['id']}", type="secondary"):
            if st.session_state.get(f"confirm_delete_{meeting['id']}", False):
                if delete_meeting(meeting['id']):
                    st.success("Meeting deleted successfully!")
                    st.rerun()
                else:
                    st.error("Failed to delete meeting")
            else:
                st.session_state[f"confirm_delete_{meeting['id']}"] = True
                st.warning("Click again to confirm deletion")
    
    # Quick insights
    if meeting.get('summary'):
        st.markdown("#### 🔍 Quick Insights")
        
        # Key topics
        if meeting['summary'].get('key_topics'):
            topics_text = ", ".join(meeting['summary']['key_topics'][:5])
            st.markdown(f"**🏷️ Key Topics:** {topics_text}")
        
        # Decisions
        if meeting['summary'].get('decisions'):
            decisions_count = len(meeting['summary']['decisions'])
            st.markdown(f"**✅ Decisions Made:** {decisions_count} decision(s)")
        
        # Action items preview
        if meeting['summary'].get('action_items'):
            st.markdown("**📋 Action Items Preview:**")
            for i, item in enumerate(meeting['summary']['action_items'][:3]):
                if isinstance(item, dict):
                    responsible = item.get('responsible_party', 'Unassigned')
                    st.markdown(f"• {item.get('item', 'N/A')} - *{responsible}*")
                else:
                    st.markdown(f"• {item}")
            
            if len(meeting['summary']['action_items']) > 3:
                st.markdown(f"... and {len(meeting['summary']['action_items']) - 3} more")
