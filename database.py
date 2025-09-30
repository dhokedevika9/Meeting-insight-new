import sqlite3
import json
import os
from datetime import datetime
import streamlit as st

DB_PATH = "meetings.db"

def initialize_database():
    """Initialize the SQLite database for storing meeting data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                transcription TEXT,
                summary TEXT,
                sentiment TEXT,
                topics TEXT,
                speakers TEXT,
                knowledge_graph TEXT,
                file_size INTEGER,
                duration REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error initializing database: {e}")

def save_meeting_data(filename, transcription, summary, sentiment, topics, speakers, knowledge_graph, file_size=0, duration=0.0):
    """Save meeting analysis data to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meetings 
            (filename, upload_date, transcription, summary, sentiment, topics, speakers, knowledge_graph, file_size, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            json.dumps(transcription) if transcription else None,
            json.dumps(summary) if summary else None,
            json.dumps(sentiment) if sentiment else None,
            json.dumps(topics) if topics else None,
            json.dumps(speakers) if speakers else None,
            json.dumps(knowledge_graph) if knowledge_graph else None,
            file_size,
            duration
        ))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return meeting_id
    except Exception as e:
        st.error(f"Error saving meeting data: {e}")
        return None

def get_all_meetings():
    """Retrieve all meetings from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM meetings ORDER BY upload_date DESC')
        meetings = cursor.fetchall()
        
        conn.close()
        
        # Convert to list of dictionaries
        meeting_list = []
        for meeting in meetings:
            meeting_dict = {
                'id': meeting[0],
                'filename': meeting[1],
                'upload_date': meeting[2],
                'transcription': json.loads(meeting[3]) if meeting[3] else None,
                'summary': json.loads(meeting[4]) if meeting[4] else None,
                'sentiment': json.loads(meeting[5]) if meeting[5] else None,
                'topics': json.loads(meeting[6]) if meeting[6] else None,
                'speakers': json.loads(meeting[7]) if meeting[7] else None,
                'knowledge_graph': json.loads(meeting[8]) if meeting[8] else None,
                'file_size': meeting[9],
                'duration': meeting[10]
            }
            meeting_list.append(meeting_dict)
        
        return meeting_list
    except Exception as e:
        st.error(f"Error retrieving meetings: {e}")
        return []

def get_meeting_by_id(meeting_id):
    """Retrieve a specific meeting by ID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting = cursor.fetchone()
        
        conn.close()
        
        if meeting:
            return {
                'id': meeting[0],
                'filename': meeting[1],
                'upload_date': meeting[2],
                'transcription': json.loads(meeting[3]) if meeting[3] else None,
                'summary': json.loads(meeting[4]) if meeting[4] else None,
                'sentiment': json.loads(meeting[5]) if meeting[5] else None,
                'topics': json.loads(meeting[6]) if meeting[6] else None,
                'speakers': json.loads(meeting[7]) if meeting[7] else None,
                'knowledge_graph': json.loads(meeting[8]) if meeting[8] else None,
                'file_size': meeting[9],
                'duration': meeting[10]
            }
        return None
    except Exception as e:
        st.error(f"Error retrieving meeting: {e}")
        return None

def delete_meeting(meeting_id):
    """Delete a meeting from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        st.error(f"Error deleting meeting: {e}")
        return False

def search_meetings(query):
    """Search meetings by filename or content."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM meetings 
            WHERE filename LIKE ? OR transcription LIKE ? OR summary LIKE ?
            ORDER BY upload_date DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        meetings = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        meeting_list = []
        for meeting in meetings:
            meeting_dict = {
                'id': meeting[0],
                'filename': meeting[1],
                'upload_date': meeting[2],
                'transcription': json.loads(meeting[3]) if meeting[3] else None,
                'summary': json.loads(meeting[4]) if meeting[4] else None,
                'sentiment': json.loads(meeting[5]) if meeting[5] else None,
                'topics': json.loads(meeting[6]) if meeting[6] else None,
                'speakers': json.loads(meeting[7]) if meeting[7] else None,
                'knowledge_graph': json.loads(meeting[8]) if meeting[8] else None,
                'file_size': meeting[9],
                'duration': meeting[10]
            }
            meeting_list.append(meeting_dict)
        
        return meeting_list
    except Exception as e:
        st.error(f"Error searching meetings: {e}")
        return []
