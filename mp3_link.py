from download_mp3 import *

destination = input("Destination: ")
while 1:
    try:
        link = input("Youtube Link: ")
        getMP3fromLink(link, destination=destination.strip())
    except KeyboardInterrupt:
        print("Stopping....")
        break