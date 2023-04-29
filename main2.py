import openai
import asyncio      #take the user input with reverse Engineered EdgeGPT
import whisper      #transform voice input to text works with ffmpeg library
import pyttsx3
import pyaudio
#import boto3
import os
import pydub
#import ffmpeg       #to get audio input
from pydub import playback
from pydub import AudioSegment
import speech_recognition as sr     #record microphone input
import json
#import EdgeGPT
from EdgeGPT import Chatbot, ConversationStyle

# Initialize the OpenAI API
openai.api_key = "APIKEY"

#Initialise the text to speech engine from pyttsx3
engine = pyttsx3.init()

# Create a recognizer object and wake word variables
recognizer = sr.Recognizer()
BING_WAKE_WORD = "bing"     #change here, the wake word that activate the microphone 
GPT_WAKE_WORD = "gpt"

def get_wake_word(phrase):      #check if wake is within voice input
    if BING_WAKE_WORD in phrase.lower():
        return BING_WAKE_WORD
    elif GPT_WAKE_WORD in phrase.lower():
        return GPT_WAKE_WORD
    else:
        return None

#def synthesize_speech(text, output_filename):       #AWS text to speech file
#    polly = boto3.client('polly', region_name='eu-west-2')
#    response = polly.synthesize_speech(
#        Text=text,
#        OutputFormat='mp3',
#        VoiceId='Brian',
#        Engine='neural'
#    )
#
#    with open(output_filename, 'wb') as f:
#        f.write(response['AudioStream'].read())

def transcribe_audio_to_text(file):  #file is the audio text to transcribe into text after the wake word
     with sr.Microphone(file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except:
        print('Skipping unknown error')



def play_audio(file):       #speechfile from Polly AWS
    sound = pydub.AudioSegment.from_file(file, format="mp3")
    playback.play(sound)

async def main():
    while True:
        #LISTENING TO MICROPHONE AND CONVERTING AUDIO TO TEXT
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Waiting for wake words 'bing' or 'gpt'...")
            while True:
                audio = recognizer.listen(source)
                try:
                    with open("audio.wav", "wb") as f:
                        f.write(audio.get_wav_data())
                    # Use the preloaded tiny_model
                    model = whisper.load_model("tiny")
                    result = model.transcribe("audio.wav", fp16=False)
                    phrase = result["text"]
                    print(f"You said: {phrase}")
                
                    wake_word = get_wake_word(phrase)
                    if wake_word is not None:
                        break
                    else:
                        print("Not a wake word. Try again.")
                except Exception as e:
                    print("Error transcribing audio: {0}".format(e))
                    continue

            print("What can I help you with? Selfishark...")      # call the synthesise voice to speak and request the user prompt when it hear the wake world
            synthesize_speech('What can I help you with?', 'response.mp3')  # verbally request user prompt after hearing wake world
            play_audio('response.mp3')  # response after wake world
            audio = recognizer.listen(source)

            try:
                with open("audio_prompt.wav", "wb") as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model("base")
                result = model.transcribe("audio_prompt.wav", fp16=False)       ##HERE
                user_input = result["text"]
                print(f"You said: {user_input}")
            except Exception as e:
                print("Error transcribing audio: {0}".format(e))
                continue

            if wake_word == BING_WAKE_WORD:
                with open('./cookies.json', 'r') as f:
                    cookies = json.load(f)
                bot = Chatbot(cookies=cookies)
                response = await bot.ask(prompt=input("What can I help you with, today?"), conversation_style=ConversationStyle.creative)
        
                for message in response["item"]["messages"]:
                    if message["author"] == "bot":
                        bot_response = message["text"]
        
                # Select only the bot response from the response dictionary
               # for message in response ["item"]["messages"]:
                #    if message["author"] == "bot":
                #        bot_response = message["text"]

            else:
                # Send prompt to GPT-3.5-turbo API
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content":
                        "You are a helpful assistant."},
                        {"role": "user", "content": user_input},
                    ],
                    temperature=0.5,
                    max_tokens=150,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    n=1,
                    stop=["\nUser:"],
                )

                bot_response = response["choices"][0]["message"]["content"]

            print("Bot's response:", bot_response)
            synthesize_speech(bot_response, 'response.mp3') #Speak response from wake work ()
            play_audio('response.mp3')  #play audio response
            #await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
	
