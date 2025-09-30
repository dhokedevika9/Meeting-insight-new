import os
import json
import tempfile
from openai import OpenAI
import streamlit as st
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Initialize OpenAI client for Whisper transcription
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Groq client for fast text analysis
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1") if GROQ_API_KEY else None

# Use Groq if available, otherwise fall back to OpenAI
analysis_client = groq_client if groq_client else openai_client
analysis_model = "llama-3.3-70b-versatile" if groq_client else "gpt-4o"

def transcribe_audio(audio_file_path):
    """Transcribe audio file using OpenAI Whisper."""
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        return {
            'text': response.text,
            'segments': getattr(response, 'segments', []),
            'language': getattr(response, 'language', 'unknown')
        }
    except Exception as e:
        st.error(f"Error transcribing audio: {e}")
        return None

def generate_meeting_summary(transcription_text):
    """Generate comprehensive meeting summary using GPT-5."""
    try:
        prompt = f"""
        Analyze the following meeting transcription and provide a comprehensive summary in JSON format.
        
        Please include:
        1. Executive summary (2-3 sentences)
        2. Key topics discussed (list)
        3. Decisions made (list)
        4. Action items with responsible parties if mentioned (list)
        5. Important quotes or statements (list)
        6. Meeting category (e.g., "Quarterly Review", "Project Brainstorm", "Client Call", etc.)
        
        Transcription:
        {transcription_text}
        
        Respond with valid JSON in this format:
        {{
            "executive_summary": "string",
            "key_topics": ["topic1", "topic2"],
            "decisions": ["decision1", "decision2"],
            "action_items": [
                {{"item": "action description", "responsible_party": "person or team"}},
            ],
            "important_quotes": ["quote1", "quote2"],
            "meeting_category": "category"
        }}
        """
        
        response = analysis_client.chat.completions.create(
            model=analysis_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        return None
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

def analyze_sentiment(text):
    """Analyze sentiment of the meeting transcription."""
    try:
        # Use TextBlob for basic sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Convert to more readable format
        if polarity > 0.1:
            sentiment_label = "Positive"
        elif polarity < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        # Use GPT-5 for more detailed sentiment analysis
        prompt = f"""
        Analyze the emotional tone and sentiment of this meeting transcription.
        Identify specific moments that were particularly positive, negative, or contentious.
        
        Provide analysis in JSON format:
        {{
            "overall_sentiment": "positive/negative/neutral",
            "confidence": 0.0-1.0,
            "positive_moments": ["moment1", "moment2"],
            "negative_moments": ["moment1", "moment2"],
            "contentious_topics": ["topic1", "topic2"],
            "emotional_highlights": ["highlight1", "highlight2"]
        }}
        
        Transcription:
        {text[:2000]}...
        """
        
        response = analysis_client.chat.completions.create(
            model=analysis_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        ai_sentiment = json.loads(content) if content else {}
        
        return {
            'textblob': {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'label': sentiment_label
            },
            'ai_analysis': ai_sentiment
        }
    except Exception as e:
        st.error(f"Error analyzing sentiment: {e}")
        return None

def extract_topics(text, num_topics=5):
    """Extract topics using Latent Dirichlet Allocation."""
    try:
        # Preprocess text
        text_clean = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        
        # Vectorize text
        vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        text_vectorized = vectorizer.fit_transform([text_clean])
        
        # Apply LDA
        lda = LatentDirichletAllocation(
            n_components=min(num_topics, 5),
            random_state=42
        )
        lda.fit(text_vectorized)
        
        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(lda.components_):
            top_features_idx = topic.argsort()[-10:][::-1]
            top_features = [feature_names[i] for i in top_features_idx]
            topics.append({
                'id': topic_idx,
                'keywords': top_features[:5],
                'weight': float(topic.max())
            })
        
        return topics
    except Exception as e:
        st.error(f"Error extracting topics: {e}")
        return []

def identify_speakers(transcription_data):
    """Attempt to identify different speakers in the transcription."""
    try:
        if 'segments' in transcription_data and transcription_data['segments']:
            # Use GPT-5 to analyze speaker patterns
            text = transcription_data['text']
            
            prompt = f"""
            Analyze this meeting transcription and identify different speakers.
            Look for patterns like:
            - Changes in speaking style
            - Direct address ("John, what do you think?")
            - Self-identification ("I think...", "In my opinion...")
            
            Provide analysis in JSON format:
            {{
                "estimated_speakers": 2-5,
                "speaker_segments": [
                    {{"text": "segment text", "speaker": "Speaker A/B/C"}},
                ],
                "confidence": 0.0-1.0
            }}
            
            Transcription:
            {text[:2000]}...
            """
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {"estimated_speakers": 1, "speaker_segments": [], "confidence": 0.1}
        
        return {"estimated_speakers": 1, "speaker_segments": [], "confidence": 0.1}
    except Exception as e:
        st.error(f"Error identifying speakers: {e}")
        return {"estimated_speakers": 1, "speaker_segments": [], "confidence": 0.1}

def generate_knowledge_connections(summary_data, topics):
    """Generate connections between topics for knowledge graph."""
    try:
        prompt = f"""
        Based on the meeting summary and topics, identify relationships and connections between different concepts.
        
        Meeting Summary: {json.dumps(summary_data)}
        Topics: {json.dumps(topics)}
        
        Create a knowledge graph structure in JSON format:
        {{
            "nodes": [
                {{"id": "node_id", "label": "node_label", "type": "topic/decision/action/person", "weight": 1-10}},
            ],
            "edges": [
                {{"source": "node_id1", "target": "node_id2", "relationship": "relates_to/caused_by/assigned_to", "weight": 1-10}},
            ]
        }}
        """
        
        response = analysis_client.chat.completions.create(
            model=analysis_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        return {"nodes": [], "edges": []}
    except Exception as e:
        st.error(f"Error generating knowledge connections: {e}")
        return {"nodes": [], "edges": []}
