import csv

file2 = r'C:/Users/shash/Downloads/My Amazon Playlist.csv'
file1 = r'C:/Users/shash/Downloads/My Spotify Playlist.csv'

def getDataFromCSV(file):
        total_data = csv.DictReader(open(file, encoding='cp437'))
        objects = []
        for data in total_data:
                objects.append(data)
        return objects

spotify_songs = getDataFromCSV(file1)
amazon_songs = getDataFromCSV(file2)


missed_songs = []
a_s = []
for songs in amazon_songs:
       a_s.append(songs['Track name'])
for song in spotify_songs:
        if song['Track name'] not in a_s:
                missed_songs.append(song)

keys = missed_songs[0].keys()

if __name__ == '__main__':
        with open(r'C:/Users/shash/Downloads/Music_sorted.csv', 'w', newline='', encoding='cp437') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(missed_songs)
        
        for missed_song in missed_songs:
                print(missed_song)