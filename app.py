from flask import Flask, request, render_template, redirect, url_for, flash
from find_titles import titles
import os
from pydub import AudioSegment
import ffmpeg
import openai
import math

# Set up OpenAI API key
openai.api_key = 'sk-proj-ZMpKDvb1RyFYblCD8t3TT3BlbkFJR7rzY4oFBN8TRwx8JdRF'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'supersecretkey'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def split_audio_to_segments(input_file, segment_size_mb=10):
    # Load your MP3 file
    audio = AudioSegment.from_mp3(input_file)

    # Calculate the segment duration in milliseconds
    file_size = os.path.getsize(input_file)  # in bytes
    segment_size = segment_size_mb * 1024 * 1024  # Convert MB to bytes

    # Calculate the approximate duration for each segment
    segment_duration = math.ceil((segment_size / file_size) * len(audio))

    # Calculate the number of segments
    num_segments = math.ceil(len(audio) / segment_duration)

    # Extract the file name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    segment_files = []
    
    # Split the file into segments
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, len(audio))

        segment = audio[start_time:end_time]

        # Export each segment to a new file
        segment_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"{base_name}_segment_{i+1}.mp3")
        segment.export(segment_filename, format="mp3")
        
        segment_files.append(segment_filename)
        print(f"Segment {i+1} exported: {start_time} to {end_time} ms as {segment_filename}")
    
    return segment_files

def convert_video_to_wav(video_file):
    try:
        # Extract audio from video file and save as mp3
        mp3_file = video_file.rsplit('.', 1)[0] + ".mp3"
        ffmpeg.input(video_file).output(mp3_file).run(overwrite_output=True)
        
        # Split the MP3 file into 25 MB segments
        segment_files = split_audio_to_segments(mp3_file)
        
        # Convert each segment to WAV and transcribe
        transcription = ""
        for segment_file in segment_files:
            audio = AudioSegment.from_file(segment_file, format="mp3")
            wav_file = segment_file.replace(".mp3", ".wav")
            audio.export(wav_file, format="wav")
            
            # Transcribe the WAV file
            transcription += transcribe_audio_openai(wav_file)
            
            # Clean up files
            os.remove(wav_file)
            os.remove(segment_file)
        
        # Clean up original MP3 file
        os.remove(mp3_file)
        
        return transcription
    except Exception as e:
        print(f"Error converting video to wav: {e}")
        return None

def transcribe_audio_openai(wav_file):
    try:
        with open(wav_file, "rb") as file:
            response = openai.audio.transcriptions.create(
                model="whisper-1", 
                file=file
            )
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def generate_title_and_hashtags(transcription):
    # Prepare the prompt for OpenAI
    prompt = (
        f"Based on the following transcription, generate a suitable title and three hashtags for the video. "
        f"Make sure the title is similar in style and tone to these existing titles: {', '.join(titles)}.\n\n"
        f"Transcription:\n{transcription}\n\n"
        f"Title and Hashtags:"
    )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates video titles and hashtags."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7
    )

    output = response.choices[0].message.content.strip()
    return output

def process_audio_file(video_file):
    transcription = convert_video_to_wav(video_file)
    if not transcription:
        return "Failed to convert video to WAV.", "", ""
    
    output = generate_title_and_hashtags(transcription)
    
    if output:
        # Extract title and hashtags from output
        title, hashtags = output.split('\n', 1)
        return transcription, title, hashtags
    else:
        return "Failed to transcribe audio.", "", ""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith(('.mp4', '.mov')):
            print("ok we're here")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            
            transcription, title, hashtags = process_audio_file(file_path)
            
            os.remove(file_path)
            
            return render_template('index.html', transcription=transcription, title=title, hashtags=hashtags)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
