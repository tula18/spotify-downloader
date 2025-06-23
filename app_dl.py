import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json, urllib.request, re
import urllib.error
from moviepy.video.VideoClip import TextClip, ImageClip  
from moviepy.video.compositing import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from pytube import YouTube 
import os, requests, time
from rich.console import Console
from pytube.exceptions import AgeRestrictedError
# import pyautogui
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
import math
import numpy as np
import yt_dlp as youtube_dl
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="3c1b217c1a6a49cea3789ab3b503d211", client_secret="38b6b43d6b6b46d3800a7322a93f5cf4"))
console = Console()

class Downloader:
    def __init__(self):
        self.ageRestricted = []
        self.folder_name = "music"
        self.final_path = ""
        url = self.validate_url(input("Enter a Spotify URL: ").strip())
        self.convert_to = "mp4"
        if "track" in url:
            print("-"*100)
            print("Starting operation for Track link type")
            songs = [self.get_track_info(url)]
        elif "playlist" in url:
            print("-"*100)
            print("Starting operation for Playlist link type")
            songs = self.get_playlist_info(url)
        elif "show" in url:
            print("-"*100)
            print("Starting operation for Show link type")
            songs = self.get_show_info(url)

        start = time.time()
        print("-"*100)
        print("Starting operation for Downloading the songs")

        downloaded = 0
        self.create_folder_if_not_exists('./tmp/')
        self.create_folder_if_not_exists(self.folder_name)
        if self.convert_to == "wav":
            self.create_folder_if_not_exists(self.folder_name+' - WAV')
        if self.convert_to == "mp4":
            self.create_folder_if_not_exists(self.folder_name+' - MP4')
        total_songs = len(songs)
        max_workers = 4  # You can adjust this number for more/less parallelism
        downloaded = 0
        with tqdm(total=total_songs, desc="Downloading songs", unit="song") as pbar:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for idx, track_info in enumerate(songs):
                    futures.append(executor.submit(
                        self._download_song_with_progress, idx, track_info, total_songs
                    ))
                for future in as_completed(futures):
                    if future.result():
                        downloaded += 1
                    pbar.update(1)
        shutil.rmtree("./tmp")
        try:
            with open('ageRestricted.json', 'r') as json_data:
                d = json.loads(json_data.read())
        except Exception as e:
            print(e)
            d = {}
        end = time.time()
        os.chdir(f"{self.folder_name}")
        print(f"Download location: {os.getcwd()}")
        console.print(
            f"DOWNLOAD COMPLETED: {downloaded}/{len(songs)} song(s) downloaded".center(
                70, " "
            ),
            style="on green",
        )
        if len(d) > 0:
            console.print(
                f"{len(d)} didn't download because of age restriction".center(
                    70, " "
                ),
                style="on red",
            )
        console.print(
            f"Total time taken: {round(end - start)} Sec".center(70, " "), style="on white"
        )

    def validate_url(self, url):
        if re.search(r"^(https?://)?open\.spotify\.com/(playlist|track|show)/.+$", url):
            return url

        raise ValueError("Invalid Spotify URL")

    def find_youtube(self, query):
        phrase = query.replace(" ", "+")
        search_link = "https://www.youtube.com/results?search_query=" + phrase
        count = 0
        try:
            response = requests.get(search_link)
            if response.status_code == 200:
                search_results = re.findall(r"watch\?v=(\S{11})", response.text)
                if search_results:
                    first_vid = "https://www.youtube.com/watch?v=" + search_results[0]
                    return first_vid
                else:
                    raise ValueError("No videos found. Please try a different search query.")
            else:
                raise ValueError("Failed to fetch search results. Please check your internet connection and try again later.")
        except requests.RequestException as e:
            raise ValueError("An error occurred while fetching search results: {}".format(e))

    def get_track_info(self, track_url):
        print("-"*100)
        res = requests.get(track_url)
        if res.status_code != 200:
            raise ValueError("Invalid Spotify track URL")

        track = sp.track(track_url)

        track_metadata = {
            "artist_name": track["artists"][0]["name"],
            "track_title": track["name"],
            "track_number": track.get("track_number", ""),
            "isrc": track["external_ids"].get("isrc", ""),
            "album_art": track["album"]["images"][1]["url"],
            "album_name": track["album"]["name"],
            "release_date": track["album"]["release_date"],
            "artists": [artist["name"] for artist in track["artists"]],
        }
        print(track["external_ids"]["isrc"])

        return track_metadata

    def create_folder_if_not_exists(self, folder_path):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return f"Folder created at {folder_path}"
        else:
            return f"Folder already exists. {folder_path}"

    
    def download_yt(self, yt_link, idx, track_info, cookies_file="cookies.txt"):
        try:
            yt_opts = {
                'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/mp4',
                'outtmpl': f'./{self.folder_name} - MP4/{idx + 1} - {track_info["artist_name"]} - {track_info["track_title"]}.%(ext)s',
                'noplaylist': True,
                'merge_output_format': 'mp4',
                'quiet': True,
            }
            if os.path.exists(cookies_file):
                yt_opts['cookiefile'] = cookies_file
            else:
                print(f"[Warning] {cookies_file} not found. Some videos may not download due to restrictions.")
            with youtube_dl.YoutubeDL(yt_opts) as ydl:
                info = ydl.extract_info(yt_link, download=True)
                # Get the actual file path from info dict
                if 'requested_downloads' in info and info['requested_downloads']:
                    return info['requested_downloads'][0]['filepath']
                elif 'filepath' in info:
                    return info['filepath']
                else:
                    return None
        except Exception as e:
            print(f"An error occurred while downloading: {e}")
            return None

    def on_progress(self, stream, chunk, bytes_remaining):
        pass  # Disable per-file progress output

    def get_playlist_info(self, sp_url):
        print("-"*100)
        print("Checking if playlist url is valid", end="", flush=True)
        res = requests.get(sp_url)
        if res.status_code != 200:
            raise ValueError("Invalid Spotify playlist URL")
        print(", Done")
        pl = sp.playlist(sp_url)
        self.folder_name = f"{pl['name']} by {pl['owner']['display_name']} - Spotify Playlist"
        print("Checking if playlist is public", end="", flush=True)
        if not pl["public"]:
            raise ValueError("Can't download private playlists. Change your playlist's state to public.")
        print(", Done")
        tracks_list = []
        count = 0
        print("Preparing the song list", end="", flush=True)
        while count < 12:
            playlist = sp.playlist_tracks(sp_url, offset=count * 100)
            if len(playlist["items"]) == 0:
                break
            tracks_list.extend(playlist["items"])
            count += 1
        print(", Done,", f"Songs Count: {len(tracks_list)}")

        json_object = json.dumps(tracks_list, indent=4)
        with open("tracks.json", "w") as outfile:
            outfile.write(json_object)

        tracks_info = []
        start = time.time()
        print("Preparing the songs metadata")
        for idx, item in enumerate(tracks_list):
            try:
                track = item["track"]
                track_metadata = {
                    "idx": idx,
                    "artist_name": track["artists"][0]["name"],
                    "track_title": track["name"],
                    "track_number": track.get("track_number", ""),
                    "isrc": track["external_ids"].get("isrc", ""),
                    "album_art": "",
                    "album_name": track["album"]["name"],
                    "release_date": track["album"]["release_date"],
                    "artists": [artist["name"] for artist in track["artists"]],
                }
                if track["album"]["images"]:
                    track_metadata["album_art"] = track["album"]["images"][1]["url"]
                tracks_info.append(track_metadata)
            except KeyError as e:
                print(f"Skipping track due to missing key: {e}")
                print(f"Track data: {json.dumps(item, indent=2)}")
            except IndexError as e:
                print(f"Skipping track due to index error: {e}")
                print(f"Track data: {json.dumps(item, indent=2)}")

        end = time.time()
        print("Done,", f"(Time to run: {end-start} Seconds)")

        json_object = json.dumps(tracks_info, indent=4)
        with open("tracks-info.json", "w") as outfile:
            outfile.write(json_object)

        return tracks_info

    def get_show_info(self, sp_url):
        print("-"*100)
        print("Checking if Show url is valid", end="", flush=True)
        res = requests.get(sp_url)
        if res.status_code != 200:
            raise ValueError("Invalid Spotify Show URL")
        print(", Done")
        pl = sp.show(sp_url)
        show_name = pl['name']
        self.folder_name = f"{pl['name']} - Spotify Show"
        tracks_list = []
        count = 0
        print("Preparing the song list", end="", flush=True)
        offset = 0
        limit = 50

        while True:
            results = sp.show_episodes(sp_url, offset=offset, limit=limit)
            tracks_list.extend(results['items'])
            if results['next'] is not None:
                offset += limit
            else:
                break
        print(tracks_list)
        print(", Done,", f"Shows Count: {len(tracks_list)}")

        json_object = json.dumps(tracks_list, indent=4)
        with open("shows.json", "w") as outfile:
            outfile.write(json_object)

        tracks_info = []
        start = time.time()
        print("Preparing the songs metadata")
        
        for idx, track in enumerate(tracks_list):
            print(f"{idx+1}/{len(tracks_list)}", end="\r")
            track_metadata = {
                "idx": idx,
                "artist_name": show_name,
                "track_title": track["name"],
                "track_number": idx,
                "isrc": track["id"],
                "album_art": "",
                "album_name": show_name,
                "release_date": track["release_date"],
                "artists": [],
            }
            if track["images"]:
                track_metadata["album_art"] = track["images"][1]["url"]
            tracks_info.append(track_metadata)

        end = time.time()
        print("Done,", f"(Time to run: {end-start} Seconds)")

        json_object = json.dumps(tracks_info, indent=4)
        with open("tracks-info.json", "w") as outfile:
            outfile.write(json_object)

        return tracks_info

    def set_metadata(self, metadata, file_path):
        """adds metadata to the downloaded mp3 file"""
        if file_path.endswith('.mp4'):
            print(f"Skipping metadata for {file_path} as it is an MP4 file.")
            return

        mp3file = EasyID3(file_path)

        # add metadata
        mp3file["albumartist"] = metadata["artist_name"]
        mp3file["artist"] = metadata["artists"]
        mp3file["album"] = metadata["album_name"]
        mp3file["title"] = metadata["track_title"]
        mp3file["date"] = metadata["release_date"]
        mp3file["tracknumber"] = str(metadata["track_number"])
        mp3file["isrc"] = metadata["isrc"]
        mp3file.save()

        # add album cover
        audio = ID3(file_path)
        with urllib.request.urlopen(metadata["album_art"]) as albumart:
            audio["APIC"] = APIC(
                encoding=3, mime="image/jpeg", type=3, desc="Cover", data=albumart.read()
            )
        audio.save(v2_version=3)

    def _download_song_with_progress(self, idx, track_info, total_songs):
        search_term = f"{track_info['artist_name']} {track_info['track_title']} audio"
        video_link = self.find_youtube(search_term)
        tqdm.write(f"Now downloading ({idx+1}/{total_songs}): {track_info['artist_name']} - {track_info['track_title']}")
        audio = self.download_yt(video_link, idx, track_info)
        if audio:
            if self.convert_to == "mp3":
                self.set_metadata(track_info, audio)
            # console.print("[blue]______________________________________________________________________")
            return True
        else:
            print("MP4 File exists. Skipping...")
            return False

if __name__ == "__main__":
    try:
        Downloader()
    except KeyboardInterrupt:
        print("Downloader stopped. Goodbye!")
