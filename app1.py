import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json, urllib.request, re
from pytube import YouTube 
import os, requests, time

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="d7bc93d225604fe3bfcca276f83740f1",
                                                           client_secret="0a94e430ad87413da14e708b0901d0c2"))

class Downloader:
    def __init__(self):
        url = self.validate_url(input("Enter a spotify url: ").strip())
        if "track" in url:
            print("this is a track")
            songs = [self.get_track_info(url)]
        elif "playlist" in url:
            songs = self.get_playlist_info(url)

    def validate_url(self, url):
        if re.search(r"^(https?://)?open\.spotify\.com/(playlist|track)/.+$", url):
            return url

        raise ValueError("Invalid Spotify URL")
    

    def get_track_info(self, track_url):
        res = requests.get(track_url)
        
        if res.status_code != 200:
            raise ValueError("Invalid Spotify track URL")
        
        sp1 = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="4c58ade0e9a74181a9e648d7dd504c5d",
                                                           client_secret="3ce4d253b04d417cb7248edc839852ca"))

        track = sp1.track(track_url)

        track_metadata = {
            "artist_name": track["artists"][0]["name"],
            "track_title": track["name"],
            "track_number": track["track_number"],
            "isrc": track["external_ids"]["isrc"],
            "album_art": track["album"]["images"][1]["url"],
            "album_name": track["album"]["name"],
            "release_date": track["album"]["release_date"],
            "artists": [artist["name"] for artist in track["artists"]],
        }

        return track_metadata
    
    def get_playlist_info(self, sp_url):
        res = requests.get(sp_url)
        if res.status_code != 200:
            raise ValueError("Invalid Spotify playlist URL")
        pl = sp.playlist(sp_url)
        if not pl["public"]:
            raise ValueError(
                "Can't download private playlists. Change your playlist's state to public."
            )
        tracks_list = []
        count = 0
        while count < 12:
            playlist = sp.playlist_tracks(sp_url, offset=count*100)
            # print(len(tracks_list))
            if len(playlist["items"]) == 0:
                break
            tracks_list.extend(playlist["items"])
            count += 1
        # playlist = sp.playlist_tracks(sp_url)
        tracks = [item["track"] for item in tracks_list]
        print(len(tracks))

        json_object = json.dumps(tracks, indent=4)
 
        # Writing to sample.json
        with open("tracks.json", "w") as outfile:
            outfile.write(json_object)

        tracks_info = []
        start = time.time()
        for idx, track in enumerate(tracks):
            # print(f"{idx+1}/{len(tracks)}", end="\r")
            print(idx)
            track_url = f"https://open.spotify.com/track/{track['id']}"
            print(track_url)
            track_info = self.get_track_info(track_url)
            tracks_info.append(track_info)
        end = time.time()
        print(end - start)

        # json_object = json.dumps(tracks, indent=4)
 
        # # Writing to sample.json
        # with open("tracks.json", "w") as outfile:
        #     outfile.write(json_object)

        return tracks_info
    
if __name__ == "__main__":

    Downloader()