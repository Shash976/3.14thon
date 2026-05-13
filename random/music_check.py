import pandas as pd

# Load the CSV files into DataFrames
playlist1 = pd.read_csv(r"C:\Users\shash\Downloads\My Amazon Music Library.csv", dtype={'ISRC': str})
playlist2 = pd.read_csv(r"C:\Users\shash\Downloads\My Spotify Library.csv", dtype={'ISRC': str})

# Merge the two playlists on the ISRC code to find unique entries
combined_playlist = pd.merge(playlist1, playlist2, on='ISRC', how='outer', indicator=True)

# Find songs that are only in playlist1
missing_in_playlist2 = combined_playlist[combined_playlist['_merge'] == 'left_only']

# Find songs that are only in playlist2
missing_in_playlist1 = combined_playlist[combined_playlist['_merge'] == 'right_only']

# Save the results to new CSV files
missing_in_playlist2.to_csv('missing_in_playlist2.csv', index=False)
missing_in_playlist1.to_csv('missing_in_playlist1.csv', index=False)
