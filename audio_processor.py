import os
import tempfile
import subprocess
from pydub import AudioSegment
import magic
import streamlit as st

def detect_file_type(file_path):
    """Detect the MIME type of a file using python-magic."""
    try:
        mime = magic.from_file(file_path, mime=True)
        return mime
    except Exception as e:
        st.error(f"Error detecting file type: {e}")
        return None

def convert_to_wav(input_path, output_path):
    """Convert audio/video file to WAV format using FFmpeg."""
    try:
        # Use FFmpeg to convert to WAV
        cmd = [
            'ffmpeg', '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
            
        return True
    except Exception as e:
        st.error(f"Error converting file: {e}")
        return False

def process_audio_file(uploaded_file):
    """Process uploaded audio/video file and prepare it for transcription."""
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_input:
            temp_input.write(uploaded_file.read())
            temp_input_path = temp_input.name
        
        # Detect file type
        mime_type = detect_file_type(temp_input_path)
        
        # Check if file is supported
        supported_types = [
            'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-wav',
            'video/mp4', 'video/quicktime', 'video/x-msvideo'
        ]
        
        if not mime_type or mime_type not in supported_types:
            os.unlink(temp_input_path)
            raise Exception(f"Unsupported file type: {mime_type}")
        
        # Convert to WAV if needed
        temp_output_path = temp_input_path.replace(temp_input_path.split('.')[-1], 'wav')
        
        if mime_type.startswith('video/') or mime_type != 'audio/wav':
            success = convert_to_wav(temp_input_path, temp_output_path)
            if not success:
                os.unlink(temp_input_path)
                raise Exception("Failed to convert file to WAV format")
        else:
            temp_output_path = temp_input_path
        
        # Clean up input file if different from output
        if temp_input_path != temp_output_path:
            os.unlink(temp_input_path)
        
        return temp_output_path
        
    except Exception as e:
        st.error(f"Error processing audio file: {e}")
        return None

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    try:
        audio = AudioSegment.from_wav(file_path)
        return len(audio) / 1000.0  # Convert milliseconds to seconds
    except Exception as e:
        st.error(f"Error getting audio duration: {e}")
        return 0

def split_audio_for_processing(file_path, chunk_duration_ms=10*60*1000):
    """Split audio file into chunks for processing large files."""
    try:
        audio = AudioSegment.from_wav(file_path)
        chunks = []
        
        # Split into chunks
        for i in range(0, len(audio), chunk_duration_ms):
            chunk = audio[i:i + chunk_duration_ms]
            
            # Create temporary file for chunk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_chunk:
                chunk.export(temp_chunk.name, format="wav")
                chunks.append(temp_chunk.name)
        
        return chunks
    except Exception as e:
        st.error(f"Error splitting audio: {e}")
        return []
