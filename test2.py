from googleapiclient.discovery import build
from pytube import YouTube
import vlc
import os
API_KEY = "none"

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


    while True:
        more = input("Möchten Sie noch einen weiteren Song abspielen? (Ja/Nein): ").strip().lower()
        if more == 'ja':
            title = input("Bitte geben Sie den Titel des Songs ein: ")
            video_url = search_youtube_video(title)
            if video_url:
                audio_file = download_youtube_audio(video_url)
                player.stop()
                play_local_audio(audio_file)
        elif more == 'nein':
            break
        else:
            print("Ungültige Eingabe. Bitte geben Sie 'Ja' oder 'Nein' ein.")

if __name__ == "__main__":
    title = input("Bitte geben Sie den Titel des Songs ein: ")
    video_url = search_youtube_video(title)
    if video_url:
        audio_file = download_youtube_audio(video_url)
        play_local_audio(audio_file)
