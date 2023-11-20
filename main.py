from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import soundcard as sc
import soundfile as sf
import numpy as np
import time
import os
import socket
import threading
import keyboard
from chat import TwitchChatBot
import tkinter as tk
from images import start_display_thread, toggle_talking, toggle_reading
from PIL import ImageGrab, ImageEnhance, Image, ImageOps
import pytesseract

#All the listening variables
OUTPUT_FILE_NAME = "out.wav"    # file name.
SAMPLE_RATE = 48000              # [Hz]. sampling rate.
THRESHOLD = 0.005                 # Adjust this threshold based on your requirements.
BUFFER_DURATION = 0.8            # Buffer duration in seconds.


#Pitch shifting variables
input_filename = "output.mp3"
output_filename = "processed_output.mp3"
speed_factor = 1.05
pitch_shift = 1.6

#Put info for your own channel
#Making the bot run
channel_name = ""
bot_nickname = ""
oauth_token = ""
bot = TwitchChatBot(channel_name, bot_nickname, oauth_token)

# Run the bot in a separate thread
threading.Thread(target=bot.run).start()

#Need API key from openAI
api_key = ''
client = OpenAI(api_key=api_key)

#AI_content = """You are a grandpa who is very old and technologically challenged. You are very clueless and get frustrated when things don't make sense. You
#                are pretty bitter and mean from your time you spend in the Vietnam war. You don't like to put up with people who are trying to steal from you.
#                You also have viruses on your computer than you need to get fixed. Also you have 4 google play gift cards of $500 each. You also love to cuss.
#                Keep your responses to 30 words or less."""
current_game = "Fortnite"
AI_content = """You are the minion Otto from the despicable me franchise streaming """ + current_game + """. You will be responding to comments
                from the chat and information from game. Game information will be formatted GAME: information. Chat will be formatted CHAT: username: message.
                Do not include this information in your response (other than the chatters username occasionally). Be extremely sassy and write funny and witty 
                comebacks to chat messages. Keep responses to 30 words or less."""

conversation_history = [
    {"role": "system", "content": AI_content}
]

def respondToText(conversation_history):
  response = client.chat.completions.create(
    model = "gpt-3.5-turbo",
    messages = conversation_history
  )
  conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})
  print(response.choices[0].message.content)
  return response

def text_to_speech(text):
  response = client.audio.speech.create(
    model="tts-1",
    voice="onyx",
    input=text.choices[0].message.content
  )
  return response

def play_audio(spoken):
  spoken.stream_to_file("output.mp3")

  content = spoken.content

  # Save the content as an audio file
  output_file = "output.mp3"
  with open(output_file, "wb") as f:
    f.write(content)

  # Load the audio file using pydub
  audio = AudioSegment.from_mp3(output_file)

  # Play the audio
  #play(audio)

def speech_to_text(audio_path):
  audio_file = open(audio_path, "rb")
  transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file, 
    response_format="text"
  )
  print(transcript)
  return transcript

def is_audio_playing(data, threshold):
    rms = np.sqrt(np.mean(data[:, 0]**2))
    return rms > threshold

#Records the desktop audio with a buffer, starts recording when there's audio above a threshold
#Also super buggy and broken, works for one or two loops max then stops the program
#Not used in Otto Bot tho
def get_audio():
  with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
    # Wait for the sound to start with a buffer
    print("Waiting for sound with buffer...")
    buffer_frames = int(BUFFER_DURATION * SAMPLE_RATE)
    buffer = mic.record(numframes=buffer_frames)

    # Continuously check for audio presence
    print("Monitoring audio...")
    while not is_audio_playing(buffer, THRESHOLD):
        buffer = mic.record(numframes=buffer_frames)
        time.sleep(0.1)  # Sleep for a short duration to avoid excessive CPU usage

    print("Audio detected. Recording...")

    # Record until there's no sound for half a second
    recording = []
    silence_frames = 0
    while silence_frames < SAMPLE_RATE:  # Half-second silence threshold
        data = mic.record(numframes=SAMPLE_RATE)
        if is_audio_playing(data, THRESHOLD):
            recording.extend(data[:, 0])
            silence_frames = 0
        else:
            silence_frames += len(data)

    print("Finished recording.")

    sf.write(file=OUTPUT_FILE_NAME, data=np.array(buffer[:, 0].tolist() + recording), samplerate=SAMPLE_RATE)

#Pitch shifts audio up and speeds up, then plays
def process_audio(input_file, output_file, speed_factor, pitch_shift):
    # Load the audio file
    audio = AudioSegment.from_file(input_file, format="mp3")

    # Speed up the audio
    audio = audio.speedup(playback_speed=speed_factor)

    # Pitch shift the audio
    audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * pitch_shift)
    })

    # Export the processed audio
    audio.export(output_file, format="mp3")

    # Play the processed audio
    play(audio)

def talkAboutGame():
  take_screenshot()
  crop()
  try:
    s = extract_text_with_tolerance()
  except:
    return -1
  
  s = s.replace('°', '0')
  arr = s.split("\n")
  if(len(s) < 2):
    return -1
  hp = arr[1]
  shield = arr[0]
  
  transcript = "GAME : You have " + hp + " HP and " + shield + " shield."
  
  conversation_history.append({"role": "user", "content": transcript})
  text_response = respondToText(conversation_history)
  spoken = text_to_speech(text_response)
  play_audio(spoken)
  toggle_talking()
  process_audio(input_filename, output_filename, speed_factor, pitch_shift)
  toggle_talking()
  return 1

def contains_non_numeric(s):
    return not all(char.isdigit() for char in s)

def take_screenshot(file_path='sc.png'):
    try:
        # Get a screenshot of the entire screen
        screenshot = ImageGrab.grab()

        # Save the screenshot to the specified file path
        screenshot.save(file_path)

        print(f"Screenshot saved as {file_path}")

    except Exception as e:
        print(f"Error taking screenshot: {e}")
        
def crop(input_path='sc.png', output_path='cropped_sc.png'):
    try:
        # Open the image
        image = Image.open(input_path)

        # Get the dimensions of the original image
        width, height = image.size

        # Define the crop percentages
        left_crop = int(width * 0.24)
        top_crop = int(height * 0.870)
        right_crop = int(width * 0.735)
        bottom_crop = int(height * 0.0795)

        # Crop the image
        cropped_image = image.crop((left_crop, top_crop, width - right_crop, height - bottom_crop))

        # Save the cropped image
        cropped_image.save(output_path)

        print(f"Cropped image saved as {output_path}")

    except Exception as e:
        print(f"Error cropping image: {e}")

def extract_text_with_tolerance(image_path='cropped_sc.png', threshold_value=150):
    try:
        # Open the enhanced and grayscale image
        image = Image.open(image_path)

        # Convert the image to grayscale
        grayscale_image = image.convert('L')

        # Apply a binary threshold to the image
        thresholded_image = grayscale_image.point(lambda p: p > threshold_value and 255)
        thresholded_image.save('threshold_image.png')

        # Use pytesseract to extract text from the thresholded image
        extracted_text = pytesseract.image_to_string(thresholded_image, config='--psm 6')

        print("Extracted text with tolerance:")
        print(extracted_text)
        return extracted_text

    except Exception as e:
        print(f"Error extracting text with tolerance: {e}")

#talkAboutGame()

start_display_thread()
toggle_talking()
toggle_reading()
talkAboutGameTimer = 0
#This is set up to run the twitch bot not the scammer bot
try:
  while True:
    #get_audio()
    #transcript = speech_to_text("out.wav")
    #Wait for another chat message if there's none to respond to
    while(len(bot.chat_history) == 0):
      print("no new messages")
      time.sleep(1)
      talkAboutGameTimer += 1
      #Talk about game every 45 seconds he's not talking to chat
      if(talkAboutGameTimer > 60):
        talkAboutGame()
        talkAboutGameTimer = 0
      
    #transcript = input("response: ")
    transcript = "CHAT: " + bot.chat_history[0][0] + ": " + bot.chat_history[0][1]
    bot.chat_history.pop(0)
    
    #If more than 5 messages in the queue, get rid of oldest
    #Prob should put in chat.py but its here so
    while(len(bot.chat_history) > 5):
      bot.chat_history.pop(0)
      
    conversation_history.append({"role": "user", "content": transcript})
    toggle_reading()
    text_response = respondToText(conversation_history)
    spoken = text_to_speech(text_response)
    play_audio(spoken)
    toggle_reading()
    toggle_talking()
    
    process_audio(input_filename, output_filename, speed_factor, pitch_shift)
    toggle_talking()
except KeyboardInterrupt:
  bot.stop()
  print("Keyboard interrupt detected. Exiting loop.")





