import streamlit as st
import os
from components.file_upload import file_upload_component
from components.dashboard import dashboard_component
from components.meeting_history import meeting_history_component
from components.knowledge_graph import knowledge_graph_component
from utils.database import initialize_database, get_all_meetings

# Page configuration
st.set_page_config(
    page_title="Meeting AI Analyzer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
initialize_database()

# Main title
st.title("🎙️ Meeting AI Analyzer")
st.markdown("Process pre-recorded meeting audio/video files to generate AI-powered transcriptions, summaries, and insights.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["Upload & Process", "Dashboard", "Meeting History", "Knowledge Graph"]
)

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# Page routing
if page == "Upload & Process":
    file_upload_component()
elif page == "Dashboard":
    dashboard_component()
elif page == "Meeting History":
    meeting_history_component()
elif page == "Knowledge Graph":
    knowledge_graph_component()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("💡 **Tips:**")
st.sidebar.markdown("- Supported formats: MP4, WAV, MP3, MOV, AVI")
st.sidebar.markdown("- For best results, use clear audio recordings")
st.sidebar.markdown("- Processing time depends on file length")
