#!/usr/bin/python2.7

#Copyright © 2018 Jake Beinart

import praw
import time, datetime
from collections import OrderedDict
import spotipy
import spotipy.util as util
import re
from spotipy.oauth2 import SpotifyClientCredentials
today = datetime.date.today()
weekday = today.weekday()
day_of_month = today.day

#REDDIT CREDENTIALS
REDDIT_CLIENT_ID = ''
REDDIT_CLIENT_SECRET = ''
REDDIT_USER_AGENT = ''

#SPOTIFY CREDENTIALS
SPOTIFY_USERNAME=''
SPOTIFY_CLIENT_ID=''
SPOTIFY_CLIENT_SECRET=''
SPOTIFY_REDIRECT_URI='https://example.com/callback/'
SPOTIFY_SCOPE="playlist-modify-public"
SPOTIFY_TEST_PLAYLIST=""
SPOTIFY_INDIEHEADS_WEEKLY="" 
SPOTIFY_INDIEHEADS_MONTHLY=""


def generatePlaylist(myTimeFilter, myPostLimit, mySubreddit, myPlaylistId):
    logfile = open("logfile.txt", 'w')
    logfile.write("-----------------------"+mySubreddit+" "+myTimeFilter+"ly " + str(today) + "-----------------------\n")
	#-------------REDDIT SECTION--------------
    reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=REDDIT_USER_AGENT)

    indieheads = reddit.subreddit(mySubreddit)
    songs = []

    for submission in indieheads.top(time_filter=myTimeFilter, limit=myPostLimit):
        title = submission.title
        if "[FRESH]" in title:
            title = re.sub('\[[^)]*\]( )*', '', title) #Remove tag
            title = re.sub(' \([^)]*\)', '', title) #Remove possible trailing parenthetical comment
            title = title.split("-")
            songs.append(title)
        elif "[FRESH ALBUM]" in title or "[FRESH EP]" in title:
            title = re.sub('\[[^)]*\]( )*', '', title) #Remove tag
            title = re.sub(' \([^)]*\)', '', title)
            title = title.split("-")
            title[0] += "[ALBUM]" #append album tag to denote special handling of albums
            songs.append(title)


    #-------------SPOTIFY SECTION--------------
	
    #--------CREATE ID LIST----------
    token = util.prompt_for_user_token(username=SPOTIFY_USERNAME, scope=SPOTIFY_SCOPE, client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URI)

    #songList = [['Star Treatment', 'Arctic Monkeys'], ['One Point Perspective', 'Arctic Monkeys'], ['Avant Gardener','Courtney Barnett']]
    uriList = []
    
    if token:
        spotify = spotipy.Spotify(auth=token)
        for song in songs:
            try:
                artistName = song[0]
                itemName = song[1].replace("'", "") #Spotify doesn't like apostrophes, apparently
                if artistName[-7:] == "[ALBUM]":
                    try:
                        results = spotify.search(q="artist:" + artistName[:-7] + " album:" + itemName, type='album')
                        tracks = spotify.album_tracks(results['albums']['items'][0]['id'])
                    except:
                        print "[ERROR] Couldn't find album: " + itemName
                        logfile.write("[ERROR] Couldn't find album: " + itemName + "\n")
                    #print tracks
                    max_popularity = -999
                    max_track = None
                    for track in tracks["items"]:
                        #print "searching for: " + artistName + " - " + track["name"].replace(u"\u2018", "'").replace(u"\u2019", "'")
                        temp_track = spotify.track(track['id'])
                        #print temp_track['popularity']
                        if temp_track['popularity'] >= max_popularity:
                            max_popularity = temp_track['popularity']
                            max_track = temp_track
                    print "Added this song from album: " + str(max_track["name"]) + " by " + artistName + " with score: " + str(max_popularity)
                    logfile.write("Added this song from album: " + str(max_track["name"]) + " by " + artistName + " with score: " + str(max_popularity) + "\n")
                    uriList.append(max_track["id"])
                else:
                    results = spotify.search(q="artist:" + artistName + " track:" + itemName, type='track')
                    try:
                        uriList.append(results['tracks']['items'][0]['id'])
                        print results['tracks']['items'][0]['name'] + " - " + results['tracks']['items'][0]['artists'][0]['name']
                        logfile.write(results['tracks']['items'][0]['name'] + " - " + results['tracks']['items'][0]['artists'][0]['name'] + "\n")
                    except:
                        print "[ERROR] Didn't find anything for this artist/song combo!" + str(song)
                        logfile.write("[ERROR] Didn't find anything for this artist/song combo!" + str(song) + "\n")
            except:
                print "[ERROR] Song format mismatch: " + str(song)
                logfile.write("[ERROR] Song format mismatch: " + str(song) + "\n")
            
                    
    else:
        print "[ERROR] Couldn't authenticate!"
        logfile.write("[ERROR] Song format mismatch: " + str(song) + "\n")
    
    #---------REMOVE DUPLICATES BUT PRESERVE ORDER----------
    uriList = list(OrderedDict.fromkeys(uriList))
    
    #---------WIPE PLAYLIST----------
    wiped_playlist = spotify.user_playlist_tracks(SPOTIFY_USERNAME, myPlaylistId)
    wiped_playlist = [song['track']['id'] for song in wiped_playlist['items']]
    #print wiped_playlist
    spotify.user_playlist_remove_all_occurrences_of_tracks(SPOTIFY_USERNAME, myPlaylistId, wiped_playlist)

    #---------ADD NEW SONGS TO PLAYLIST----------
    output_code = spotify.user_playlist_add_tracks(SPOTIFY_USERNAME, myPlaylistId, uriList)
    
    logfile.write("---------------------------------------------------------------------\n\n")
    logfile.close()
    
#--------------------------------------CREATE PLAYLISTS--------------------------------------
#generatePlaylist('week', 75, 'indieheads', SPOTIFY_TEST_PLAYLIST)
 
if(weekday == 4):
    generatePlaylist('week', 75, 'indieheads', SPOTIFY_INDIEHEADS_WEEKLY)
    
if(day_of_month == 1):
    generatePlaylist('month', 150, 'indieheads', SPOTIFY_INDIEHEADS_MONTHLY)