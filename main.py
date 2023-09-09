'''

This program will fill a playlist of songs whose album covers are only
greyscale. Genre, artist, and song content will be determined
by a list of user-specified artists and genres. Playlist refreshes every
three hours.

'''

#import libraries
import json
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from image_bw import *
from random import randint
from datetime import datetime

#playlist details
added_count = 0 #number of songs in the playlist
acceptable_tracks = [] #songs that are in the playlist

#client access scope
scope = "playlist-modify-private"
lenient_mode = False
lenient_mode_offset = 0.5

#api data
sp = None
api_calls = 0

#SEED VALUES - how the playlist is filled
artist_seeds = []
genre_seeds = []

#fetches + downloads album art for given url, returns True on success, False otherwise
def get_album_art(albumURL):
    #save image to local program directory
    try:
        img_data = requests.get(albumURL).content
    except:
        print("[ERR] an album's artwork could not be downloaded, ignored")
        return False
    else:
        with open("cover.jpg", "wb") as handler:
            handler.write(img_data)
            handler.close()
        return True

#generates list of recommended tracks for playlist, returns list of item=
#(URI, album URI, name, artist name)
def generate_recs(amount, artistSeeds, genreSeeds):
    sp_recs = [(track["uri"], track["album"]["uri"], track["name"], track["artists"][0]["name"])\
    for track in sp.recommendations(artistSeeds, genreSeeds, limit=amount)["tracks"]]
    global api_calls
    api_calls += 1
    return sp_recs

#removes songs from a given list of URIs that:
#have energy level > 0.5 after 11:59pm
#have energy level < 0.5 before 11:59pm
#if isLenient is true, cuttoffs are lessened by lenient_mode_offset
def vibe_check(songURIs, isLenient):
    energy_levels = [energy_val["energy"] for energy_val in sp.audio_features(songURIs)]
    global api_calls
    api_calls += 1
    offset = 0
    if isLenient:
        offset = lenient_mode_offset
    time_pm_am = datetime.today().strftime("%p")
    revised_song_list = []
    for song in range(len(songURIs)):
        if time_pm_am == "PM":
            if energy_levels[song] > (0.5 - offset):
                revised_song_list.append(songURIs[song])
        else:
            if energy_levels[song] < (0.5 + offset):
                revised_song_list.append(songURIs[song])
    return revised_song_list

#refresh global artist and genre seed lists from artists.json and genres.json
#randomly picks a x artists seeds and y genre seeds, where x + y = 5
def refresh_seeds():
    #clear global seed values
    artist_seeds.clear()
    genre_seeds.clear()
    #seed counts (sum must be <= 5 per spotify api specs)
    artist_count = 0
    genre_count = 0
    #get all preferred artists and genres from json files
    all_artists = []
    all_genres = []
    with open('artists.json') as json_file:
        all_artists = json.load(json_file)
    with open('genres.json') as json_file:
        all_genres = json.load(json_file)
    #randomly determine seed count for both artist and songs
    artist_count = randint(1, 4)
    genre_count = 5 - artist_count
    #pick artist_count amount of artist seeds
    for i in range(artist_count):
        added = False
        while not added:
            tmp = all_artists["artists"][randint(0,len(all_artists["artists"])-1)]
            if tmp not in artist_seeds:
                artist_seeds.append(tmp)
                added = True
    #pick song_count amount of song seeds
    for i in range(genre_count):
        added = False
        while not added:
            tmp = all_genres["genres"][randint(0,len(all_genres["genres"])-1)]
            if tmp not in genre_seeds:
                genre_seeds.append(tmp)
                added = True
    return (artist_seeds, genre_seeds)

#updates playlist name with greeting
def update_playlist_name():
    name_mod = ""
    time_pm_am = datetime.today().strftime("%I%p")
    if "PM" in time_pm_am:
        name_mod = "hi :)"
    else:
        name_mod = "gm :)"
    name_final = "B&W Mix - " + name_mod
    sp.playlist_change_details(pl_uri, name=name_final)
    global api_calls
    api_calls += 1

#update playlist desc with energy and status
def update_playlist_desc(isUpdating):
    energy = ""
    status = ""
    time_pm_am = datetime.today().strftime("%p")
    time_hour = datetime.today().strftime("%I")
    if isUpdating:
        status = "Updating..."
    else:
        if time_hour[0] == "0":
            status = "Updated @" + time_hour[1] + time_pm_am
        else:
            status = "Updated @" + time_hour + time_pm_am
    if time_pm_am == "PM":
        energy = "High"
    else:
        energy = "Chill"
    desc_final = "- Auto-Managed - Energy: " + energy + " - Status: " + status + " -"
    sp.playlist_change_details(pl_uri, description=desc_final)
    global api_calls
    api_calls += 1

#MAIN
if __name__ == "__main__":
    #request spotify authentication + playlist id
    c_id = input("Enter client ID: ")
    c_secret = input("Enter client secret: ")
    r_uri = input("Enter return url: ")
    pl_uri = input("Enter playlist uri: ")

    #initialize api
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=c_id,client_secret=c_secret,redirect_uri=r_uri,scope=scope))
    api_calls += 1

    #report initial values
    print("Starting...")
    time.sleep(2)

    fail_count = 0 # of loop iterations where zero songs are added

    while True:
        print("[INFO] refreshing playlist")
        print("updating playlist details")
        update_playlist_name()
        update_playlist_desc(True)
        print("[INFO] seeds loaded:", refresh_seeds())
        lenient_mode = False
        #clear playlist
        if added_count > 0:
            sp.playlist_remove_all_occurrences_of_items(pl_uri, acceptable_tracks)
            acceptable_tracks.clear()
            added_count = 0
            api_calls += 1
        print("[INFO] Song scanning in 5 seconds...\n")
        time.sleep(5)
        print("[INFO] scanning songs...")
        while added_count < 20:
            #tell spotify to return a list of song suggestions
            recs = generate_recs(20, artist_seeds, genre_seeds)
            num_songs_found = 0
            found_tracks = []
            found_albums = []
            #get an album cover url for every suggestion
            for rec in recs:
                found_albums.append(rec[1])
            album_covers = [url["images"][-1]["url"] for url in sp.albums(found_albums)["albums"]]
            api_calls += 1
            #keep all new suggestons with greyscale album covers
            for i in range(len(recs)):
                if recs[i][0] not in acceptable_tracks and get_album_art(album_covers[i]) and detect_color_image("cover.jpg") == 1:
                    #print("________", rec[2], "by", rec[3], "____ACCEPTED____")
                    found_tracks.append(recs[i][0])
            print("[FILTER] found", len(found_tracks), "new greyscale tracks")

            #keep remaining suggestions that pass vibe_check functiom
            if len(found_tracks) != 0:
                found_tracks = vibe_check(found_tracks, lenient_mode)
            print("[FILTER]", len(found_tracks), "tracks have appropriate energy")

            #add remaining suggestions to playlist (if any)
            if len(found_tracks) > 0:
                sp.playlist_add_items(pl_uri, found_tracks)
                api_calls += 1
                num_songs_found = len(found_tracks)
                acceptable_tracks.extend(found_tracks)
                fail_count = 0
            else:
                fail_count += 1 #report failed loop iterations
                print("[WARN] fail count:", fail_count)

            #report number of songs added per iteration
            print("\n[ADDED] :", num_songs_found, "songs")
            added_count += num_songs_found
            print("[INFO] [", added_count, "total songs have been added ]\n")

            #if 3 iterations fail, refresh genre and artist seeds
            if fail_count >= 3:
                print("[WARN/INFO] seeds reloaded:", refresh_seeds())
                print("[WARN/INFO] lenient mode enabled")
                lenient_mode = True
                fail_count = 0

            print("[INFO]", api_calls, "spotify api calls")
            time.sleep(5)
        update_playlist_desc(False)
        print("[INFO] ____PLAYLIST REFRESHED____")
        print("[INFO] ____WAITING 3 HOUR(S)____")
        time.sleep(3600) #refresh playlist every 3 hours
