from flask import Flask, request, render_template, redirect, url_for, flash
from find_titles import titles
import os
from pydub import AudioSegment
import ffmpeg
import openai

# Set up OpenAI API key
openai.api_key = 'sk-proj-ZMpKDvb1RyFYblCD8t3TT3BlbkFJR7rzY4oFBN8TRwx8JdRF'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'supersecretkey'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    wav_file = convert_video_to_wav(video_file)
    if not wav_file:
        return "Failed to convert video to WAV.", "", ""
    
    transcription = transcribe_audio_openai(wav_file)
    
    # Clean up temporary files
    os.remove(wav_file)
    
    if transcription:
        output = generate_title_and_hashtags(transcription)
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
