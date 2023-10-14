import pytube
import os
import sys
import eyed3

def getUrls(playlist_url):
    urls = []
    playlist_videos = pytube.Playlist(playlist_url)
    playlist_name = playlist_videos.title
    for url in playlist_videos:
        urls.append(url)
    
    return urls, playlist_name

def getMP3fromLink(video_link, playlist_name = "", destination=r"C:\Users\shash\Downloads\prisha"):
    youtube_vid = pytube.YouTube(video_link)
    video = youtube_vid.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=destination)
    base,ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file,new_file)
    try:
        track = eyed3.load(new_file)
        track.initTag()
        track.tag.title = youtube_vid.title
        track.tag.artist = youtube_vid.author.replace('VEVO', '')
        track.tag.album = playlist_name 
        track.tag.save(version=(1,None,None))
        track.tag.save()
    except:
        print("\tNo metadata found")
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
        getMP3fromLink(url, playlist_name, destination)
    print("Done")