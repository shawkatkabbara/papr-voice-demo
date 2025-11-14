#!/usr/bin/env python3
"""
Voice recording component for Streamlit using streamlit-audio-recorder
"""

import streamlit as st
from audiorecorder import audiorecorder
import io
import wave

def create_voice_input():
    """Create a voice input component that returns recorded audio"""

    st.markdown("### 🎤 Voice Input")
    st.caption("Click the microphone to start/stop recording")

    # Audio recorder component
    audio = audiorecorder("🎤 Start Recording", "⏹️ Stop Recording")

    if len(audio) > 0:
        # Display audio player for playback
        st.audio(audio.export().read(), format="audio/wav")

        # Convert to bytes for API
        audio_bytes = audio.export().read()

        return audio_bytes

    return None


def audio_bytes_to_wav(audio_bytes: bytes) -> bytes:
    """Convert raw audio bytes to WAV format"""
    # This is already in WAV format from audiorecorder
    return audio_bytes
