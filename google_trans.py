import os
from pydub import AudioSegment
import ffmpeg
import openai

# Set up OpenAI API key
openai.api_key = 'sk-proj-ZMpKDvb1RyFYblCD8t3TT3BlbkFJR7rzY4oFBN8TRwx8JdRF'

def convert_video_to_wav(video_file):
    try:
        # Extract audio from video file and save as mp3
        mp3_file = video_file.rsplit('.', 1)[0] + ".mp3"
        ffmpeg.input(video_file).output(mp3_file).run(overwrite_output=True)
        
        # Convert mp3 to wav
        audio = AudioSegment.from_file(mp3_file, format="mp3")
        wav_file = mp3_file.replace(".mp3", ".wav")
        audio.export(wav_file, format="wav")
        
        # Clean up mp3 file
        os.remove(mp3_file)
        
        return wav_file
    except Exception as e:
        print(f"Error converting video to wav: {e}")
        return None

def transcribe_audio_openai(wav_file):
    try:
        with open(wav_file, "rb") as file:
            transcription = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=file
            )
        return transcription.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def process_audio_file(video_file):
    wav_file = convert_video_to_wav(video_file)
    if not wav_file:
        return "Failed to convert video to WAV."
    
    transcription = transcribe_audio_openai(wav_file)
    
    # Clean up temporary files
    os.remove(wav_file)
    
    return transcription

# Replace with the path to your video file
video_path = r"C:\Users\akenn\OneDrive\Desktop\POC Coding\Conner Brown.mp4"

# Process the audio file and get the transcription
transcription = process_audio_file(video_path)
print("Transcription:", transcription)
