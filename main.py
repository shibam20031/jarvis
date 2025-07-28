# main.py
import webbrowser
import pyautogui
import time
import urllib.parse
import wikipedia
import requests
from bs4 import BeautifulSoup
import subprocess
import pyttsx3
from pytube import Search
import eel
import threading
import queue
import datetime
import pyjokes
import sys
import re
import speech_recognition as sr

# Initialize Eel
eel.init('web')

# Global variables
speech_queue = queue.Queue()
assistant_active = True
user_name = ''
assistant_name = 'Jarvis'
listening_for_wake_word = True

# TTS Engine with improved initialization
class TTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.configure_voice()
        
    def configure_voice(self):
        voices = self.engine.getProperty('voices')
        try:
            # Try to set a female voice if available
            self.engine.setProperty('voice', voices[0].id)
        except:
            # Fallback to default voice
            pass
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)  # Slightly lower volume
        self.engine.setProperty('pitch', 110)

    def speak(self, text):
        print("Speaking:", text)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)

tts_engine = TTSEngine()

@eel.expose
def speak(text):
    print(f"Assistant: {text}")
    eel.updateResponse(text)
    speech_queue.put(text)

def speech_worker():
    while assistant_active:
        try:
            text = speech_queue.get(timeout=1)
            if text:
                tts_engine.speak(text)
            speech_queue.task_done()
        except queue.Empty:
            continue

@eel.expose
def wish_me():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak(f"Good morning! I'm {assistant_name}. How can I help you?")
    elif 12 <= hour < 18:
        speak(f"Good afternoon! I'm {assistant_name}. How can I help you?")
    else:
        speak(f"Good evening! I'm {assistant_name}. How can I help you?")

@eel.expose
def take_command():
    r = sr.Recognizer()
    r.energy_threshold = 4000  # Increased energy threshold for better detection
    r.dynamic_energy_threshold = True
    
    try:
        with sr.Microphone() as source:
            eel.updateStatus("Listening...")
            print("Listening...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=5, phrase_time_limit=8)

        eel.updateStatus("Recognizing...")
        try:
            query = r.recognize_google(audio, language='en-in').lower()
            eel.updateStatus("Ready")
            print("You said:", query)
            return query
        except sr.UnknownValueError:
            eel.updateStatus("Ready")
            return "none"
        except sr.RequestError as e:
            eel.updateStatus("Ready")
            print("Could not request results; {0}".format(e))
            return "none"
    except Exception as e:
        eel.updateStatus("Ready")
        print("Microphone error:", e)
        return "none"
@eel.expose
def clean_wiki_text(text):
    return re.sub(r'\[\d+\]', '', text).replace('\n', ' ').strip()
@eel.expose
def get_wikipedia_summary(query):
    try:
        # Clean the query by removing command keywords
        original_query = query
        query = query.replace("wikipedia", "").replace("search", "")\
                   .replace("who is", "").replace("what is", "").strip()
        
        if not query:
            speak("Please specify what you'd like me to look up on Wikipedia.")
            return "Please specify what to search on Wikipedia."
        
        # Announce the search with a more natural phrasing
        speak(f"Checking Wikipedia for information about {query}...")
        wikipedia.set_lang("en")
        
        try:
            # Get the summary with more sentences for better context
            summary = wikipedia.summary(query, sentences=3)
            clean_summary = clean_wiki_text(summary)
            
            # Speak the summary in a more natural way
            speak(f"Here's what I found about {query}: {clean_summary}")
            
            # Return a formatted version for display
            return f"Wikipedia: {query}\n\n{clean_summary}"
            
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:3]  # Get first 3 options
            error_msg = (f"There are multiple meanings for {query}. "
                        f"Please be more specific. Options include: {', '.join(options)}")
            speak(error_msg)
            return error_msg
            
        except wikipedia.exceptions.PageError:
            error_msg = f"I couldn't find any Wikipedia article about {query}."
            speak(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Sorry, I encountered an error while searching Wikipedia: {str(e)}"
        speak(error_msg)
        return error_msg
@eel.expose
def play_on_youtube(query):
    try:
        # Clean the query by removing command keywords
        query = query.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
        
        if not query:
            speak("What would you like me to play on YouTube?")
            return "Please specify what to play on YouTube."
            
        # Search for the video
        speak(f"Searching YouTube for {query}...")
        s = Search(query)
        
        if s.results:
            video = s.results[0]
            # Announce the video being played
            speak(f"Playing {video.title} on YouTube")
            webbrowser.open(f"https://youtube.com/watch?v={video.video_id}")
            return f"Playing: {video.title}"
        
        speak("Sorry, I couldn't find any videos matching your request.")
        return "No matching videos found."
        
    except Exception as e:
        error_msg = f"Failed to play YouTube video: {str(e)}"
        speak(error_msg)
        return error_msg
@eel.expose
def search_google(query):
    try:
        # Clean up the query by removing command keywords
        query = query.replace("search", "").replace("on google", "").replace("google", "").strip()
        
        if not query:
            speak("What would you like me to search on Google?")
            return "Please specify what to search on Google."
        
        # Speak that we're performing the search
        speak(f"Searching Google for {query}")
        
        # Create the search URL and open it
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        
        return f"Searching Google for: {query}"
    except Exception as e:
        error_msg = f"Failed to perform Google search: {str(e)}"
        speak(error_msg)
        return error_msg
@eel.expose
def open_application(app_name):
    app_paths = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'outlook': 'outlook.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'firefox': 'firefox.exe'
    }
    try:
        app = app_name.strip().lower()
        if app in app_paths:
            # Speak that we're opening the application
            speak(f"Opening {app}...")
            subprocess.Popen(app_paths[app])
            return f"Opened {app}."
        speak(f"Sorry, I don't recognize the application: {app_name}")
        return f"Application not recognized: {app_name}"
    except Exception as e:
        error_msg = f"Failed to open {app_name}: {str(e)}"
        speak(error_msg)
        return error_msg

def open_website(url, name):
    try:
        webbrowser.open(url)
        return f"Opening {name}"
    except Exception as e:
        return f"Failed to open {name}: {str(e)}"

def get_weather(city="London"):
    try:
        api_key = "d850f7f52bf19300a9eb4b0aa6b80f0d"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data["cod"] != 200:
            return "City not found."
            
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        
        return f"{city} weather: {desc}, Temperature: {temp}°C, Humidity: {humidity}%, Wind: {wind} km/h"
    except Exception as e:
        return f"Could not get weather info: {str(e)}"

def get_news():
    try:
        url = "https://www.bbc.com/news"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.strip() for h in soup.find_all('h3') if h.text.strip()]
        return "Top news:\n" + "\n".join(headlines[:5])
    except Exception as e:
        return f"Couldn't fetch news: {str(e)}"


@eel.expose
def handle_command(command):
    command = command.lower()
    result = None

    # === Time command ===
    if "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        result = f"The current time is {current_time}"

    # === Date command ===
    elif "date" in command:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        result = f"Today's date is {current_date}"

    # === Joke ===
    elif "joke" in command:
        result = pyjokes.get_joke()

    # === Weather ===
    elif "weather" in command:
        city = command.split("in")[-1].strip() if "in" in command else "London"
        result = get_weather(city)

    # === News ===
    elif "news" in command:
        result = get_news()

    # === YouTube play ===
    elif "play" in command and "youtube" in command:
        result = play_on_youtube(command)

    # === Wikipedia ===
    elif "wikipedia" in command or "who is" in command or "what is" in command:
        result = get_wikipedia_summary(command)
        return result  # Already spoken in the function

    # === Website Shortcuts ===
    elif "whatsapp" in command:
        result = open_website("https://web.whatsapp.com", "WhatsApp Web")
    elif "facebook" in command:
        result = open_website("https://www.facebook.com", "Facebook")
    elif "instagram" in command:
        result = open_website("https://www.instagram.com", "Instagram")
    elif "gmail" in command:
        result = open_website("https://mail.google.com", "Gmail")
    elif "twitter" in command:
        result = open_website("https://twitter.com", "Twitter")
    elif "linkedin" in command:
        result = open_website("https://www.linkedin.com", "LinkedIn")
    elif "reddit" in command:
        result = open_website("https://www.reddit.com", "Reddit")
    elif "amazon" in command:
        result = open_website("https://www.amazon.com", "Amazon")
    elif "netflix" in command:
        result = open_website("https://www.netflix.com", "Netflix")
    elif "spotify" in command:
        result = open_website("https://open.spotify.com", "Spotify")
    elif "github" in command:
        result = open_website("https://github.com", "GitHub")

    # === Open website ===
    elif "youtube" in command:
        result = open_website("https://www.youtube.com", "YouTube")
    elif "google" in command:
        result = open_website("https://www.google.com", "Google")

    # === Google Search ===
    elif "search" in command and "google" in command:
        result = search_google(command)

    # === Open Application ===
    elif "open" in command:
        app = command.split("open")[-1].strip()
        result = open_application(app)

    # === Exit command ===
    elif "bye" in command or "exit" in command or "quit" in command:
        global assistant_active
        assistant_active = False
        result = "Goodbye! Have a nice day."
        eel.closeWindow()  # Close the browser window

    # === Unknown command ===
    else:
        result = "Sorry, I didn't understand that. Please try again or say 'help' for a list of commands."

    speak(result)
    return result


def wake_word_detection():
    r = sr.Recognizer()
    r.energy_threshold = 300  # Higher threshold to reduce false positives
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.6

    while assistant_active:
        try:
            with sr.Microphone() as source:
                print("\nListening for wake word...")
                eel.updateStatus("Sleeping... Say 'Jarvis' to activate")
                r.adjust_for_ambient_noise(source, duration=2)
                audio = r.listen(source, timeout=5, phrase_time_limit=4)
                
            try:
                query = r.recognize_google(audio, language='en-in').lower()
                print("Heard:", query)
                
                # Check for multiple wake word variations
                wake_words = [assistant_name.lower(), "jarvis", "hey jarvis", "ok jarvis"]
                if any(wake_word in query for wake_word in wake_words):
                    eel.updateStatus("Wake word detected!")
                    speak("Yes? How can I help you?")
                    
                    # Get command after wake word
                    command = take_command()
                    if command and command != "none":
                        handle_command(command)
                        
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
                
        except Exception as e:
            print("Wake word detection error:", e)
            time.sleep(1)

# Start the application
if __name__ == '__main__':
    try:
        # Start speech worker thread
        speech_thread = threading.Thread(target=speech_worker, daemon=True)
        speech_thread.start()
        
        # Start wake word detection thread
        wake_thread = threading.Thread(target=wake_word_detection, daemon=True)
        wake_thread.start()
        
        # Start the GUI
        eel.start('index.html', size=(900, 700), mode='chrome', 
                 host='localhost', port=8000, shutdown_delay=5.0)
        
    except Exception as e:
        print("Application error:", e)
    finally:
        assistant_active = False
        speech_thread.join(timeout=1)
        wake_thread.join(timeout=1)
        sys.exit()