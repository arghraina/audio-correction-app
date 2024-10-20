from flask import Flask, request, render_template, send_file
from google.cloud import speech, texttospeech
import openai
import moviepy.editor as mp
import os

# Set up your Flask app
app = Flask(__name__)

# Set up Google and OpenAI API keys
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_credentials.json' # I DON"T HAVE ACCOUNT IN GOOGLE TEXT-TO-SPEECH or SPEECH-TO-TEXT API's as I am a college student right now.
openai.api_key = '22ec84421ec24230a3638d1b51e3a7dc'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'video_file' not in request.files:
            return "No file uploaded.", 400
        
        video_file = request.files['video_file']
        video_file.save("uploaded_video.mp4")  # Save the uploaded video

        # Process the video file
        transcription = transcribe_audio("uploaded_video.mp4")
        corrected_transcription = correct_transcription(transcription)
        new_audio_path = generate_audio(corrected_transcription)
        output_video_path = replace_audio("uploaded_video.mp4", new_audio_path)

        return send_file(output_video_path, as_attachment=True)

    return render_template('index.html')

def transcribe_audio(video_file):
    video = mp.VideoFileClip(video_file)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path)

    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    
    response = client.recognize(config=config, audio=audio)
    transcription = " ".join([result.alternatives[0].transcript for result in response.results])
    
    return transcription

def correct_transcription(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Correct the following transcription for grammatical mistakes: '{transcription}'"}
        ]
    )
    return response['choices'][0]['message']['content']

def generate_audio(text):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    audio_path = "corrected_audio.wav"
    with open(audio_path, "wb") as out:
        out.write(response.audio_content)

    return audio_path

def replace_audio(video_file, new_audio_file):
    video = mp.VideoFileClip(video_file)
    new_audio = mp.AudioFileClip(new_audio_file)
    final_video = video.set_audio(new_audio)
    output_path = "output_video.mp4"
    final_video.write_videofile(output_path, codec="libx264")
    
    return output_path

if __name__ == '__main__':
    app.run(debug=True)