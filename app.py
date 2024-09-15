import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json, urllib.request, re
import urllib.error
from moviepy.editor import *
from pytubefix import YouTube 
import os, requests, time
from rich.console import Console
from pytube.exceptions import AgeRestrictedError
import pyautogui
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
import math
import numpy as np

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
        for idx, track_info in enumerate(songs):
            search_term = f"{track_info['artist_name']} {track_info['track_title']} audio"
            video_link = self.find_youtube(search_term)
            console.print(
                f"[magenta]({idx+1}/{len(songs)})[/magenta] Downloading '[cyan]{track_info['artist_name']} - {track_info['track_title']}[/cyan]'..."
            )
            audio = self.download_yt(video_link, idx, track_info)
            if audio:
                print(audio)
                if self.convert_to == "mp3":
                    self.set_metadata(track_info, audio)
                console.print(
                    "[blue]______________________________________________________________________"
                )
                downloaded += 1
            else:
                print("MP4 File exists. Skipping...")
            pyautogui.press('shift')
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
        print(search_link)
        try:
            response = requests.get(search_link)
            
            # Save the HTML content for reference (optional)
            with open(f"html/youtube_search_results-{query}.html", "w", encoding="utf-8") as file:
                file.write(response.text)
            
            if response.status_code == 200:
                # Extract video IDs from the search results
                search_results = re.findall(r"watch\?v=(\S{11})", response.text)

                if search_results:
                    # Try to skip sponsored videos by not using the first result
                    for idx, video_id in enumerate(search_results):
                        video_link = "https://www.youtube.com/watch?v=" + video_id
                        
                        # Optionally, you could check for additional criteria here to filter out ads.
                        # For simplicity, we skip the first video and use the second or later ones.
                        if idx == 0:
                            print("Skipping the first result to avoid sponsored videos...")
                            continue  # Skip the first result, which could be sponsored
                        
                        return video_link
                    
                    raise ValueError("No valid video found. Please try a different search query.")
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

    def download_yt(self, yt_link, idx, track_info):
        try:
            yt = YouTube(yt_link, on_progress_callback=self.on_progress)
            yt.title = "".join([c for c in yt.title if c not in ['/', '\\', '|', '?', '*', ':', '>', '<', '"']])
            safe_artist_name = track_info['artist_name'].replace("/", "-").replace("\\", "-")
            safe_title = yt.title.replace("/", "-").replace("\\", "-")
            folder_path = self.folder_name + ' - MP4' if self.convert_to == "mp4" else self.folder_name
            self.final_path = f"./{folder_path}/{idx + 1} - {safe_artist_name} - {safe_title}.mp4"
            exists = os.path.exists(self.final_path)
            if exists:
                return False
            video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            video.download(output_path=folder_path, filename=f"{idx + 1} - {safe_artist_name} - {safe_title}.mp4")
            return self.final_path
        except AgeRestrictedError:
            self.ageRestricted.append(track_info)
            json_object = json.dumps(self.ageRestricted, indent=4)
            with open("ageRestricted.json", "w") as outfile:
                outfile.write(json_object)
            print(f"Video {yt_link} is age restricted and cannot be downloaded.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = math.floor(bytes_downloaded / total_size * 100)
        side_size = 100 - percentage_of_completion
        mes_len = len(str(percentage_of_completion) + '%')
        per_side_size = math.floor((5 - mes_len) / 2)
        print(f"{percentage_of_completion}%{' ' * per_side_size} - |{'-' * percentage_of_completion}{' ' * side_size}|", end="\r")

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

if __name__ == "__main__":
    try:
        Downloader()
    except KeyboardInterrupt:
        print("Downloader stopped. Goodbye!")
