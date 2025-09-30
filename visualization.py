import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

def create_sentiment_timeline(sentiment_data, meeting_duration=None):
    """Create a timeline visualization of sentiment throughout the meeting."""
    try:
        if not sentiment_data or 'ai_analysis' not in sentiment_data:
            return None
        
        # Create sample timeline data based on sentiment analysis
        ai_data = sentiment_data['ai_analysis']
        textblob_data = sentiment_data['textblob']
        
        # Generate timeline points
        timeline_points = []
        
        # Add positive moments
        for i, moment in enumerate(ai_data.get('positive_moments', [])):
            timeline_points.append({
                'time': i * 5,  # Every 5 minutes
                'sentiment': 0.7,
                'moment': moment,
                'type': 'Positive'
            })
        
        # Add negative moments
        for i, moment in enumerate(ai_data.get('negative_moments', [])):
            timeline_points.append({
                'time': (i + 1) * 7,  # Offset timing
                'sentiment': -0.5,
                'moment': moment,
                'type': 'Negative'
            })
        
        if not timeline_points:
            # Create a simple overall sentiment point
            timeline_points.append({
                'time': 0,
                'sentiment': textblob_data['polarity'],
                'moment': f"Overall: {textblob_data['label']}",
                'type': textblob_data['label']
            })
        
        df = pd.DataFrame(timeline_points)
        
        fig = px.scatter(
            df, 
            x='time', 
            y='sentiment',
            color='type',
            hover_data=['moment'],
            title='Sentiment Timeline',
            labels={'time': 'Time (minutes)', 'sentiment': 'Sentiment Score'}
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(height=400)
        
        return fig
    except Exception as e:
        st.error(f"Error creating sentiment timeline: {e}")
        return None

def create_topic_distribution(topics):
    """Create a visualization of topic distribution."""
    try:
        if not topics:
            return None
        
        df = pd.DataFrame(topics)
        df['topic_label'] = df['keywords'].apply(lambda x: ', '.join(x[:3]))
        
        fig = px.bar(
            df,
            x='topic_label',
            y='weight',
            title='Topic Distribution',
            labels={'topic_label': 'Topics', 'weight': 'Relevance Score'}
        )
        
        fig.update_xaxes(tickangle=45)
        fig.update_layout(height=400)
        
        return fig
    except Exception as e:
        st.error(f"Error creating topic distribution: {e}")
        return None

def create_meeting_analytics_summary(meetings_data):
    """Create summary analytics for all meetings."""
    try:
        if not meetings_data:
            return None
        
        df = pd.DataFrame(meetings_data)
        
        # Meeting categories distribution
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            
            fig_categories = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title='Meeting Categories Distribution'
            )
            
            return fig_categories
        
        return None
    except Exception as e:
        st.error(f"Error creating analytics summary: {e}")
        return None

def create_action_items_chart(meetings_data):
    """Create visualization of action items over time."""
    try:
        if not meetings_data:
            return None
        
        # Extract action items count per meeting
        action_items_data = []
        for meeting in meetings_data:
            if 'summary' in meeting and 'action_items' in meeting['summary']:
                action_items_data.append({
                    'date': meeting.get('upload_date', datetime.now().strftime('%Y-%m-%d')),
                    'filename': meeting['filename'],
                    'action_items_count': len(meeting['summary']['action_items'])
                })
        
        if not action_items_data:
            return None
        
        df = pd.DataFrame(action_items_data)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = px.bar(
            df.sort_values('date'),
            x='date',
            y='action_items_count',
            title='Action Items per Meeting',
            labels={'date': 'Date', 'action_items_count': 'Number of Action Items'},
            hover_data=['filename']
        )
        
        fig.update_layout(height=400)
        
        return fig
    except Exception as e:
        st.error(f"Error creating action items chart: {e}")
        return None

def create_sentiment_comparison(meetings_data):
    """Create sentiment comparison across meetings."""
    try:
        if not meetings_data:
            return None
        
        sentiment_data = []
        for meeting in meetings_data:
            if 'sentiment' in meeting and 'textblob' in meeting['sentiment']:
                sentiment_data.append({
                    'filename': meeting['filename'][:20] + '...' if len(meeting['filename']) > 20 else meeting['filename'],
                    'polarity': meeting['sentiment']['textblob']['polarity'],
                    'subjectivity': meeting['sentiment']['textblob']['subjectivity'],
                    'label': meeting['sentiment']['textblob']['label']
                })
        
        if not sentiment_data:
            return None
        
        df = pd.DataFrame(sentiment_data)
        
        fig = px.scatter(
            df,
            x='polarity',
            y='subjectivity',
            color='label',
            hover_data=['filename'],
            title='Meeting Sentiment Analysis',
            labels={
                'polarity': 'Sentiment Polarity (Negative ← → Positive)',
                'subjectivity': 'Subjectivity (Objective ← → Subjective)'
            }
        )
        
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
        fig.update_layout(height=400)
        
        return fig
    except Exception as e:
        st.error(f"Error creating sentiment comparison: {e}")
        return None
