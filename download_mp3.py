import pytube
import os
import sys
import eyed3
from moviepy.editor import *
import shutil

def getUrls(playlist_url):
    urls = []
    playlist_videos = pytube.Playlist(playlist_url)
    playlist_name = playlist_videos.title
    for url in playlist_videos:
        urls.append(url)
    return urls, playlist_name

def download_youtube_audio(video_url, output_path):
  """Downloads the audio of a YouTube video as an MP3 file to the specified output path.

  Args:
    video_url: The URL of the YouTube video to download.
    output_path: The path to the output MP3 file.
  """

  youtube = pytube.YouTube(video_url)
  audio_stream = youtube.streams.get_audio_only()
  audio_stream.download(filename=output_path)

def getMP3fromLink(video_link, playlist_name = "", destination=r"C:\Users\shash\Downloads\prisha"):
    youtube_vid = pytube.YouTube(video_link)
    download_youtube_audio(video_link, os.path.join(destination,f"{youtube_vid.title.strip()}.mp3"))
    #try:    
    #    track = eyed3.load(out_mp3)
    #    track.initTag()
    #    track.tag.title = youtube_vid.title.replace('VEVO', '').replace('Official', '').replace('Lyric', '').replace('Video', '')
    #    track.tag.artist = youtube_vid.author.replace('VEVO', '').replace('Official', '').replace('Lyric', '').replace('Video', '')
    #    track.tag.album = playlist_name 
    #    track.tag.save(version=(1,None,None))
    #except:
    #    print("\tNo metadata found")
    print(youtube_vid.title + " is downloaded")

def getMP4fromLink(video_link, SAVE_PATH=r"C:\shashg\Downloads\test_mp4"):
    yt = pytube.YouTube(video_link)
    mp4files = yt.filter('mp4') 
    # get the video with the extension and
    # resolution passed in the get() function 
    d_video = yt.get(mp4files[-1].extension,mp4files[-1].resolution)
    d_video.download(SAVE_PATH)
    print('COMPLETED')

if __name__ == '__main__' :
    playlist_url = sys.argv[1]
    try:
        if os.path.exists(sys.argv[2].strip()):
            destination = sys.argv[2].strip()
    except:
        destination = r"C:\Users\shash\Downloads\prish"
    urls, playlist_name = getUrls(playlist_url)
    for url in urls:
        try:
            getMP3fromLink(url, playlist_name, destination)
        except Exception as err:
            print(f"\tError with {pytube.YouTube(url).title}-> {err}")
            continue
    print("Done")