from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect
from urllib.request import Request, urlopen
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import re
import datetime
import os
import time


def authorize():
    # Authenticate spotify credentials
    # Note: Save you credentials as environment variables
    scope = 'user-read-private playlist-modify-public'
    username = os.environ.get('SPOTIFY_USERNAME')
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
    print(str(username) + str(client_secret))
    
    delete_cached_token(username)
    token = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, username=username)
    return token
    

def delete_cached_token(username):
    if os.path.exists(os.getcwd()+'.cache'):
        os.remove(".cache")
    if os.path.exists(os.getcwd()+'.cache-'+str(username)):
        os.remove(".cache-"+str(username))


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
    
def song_list_new():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://radioparadise.com/music/what-is-playing')
    
        page.wait_for_load_state("networkidle")
        
        list_of_songs = []
        playtime = 0
        i = 1
        while playtime < 65:
            song = page.locator("div.song-row").nth(i).inner_text()
            split_data = song.split("\n")
            title = split_data[2]
            artist = split_data[3]
            playtime = playtime + float(split_data[5])
            list_of_songs.append(artist + " " + title)
            i = i+1
            
        list_of_songs = list(reversed(list_of_songs))        
        print("Playtime: " + str(playtime) + " minutes")
    browser.close()
    return list_of_songs   
    

def find_and_add_songs(playlistid):
    # List new songs from radio webpage
    #list_of_songs = song_list(setup_data()) # Old website
    list_of_songs = song_list_new() # New website
    #print(list_of_songs)
    
    result_list = []
    
    # List of track ids to remove from playlist
    remove_track_id = remove_all_songs(playlistid)
    
    # Ensure the new song list does not have any old removed songs from previous playlist update
    for song in list_of_songs:
        time.sleep(0.1)
        result = spotifyObject.search(q=song, limit=5, offset=0, type='track', market='US')
        #print(json.dumps(result, sort_keys=4, indent=4))
        if result['tracks']['total'] != 0:
            if result['tracks']['items'][0]['uri'] not in remove_track_id:
                if result['tracks']['items'][0]['artists'][0]['name'] in song:
                    result_list.append(result['tracks']['items'][0]['uri'])
    
    #print('Found ' + str(len(result_list)) + ' out of ' + str(len(list_of_songs)) + ' songs.')
    
    if len(result_list) > 0:
        # Add new songs and update description
        spotifyObject.playlist_add_items(playlist_id=playlistid, items=result_list)
        
        time.sleep(2)
        
        # Check update
        current_tracks = spotifyObject.playlist_tracks(playlist_id=playlistid)
        
        if current_tracks['total'] == len(result_list):
            update_log('Update successful. Added ' + str(current_tracks['total']) + ' new songs.')
        elif current_tracks['total'] < len(result_list) and current_tracks['total'] > 0:
            update_log('Update successful. Added ' + str(current_tracks['total']) 
            + ' out of ' + str(len(result_list)) + ' songs.')
        elif current_tracks['total'] == 0:
            update_log('Update failed.')
        else:
            update_log('Unknown: current_tracks > result_list')
    else:
        # Rick roll the playlist
        rick_list = []
        rick_list.append('spotify:track:4PTG3Z6ehGkBFwjybzWkR8')
        spotifyObject.playlist_add_items(playlist_id=playlistid, items=rick_list)
        update_log("Rickroll.")


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
    if len(remove_track_id) > 0:
        spotifyObject.playlist_remove_all_occurrences_of_items(playlist_id=playlistid,
                                                               items=remove_track_id)
    return remove_track_id


def description_update(playlist_id):
    # Adds the last playlist update time to the playlist description
    uptime = datetime.datetime.now()
    last_update_time = str('Last updated: ' + uptime.strftime('%b') + ' ' + uptime.strftime('%d')
                           + ', ' + uptime.strftime('%I') + ':' + uptime.strftime('%M') + ' ' + uptime.strftime('%p'))
    track_src = 'Track Source: Radio Paradise: Main Mix'
    playlist_description = str(last_update_time + '; ' + track_src)
    spotifyObject.playlist_change_details(playlist_id=playlist_id, name='Autoplaylist: RP Main Mix',
                                          description=playlist_description)

def update_log(text):
    logtime = datetime.datetime.now()
    log = str(logtime.strftime('%m/%d/%Y, %H:%M:%S') + ' ' + text + '\n')
    with open("updatelog.txt", "a") as myfile:
        myfile.write(log)
    
    
print('Running autoplaylist.py')
playlist_id = os.environ.get('PLAYLIST_ID')
print('Authenticating Spotify credentials ...') 
spotifyObject = spotipy.Spotify(auth_manager=authorize())
print('Updating playlist')
find_and_add_songs(playlist_id)
description_update(playlist_id)
print('Done.')
