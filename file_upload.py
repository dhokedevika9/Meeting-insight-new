import streamlit as st
import os
import tempfile
from utils.audio_processor import process_audio_file, get_audio_duration
from utils.ai_analyzer import (
    transcribe_audio, 
    generate_meeting_summary, 
    analyze_sentiment, 
    extract_topics,
    identify_speakers,
    generate_knowledge_connections
)
from utils.database import save_meeting_data

def file_upload_component():
    """Component for uploading and processing meeting files."""
    
    st.header("📁 Upload Meeting Recording")
    st.markdown("Upload your meeting audio or video file to generate AI-powered insights.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an audio or video file",
        type=['mp3', 'wav', 'mp4', 'mov', 'avi', 'm4a'],
        help="Supported formats: MP3, WAV, MP4, MOV, AVI, M4A"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"📊 File size: {uploaded_file.size / (1024*1024):.2f} MB")
        
        # Processing button
        if st.button("🚀 Process Meeting", type="primary"):
            process_meeting_file(uploaded_file)

def process_meeting_file(uploaded_file):
    """Process the uploaded meeting file through the AI pipeline."""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Process audio file
        status_text.text("🔄 Processing audio file...")
        progress_bar.progress(10)
        
        audio_path = process_audio_file(uploaded_file)
        if not audio_path:
            st.error("❌ Failed to process audio file")
            return
        
        # Get file duration
        duration = get_audio_duration(audio_path)
        
        # Step 2: Transcribe audio
        status_text.text("🎤 Transcribing audio (this may take a while)...")
        progress_bar.progress(25)
        
        transcription = transcribe_audio(audio_path)
        if not transcription:
            st.error("❌ Failed to transcribe audio")
            os.unlink(audio_path)
            return
        
        # Step 3: Generate summary
        status_text.text("📝 Generating meeting summary...")
        progress_bar.progress(50)
        
        summary = generate_meeting_summary(transcription['text'])
        if not summary:
            st.error("❌ Failed to generate summary")
            os.unlink(audio_path)
            return
        
        # Step 4: Analyze sentiment
        status_text.text("😊 Analyzing sentiment...")
        progress_bar.progress(65)
        
        sentiment = analyze_sentiment(transcription['text'])
        
        # Step 5: Extract topics
        status_text.text("🏷️ Extracting topics...")
        progress_bar.progress(75)
        
        topics = extract_topics(transcription['text'])
        
        # Step 6: Identify speakers
        status_text.text("👥 Identifying speakers...")
        progress_bar.progress(85)
        
        speakers = identify_speakers(transcription)
        
        # Step 7: Generate knowledge graph
        status_text.text("🕸️ Generating knowledge connections...")
        progress_bar.progress(95)
        
        knowledge_graph = generate_knowledge_connections(summary, topics)
        
        # Step 8: Save to database
        status_text.text("💾 Saving analysis...")
        progress_bar.progress(100)
        
        meeting_id = save_meeting_data(
            filename=uploaded_file.name,
            transcription=transcription,
            summary=summary,
            sentiment=sentiment,
            topics=topics,
            speakers=speakers,
            knowledge_graph=knowledge_graph,
            file_size=uploaded_file.size,
            duration=duration
        )
        
        # Clean up temporary file
        if audio_path:
            os.unlink(audio_path)
        
        if meeting_id:
            status_text.text("✅ Processing complete!")
            st.success("🎉 Meeting processed successfully!")
            
            # Display results preview
            display_processing_results(transcription, summary, sentiment, topics, speakers)
            
            # Button to view in dashboard
            if st.button("📊 View in Dashboard"):
                st.rerun()
        else:
            st.error("❌ Failed to save meeting data")
            
    except Exception as e:
        st.error(f"❌ Error processing meeting: {e}")
        if 'audio_path' in locals() and os.path.exists(audio_path):
            os.unlink(audio_path)

def display_processing_results(transcription, summary, sentiment, topics, speakers):
    """Display a preview of the processing results."""
    
    st.markdown("---")
    st.subheader("📋 Processing Results Preview")
    
    # Transcription preview
    with st.expander("📝 Transcription Preview"):
        transcript_text = transcription['text'][:500]
        st.text(transcript_text + "..." if len(transcription['text']) > 500 else transcript_text)
    
    # Summary
    if summary:
        with st.expander("📊 Meeting Summary", expanded=True):
            st.markdown(f"**Executive Summary:** {summary.get('executive_summary', 'N/A')}")
            
            if summary.get('key_topics'):
                st.markdown("**Key Topics:**")
                for topic in summary['key_topics']:
                    st.markdown(f"• {topic}")
            
            if summary.get('decisions'):
                st.markdown("**Decisions Made:**")
                for decision in summary['decisions']:
                    st.markdown(f"• {decision}")
            
            if summary.get('action_items'):
                st.markdown("**Action Items:**")
                for item in summary['action_items']:
                    if isinstance(item, dict):
                        st.markdown(f"• {item.get('item', 'N/A')} - *{item.get('responsible_party', 'Unassigned')}*")
                    else:
                        st.markdown(f"• {item}")
    
    # Sentiment
    if sentiment:
        with st.expander("😊 Sentiment Analysis"):
            textblob_sentiment = sentiment.get('textblob', {})
            st.markdown(f"**Overall Sentiment:** {textblob_sentiment.get('label', 'N/A')}")
            st.markdown(f"**Polarity Score:** {textblob_sentiment.get('polarity', 0):.2f} (-1 to 1)")
            st.markdown(f"**Subjectivity Score:** {textblob_sentiment.get('subjectivity', 0):.2f} (0 to 1)")
    
    # Topics
    if topics:
        with st.expander("🏷️ Key Topics"):
            for i, topic in enumerate(topics[:3]):
                keywords = ", ".join(topic.get('keywords', [])[:5])
                st.markdown(f"**Topic {i+1}:** {keywords}")
    
    # Speakers
    if speakers and speakers.get('estimated_speakers', 0) > 1:
        with st.expander("👥 Speaker Analysis"):
            st.markdown(f"**Estimated Speakers:** {speakers.get('estimated_speakers', 'Unknown')}")
            st.markdown(f"**Confidence:** {speakers.get('confidence', 0):.1%}")
