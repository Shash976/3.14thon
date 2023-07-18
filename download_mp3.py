import pytube
import os
import sys
import music_tag

def getUrls(playlist_url):
    urls = []
    playlist_videos = pytube.Playlist(playlist_url)
    playlist_name = playlist_videos.title
    for url in playlist_videos:
        urls.append(url)
    
    return urls, playlist_name

def getMP3fromLink(video_link, playlist_name = ""):
    youtube_vid = pytube.YouTube(video_link)
    video = youtube_vid.streams.filter(only_audio=True).first()

    destination = r"C:\Users\shashg\Downloads\prisha"

    out_file = video.download(output_path=destination)

    base,ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file,new_file)
    track = music_tag.load_file(new_file)
    track['title'] = youtube_vid.title
    track['artist'] = youtube_vid.author.replace('VEVO', '')
    track['album artist'] = youtube_vid.author.replace('VEVO', '')
    track["album"] = playlist_name
    track.save()
    print(youtube_vid.title + " is downloaded")

def getMP4fromLink(video_link):
    yt = pytube.YouTube(video_link)
    mp4files = yt.filter('mp4') 
    SAVE_PATH = r"C:\shashg\Downloads\test_mp4"
    # get the video with the extension and
    # resolution passed in the get() function 
    d_video = yt.get(mp4files[-1].extension,mp4files[-1].resolution)
    d_video.download(SAVE_PATH)
    print('COMPLETED')

if __name__ == '__main__' :
    playlist_url = sys.argv[1]
    urls, playlist_name = getUrls(playlist_url)
    for url in urls:
        getMP3fromLink(url, playlist_name)
    print("Done")