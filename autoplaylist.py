from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import re
import datetime


def authorize():
    # Authenticate spotify credentials
    # Note: Save you credentials as environment variables
    scope = 'playlist-modify-public'
    username = '21wrhzneviibcick6tnquhp4i'
    token = SpotifyOAuth(scope=scope, username=username)
    return token


def setup_data():
    req = Request(url='http://www2.radioparadise.com/rp3-mx.php?n=Playlist', headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    return webpage


def song_list(content):
    soup = BeautifulSoup(content, 'lxml')
    #print(soup.prettify())
    list_of_songs = []
    
    # Scrape Radio Paradise website for songs played in the last hour
    song_cards = soup.find_all('div', class_=['p-row1', 'p-row2'])
    for songs in song_cards:
        song = songs.a.text
        song = song[5:].replace("-", "").strip(' ')
        song = song[2:]
        song = re.sub("\s\s+", " ", song)
        list_of_songs.append(song)
    list_of_songs = list(reversed(list_of_songs))
    list_of_songs = list_of_songs[4:]
    return list_of_songs


def find_and_add_songs(playlistid):
    # List new songs from radio webpage
    list_of_songs = song_list(setup_data())
    #print(list_of_songs)
    
    result_list = []
    
    # List of track ids to remove from playlist
    remove_track_id = remove_all_songs(playlistid)
    
    # Ensure the new song list does not have any old removed songs from previous playlist update
    for song in list_of_songs:
        result = spotifyObject.search(q=song, market='US')
        #print(json.dumps(result, sort_keys=4, indent=4))
        if result['tracks']['total'] != 0:
            if result['tracks']['items'][0]['uri'] not in remove_track_id:
                if result['tracks']['items'][0]['artists'][0]['name'] in song:
                    result_list.append(result['tracks']['items'][0]['uri'])
                    
    # Add new songs and update description
    spotifyObject.playlist_add_items(playlist_id=playlistid, items=result_list)
    spotifyObject.playlist_change_details(playlist_id=playlist_id, name='Rpi4test',
                                          description=description_update())



def remove_all_songs(playlistid):
    # Fetch current songs in the playlist
    remove_track_result = spotifyObject.playlist_tracks(playlist_id=playlistid)
    #print(json.dumps(remove_track_result,sort_keys=4,indent=4))
    
    # List of track IDs to remove from playlist
    remove_track_id = []
    for i in range(0, remove_track_result['total']):
        remove_track = remove_track_result['items'][i]['track']['uri']
        remove_track_id.append(remove_track)
        
    # Remove songs from playlist
    spotifyObject.playlist_remove_all_occurrences_of_items(playlist_id=playlistid,
                                                           items=remove_track_id)
    return remove_track_id


def description_update():
    # Adds the last playlist update time to the playlist description
    uptime = datetime.datetime.now()
    last_update_time = str('Last updated: ' + uptime.strftime('%b') + ' ' + uptime.strftime('%d')
                           + ', ' + uptime.strftime('%I') + ':' + uptime.strftime('%M') + ' ' + uptime.strftime('%p'))
    track_src = 'sqlupd'
    playlist_description = str(last_update_time)
    return playlist_description

print('Running autoplaylist.py')
playlist_id = '6bgghJZjZNNNhyIMPy1mD6'
print('Authenticating Spotify credentials ...') 
spotifyObject = spotipy.Spotify(auth_manager=authorize())
print('Updating playlist')
find_and_add_songs(playlist_id)
print('Done.')
