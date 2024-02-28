import openai
import speech_recognition as sr
from gtts import gTTS
import pygame
from datetime import datetime
import os
import threading
import requests
from googleapiclient.discovery import build
from pytube import YouTube
import vlc

openai.api_key = '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'
API_KEY = "AIzaSyAy4ZTo98sPZGodWTQNWLhqJJsqzDEdc-E"

recognizer = sr.Recognizer()

welcome_message = "System Online!"
Activated_message = "Hey wie kann ich helfen?"

activation_phrase = "hey James"

def process_voice_input():
    with sr.Microphone() as source:
        print("Warte auf Aktivierung...")
        audio = recognizer.listen(source)

        try:
            print("Aktiviert... Spracherkennung läuft...")
            user_input = recognizer.recognize_google(audio, language='de-DE')
            print("Du: ", user_input)
            return user_input
        except sr.UnknownValueError:
            print("Entschuldigung, ich konnte dich nicht verstehen.")
            return None
        except sr.RequestError as e:
            print("Fehler bei der Spracherkennung; {0}".format(e))
            return None

def chat(message):
    if "openai" in message.lower():
        return "Network Error 300. Bitte Backend neu starten."

    if 'uhrzeit' in message.lower() or ('wie' in message.lower() and 'spät' in message.lower()):
        current_time = datetime.now().strftime("%H:%M")
        return f"Es ist {current_time} Uhr."

    if 'wie ist das wetter' in message.lower():
        location = get_user_location()
        if location:
            weather_data = get_weather_data(location['latitude'], location['longitude'])
            if weather_data:
                return format_weather_response(weather_data)
            else:
                return "Es gab ein Problem beim Abrufen der Wetterdaten."
        else:
            return "Es gab ein Problem beim Abrufen des Standorts."

    if 'spiele' in message.lower():
        split_message = message.split("spiele", 1)
        if len(split_message) > 1:
            query = split_message[1].strip()
            # Check for "ab" at the end of the query and trim if present
            if query.endswith("ab"):
                query = query[:-2].strip()
            video_url = search_youtube_video(query)
            if video_url:
                audio_file = download_youtube_audio(video_url)
                play_local_audio(audio_file)
                return "Das Video wird abgespielt."
            else:
                return "Das Video konnte nicht gefunden werden."
        else:
            return "Bitte geben Sie den Titel des Videos an, das Sie abspielen möchten."

    messages = [{"role": "system", "content": "Du bist der persönliche assistent von Matti dein name ist NINA(Neural Intelligent Navigation Assistant)"}]
    messages.append({"role": "user", "content": message})

    try:
        chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        reply = chat.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        return reply
    except openai.error.APIError as e:
        return f"API-Fehler: {e}"

def speak(text):
    tts = gTTS(text=text, lang='de', slow=False)
    output_file = "output.mp3"
    tts.save(output_file)
    pygame.mixer.init()
    pygame.mixer.music.load(output_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    os.remove(output_file)

def start_standby_timer():
    global last_input_time
    last_input_time = datetime.now()
    standby_thread = threading.Timer(30, standby_mode)
    standby_thread.start()

def standby_mode():
    global last_input_time
    last_input_time = datetime.now()

    while True:
        user_input = process_voice_input()

        if user_input and activation_phrase.lower() in user_input.lower():
            speak(Activated_message)
            start_standby_timer()
            return

def format_weather_response(weather_data):
    response = "Die aktuelle Wettervorhersage ist wie folgt:\n"
    for key, value in weather_data.items():
        response += f"{key.replace('_', ' ').capitalize()}: {value}\n"
    return response

def get_weather_data(latitude, longitude):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,rain,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m&hourly=temperature_2m&daily=sunrise,sunset&timezone=Europe%2FBerlin&forecast_days=1"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current_data = data.get('current', {})
        units = data.get('current_units', {})
        weather_formatted = {
            'Temperatur': f"{current_data.get('temperature_2m')} {units.get('temperature_2m', '')}",
            'Gefühlt wie': f"{current_data.get('apparent_temperature')} {units.get('apparent_temperature', '')}",
            'Luft Druck': f"{current_data.get('pressure_msl')} {units.get('pressure_msl', '')}",
            'Wolken': f"{current_data.get('cloud_cover')} {units.get('cloud_cover', '')}",
            'Regen': f"{current_data.get('rain')} {units.get('rain', '')}",
            'relative Luftfeuchtigkeit': f"{current_data.get('relative_humidity_2m')} {units.get('relative_humidity_2m', '')}",
            'windgeschwindigkeit': f"{current_data.get('wind_speed_10m')} {units.get('wind_speed_10m', '')}",
            'Windrichtung': f"{current_data.get('wind_direction_10m')} {units.get('wind_direction_10m', '')}",
        }
        return weather_formatted
    except requests.RequestException as e:
        print("Error fetching weather data:", e)
        return None

def getip():
    try:
        api = "https://api.ipify.org/?format=json"
        response = requests.get(api)
        response.raise_for_status()
        data = response.json()
        return data['ip']
    except requests.RequestException as e:
        print("Error fetching IP address:", e)
        return None

def get_user_location():
    ip = getip()
    if ip:
        try:
            url = f"https://freegeoip.app/json/{ip}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return {'latitude': data['latitude'], 'longitude': data['longitude']}
        except requests.RequestException as e:
            print("Error fetching location data:", e)
            return None
    return None

def search_youtube_video(title):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    search_response = youtube.search().list(
        q=title,
        part='id',
        maxResults=1,
        type='video'
    ).execute()

    if 'items' in search_response:
        video_id = search_response['items'][0]['id']['videoId']
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        print("Keine Videos gefunden.")
        return None

def download_youtube_audio(video_url):
    yt = YouTube(video_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download(output_path=os.getcwd(), filename="audio.mp3")
    return audio_file

def play_local_audio(audio_file):
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(audio_file)
    player.set_media(media)

    player.play()

def main():
    speak(welcome_message)
    start_standby_timer()

    while True:
        user_input = process_voice_input()

        if user_input and activation_phrase.lower() in user_input.lower():
            speak(Activated_message)
            start_standby_timer()

            while True:
                user_input = process_voice_input()

                if user_input and user_input.lower() in ['auf Wiedersehen', 'exit', 'bye', 'standby']:
                    goodbye_message = "Auf Wiedersehen!"
                    speak(goodbye_message)
                    return

                if user_input:
                    response = chat(user_input)
                    print("response: ", response)
                    speak(response)
                    start_standby_timer()

if __name__ == '__main__':
    main()
