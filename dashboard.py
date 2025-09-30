import streamlit as st
from utils.database import get_all_meetings
from utils.visualization import (
    create_sentiment_timeline,
    create_topic_distribution,
    create_meeting_analytics_summary,
    create_action_items_chart,
    create_sentiment_comparison
)

def dashboard_component():
    """Main dashboard component displaying meeting insights."""
    
    st.header("📊 Meeting Analytics Dashboard")
    
    # Get all meetings
    meetings = get_all_meetings()
    
    if not meetings:
        st.info("📭 No meetings processed yet. Upload a meeting recording to get started!")
        return
    
    # Overview metrics
    st.subheader("📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Meetings", len(meetings))
    
    with col2:
        total_duration = sum(m.get('duration', 0) for m in meetings)
        st.metric("Total Duration", f"{total_duration/60:.1f} min")
    
    with col3:
        total_action_items = sum(
            len(m.get('summary', {}).get('action_items', [])) 
            for m in meetings if m.get('summary')
        )
        st.metric("Action Items", total_action_items)
    
    with col4:
        avg_sentiment = sum(
            m.get('sentiment', {}).get('textblob', {}).get('polarity', 0) 
            for m in meetings if m.get('sentiment')
        ) / len(meetings) if meetings else 0
        sentiment_emoji = "😊" if avg_sentiment > 0.1 else "😐" if avg_sentiment > -0.1 else "😟"
        st.metric("Avg Sentiment", f"{sentiment_emoji} {avg_sentiment:.2f}")
    
    # Meeting selection
    st.subheader("📋 Meeting Details")
    
    if meetings:
        # Meeting selector
        meeting_options = [f"{m['filename']} ({m['upload_date']})" for m in meetings]
        selected_meeting_idx = st.selectbox(
            "Select a meeting to view details:",
            range(len(meeting_options)),
            format_func=lambda x: meeting_options[x]
        )
        
        selected_meeting = meetings[selected_meeting_idx]
        display_meeting_details(selected_meeting)
    
    # Analytics section
    st.subheader("📊 Analytics")
    
    # Create tabs for different analytics
    tab1, tab2, tab3 = st.tabs(["📈 Sentiment Analysis", "🏷️ Topic Trends", "✅ Action Items"])
    
    with tab1:
        # Sentiment comparison across meetings
        sentiment_fig = create_sentiment_comparison(meetings)
        if sentiment_fig:
            st.plotly_chart(sentiment_fig, use_container_width=True)
        else:
            st.info("No sentiment data available for visualization.")
    
    with tab2:
        # Meeting categories
        analytics_fig = create_meeting_analytics_summary(meetings)
        if analytics_fig:
            st.plotly_chart(analytics_fig, use_container_width=True)
        else:
            st.info("No category data available for visualization.")
    
    with tab3:
        # Action items over time
        action_items_fig = create_action_items_chart(meetings)
        if action_items_fig:
            st.plotly_chart(action_items_fig, use_container_width=True)
        else:
            st.info("No action items data available for visualization.")

def display_meeting_details(meeting):
    """Display detailed information for a selected meeting."""
    
    # Meeting header
    st.markdown(f"### 📁 {meeting['filename']}")
    st.markdown(f"**Date:** {meeting['upload_date']}")
    st.markdown(f"**Duration:** {meeting.get('duration', 0)/60:.1f} minutes")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Summary", 
        "📄 Transcription", 
        "😊 Sentiment", 
        "🏷️ Topics", 
        "👥 Speakers"
    ])
    
    with tab1:
        display_summary_tab(meeting)
    
    with tab2:
        display_transcription_tab(meeting)
    
    with tab3:
        display_sentiment_tab(meeting)
    
    with tab4:
        display_topics_tab(meeting)
    
    with tab5:
        display_speakers_tab(meeting)

def display_summary_tab(meeting):
    """Display meeting summary information."""
    summary = meeting.get('summary')
    
    if not summary:
        st.info("No summary available for this meeting.")
        return
    
    # Executive summary
    if summary.get('executive_summary'):
        st.markdown("#### 📋 Executive Summary")
        st.markdown(summary['executive_summary'])
    
    # Meeting category
    if summary.get('meeting_category'):
        st.markdown(f"#### 📂 Category: {summary['meeting_category']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Key topics
        if summary.get('key_topics'):
            st.markdown("#### 🔑 Key Topics")
            for topic in summary['key_topics']:
                st.markdown(f"• {topic}")
        
        # Decisions
        if summary.get('decisions'):
            st.markdown("#### ✅ Decisions Made")
            for decision in summary['decisions']:
                st.markdown(f"• {decision}")
    
    with col2:
        # Action items
        if summary.get('action_items'):
            st.markdown("#### 📋 Action Items")
            for item in summary['action_items']:
                if isinstance(item, dict):
                    responsible = item.get('responsible_party', 'Unassigned')
                    st.markdown(f"• **{item.get('item', 'N/A')}** - *{responsible}*")
                else:
                    st.markdown(f"• {item}")
        
        # Important quotes
        if summary.get('important_quotes'):
            st.markdown("#### 💬 Important Quotes")
            for quote in summary['important_quotes']:
                st.markdown(f"> {quote}")

def display_transcription_tab(meeting):
    """Display meeting transcription."""
    transcription = meeting.get('transcription')
    
    if not transcription:
        st.info("No transcription available for this meeting.")
        return
    
    # Transcription text
    st.markdown("#### 📄 Full Transcription")
    
    # Show language if available
    if isinstance(transcription, dict) and transcription.get('language'):
        st.markdown(f"**Language:** {transcription['language']}")
    
    # Show transcription text
    transcript_text = transcription.get('text', transcription) if isinstance(transcription, dict) else transcription
    
    # Text area for easy reading and copying
    st.text_area(
        "Transcription:",
        transcript_text,
        height=400,
        help="You can copy this text for external use"
    )
    
    # Download button
    st.download_button(
        label="📥 Download Transcription",
        data=transcript_text,
        file_name=f"{meeting['filename']}_transcription.txt",
        mime="text/plain"
    )

def display_sentiment_tab(meeting):
    """Display sentiment analysis results."""
    sentiment = meeting.get('sentiment')
    
    if not sentiment:
        st.info("No sentiment analysis available for this meeting.")
        return
    
    # TextBlob sentiment
    if 'textblob' in sentiment:
        textblob_data = sentiment['textblob']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Sentiment", textblob_data.get('label', 'N/A'))
        
        with col2:
            polarity = textblob_data.get('polarity', 0)
            st.metric("Polarity", f"{polarity:.2f}", help="Range: -1 (negative) to 1 (positive)")
        
        with col3:
            subjectivity = textblob_data.get('subjectivity', 0)
            st.metric("Subjectivity", f"{subjectivity:.2f}", help="Range: 0 (objective) to 1 (subjective)")
    
    # AI sentiment analysis
    if 'ai_analysis' in sentiment:
        ai_data = sentiment['ai_analysis']
        
        st.markdown("#### 🤖 AI Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if ai_data.get('positive_moments'):
                st.markdown("**😊 Positive Moments:**")
                for moment in ai_data['positive_moments']:
                    st.markdown(f"• {moment}")
            
            if ai_data.get('contentious_topics'):
                st.markdown("**⚠️ Contentious Topics:**")
                for topic in ai_data['contentious_topics']:
                    st.markdown(f"• {topic}")
        
        with col2:
            if ai_data.get('negative_moments'):
                st.markdown("**😟 Negative Moments:**")
                for moment in ai_data['negative_moments']:
                    st.markdown(f"• {moment}")
            
            if ai_data.get('emotional_highlights'):
                st.markdown("**🎭 Emotional Highlights:**")
                for highlight in ai_data['emotional_highlights']:
                    st.markdown(f"• {highlight}")
    
    # Sentiment timeline visualization
    sentiment_timeline = create_sentiment_timeline(sentiment)
    if sentiment_timeline:
        st.plotly_chart(sentiment_timeline, use_container_width=True)

def display_topics_tab(meeting):
    """Display topic analysis results."""
    topics = meeting.get('topics')
    
    if not topics:
        st.info("No topic analysis available for this meeting.")
        return
    
    st.markdown("#### 🏷️ Identified Topics")
    
    # Topic visualization
    topic_fig = create_topic_distribution(topics)
    if topic_fig:
        st.plotly_chart(topic_fig, use_container_width=True)
    
    # Topic details
    for i, topic in enumerate(topics):
        with st.expander(f"Topic {i+1}: {', '.join(topic.get('keywords', [])[:3])}"):
            st.markdown(f"**Keywords:** {', '.join(topic.get('keywords', []))}")
            st.markdown(f"**Relevance Score:** {topic.get('weight', 0):.3f}")

def display_speakers_tab(meeting):
    """Display speaker analysis results."""
    speakers = meeting.get('speakers')
    
    if not speakers:
        st.info("No speaker analysis available for this meeting.")
        return
    
    st.markdown("#### 👥 Speaker Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Estimated Speakers", speakers.get('estimated_speakers', 'Unknown'))
    
    with col2:
        confidence = speakers.get('confidence', 0)
        st.metric("Confidence", f"{confidence:.1%}")
    
    # Speaker segments
    if speakers.get('speaker_segments'):
        st.markdown("#### 🗣️ Speaker Segments")
        
        for i, segment in enumerate(speakers['speaker_segments'][:10]):  # Show first 10 segments
            with st.expander(f"{segment.get('speaker', 'Unknown Speaker')} - Segment {i+1}"):
                st.markdown(segment.get('text', 'No text available'))
    else:
        st.info("No detailed speaker segments available.")
