import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json, urllib.request, re
import urllib.error
from moviepy.editor import *
from pytube import YouTube 
import os, requests, time
from rich.console import Console
from pytube.exceptions import AgeRestrictedError
import pyautogui
import shutil
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
from pydub import AudioSegment
import math


sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="3c1b217c1a6a49cea3789ab3b503d211", client_secret="38b6b43d6b6b46d3800a7322a93f5cf4"))
console = Console()
class Downloader:
    def __init__(self):
        self.ageRestricted = []
        self.folder_name = "music"
        self.final_path = ""
        url = self.validate_url(input("Enter a spotify url: ").strip())
        self.convert_to = "wav"
        if "track" in url:
            print("-"*100)
            print("Starting operetion for Track link type")
            songs = [self.get_track_info(url)]
        elif "playlist" in url:
            print("-"*100)
            print("Starting operetion for Playlist link type")
            songs = self.get_playlist_info(url)
        elif "show" in url:
            print("-"*100)
            print("Starting operetion for show link type")
            songs = self.get_show_info(url)

        start = time.time()
        print("-"*100)
        print("Starting operetion for Downloading the songs")

        downloaded = 0
        self.create_folder_if_not_exists('./tmp/')
        self.create_folder_if_not_exists(self.folder_name)
        if self.convert_to == "wav":
            self.create_folder_if_not_exists(self.folder_name+' - WAV')
        for idx, track_info in enumerate(songs):
            search_term = f"{track_info['artist_name']} {track_info['track_title']} audio"
            video_link = self.find_youtube(search_term)
            console.print(
                f"[magenta]({idx+1}/{len(songs)})[/magenta] Downloading '[cyan]{track_info['artist_name']} - {track_info['track_title']}[/cyan]'..."
            )
            audio = self.download_yt(video_link, idx, track_info)
            if audio:
                print(audio)
                
                self.set_metadata(track_info, audio)
                console.print(
                    "[blue]______________________________________________________________________"
                )
                downloaded += 1
            else:
                print("MP3 File exists. Skipping...")
            if self.convert_to == "wav":
                wav_file_path = self.final_path.replace('.mp3', '.wav')
                wav_file_path = wav_file_path.replace(self.folder_name, self.folder_name+" - WAV")
                # print(wav_file_path)
                song_title = os.path.basename(self.final_path).split(" - ")[2]  # Adjust the split logic based on your file naming convention
                is_age_restricted = any(song['track_title'] in self.final_path for song in self.ageRestricted)
                exists = os.path.exists(wav_file_path)
                if exists:
                    print("This WAV file already exists.")
                elif is_age_restricted:
                    print(f"{song_title} Is an Age Restricted song. Skipping")
                elif not os.path.exists(self.final_path):
                    print(f"{self.final_path} is not exist as an MP3 file. Skipping")
                else:
                    print(f"Converting to WAV File in: {wav_file_path}")
                    self.convert_mp3_to_wav(self.final_path, wav_file_path)
                    self.set_metadata(track_info, self.final_path)
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
            f"DOWNLOAD COMPLETED: {downloaded}/{len(songs)} song(s) dowloaded".center(
                70, " "
            ),
            style="on green",
        )
        if len(d) > 0:
            console.print(
                f"{len(d)} didnt Downloaded because of age restriction".center(
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
    
    def convert_mp3_to_wav(self, mp3_file_path, wav_file_path):
        """
        Converts an MP3 file to WAV format.
        
        Args:
        - mp3_file_path: The path to the input MP3 file.
        - wav_file_path: The path where the output WAV file will be saved.
        """
        # Load the MP3 audio file
        audio = AudioSegment.from_mp3(mp3_file_path)
        
        # Export the audio file in WAV format
        audio.export(wav_file_path, format="wav")
    

    def find_youtube(self, query):
        phrase = query.replace(" ", "+")
        search_link = "https://www.youtube.com/results?search_query=" + phrase
        # print(search_link)
        count = 0
        try:
            response = requests.get(search_link)
            # Check if the request was successful
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
            # Catch any requests-related exceptions
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
            "track_number": track["track_number"],
            # "isrc": track["external_ids"]["isrc"],
            "album_art": track["album"]["images"][1]["url"],
            "album_name": track["album"]["name"],
            "release_date": track["album"]["release_date"],
            "artists": [artist["name"] for artist in track["artists"]],
        }
        print(track["external_ids"]["isrc"])

        return track_metadata
    
    def create_folder_if_not_exists(self, folder_path):
        """
        This function checks if a folder exists at the specified path. 
        If the folder does not exist, it creates the folder.
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return f"Folder created at {folder_path}"
        else:
            return f"Folder already exists. {folder_path}"
    
    def prompt_exists_action(self):
        """ask the user what happens if the file being downloaded already exists"""
        global file_exists_action
        if file_exists_action == "SA":  # SA == 'Skip All'
            return False
        elif file_exists_action == "RA":  # RA == 'Replace All'
            return True

        print("This file already exists.")
        while True:
            resp = (
                input("replace[R] | replace all[RA] | skip[S] | skip all[SA]: ")
                .upper()
                .strip()
            )
            if resp in ("RA", "SA"):
                file_exists_action = resp
            if resp in ("R", "RA"):
                return True
            elif resp in ("S", "SA"):
                return False
            print("---Invalid response---")
    
    def download_yt(self, yt_link, idx, track_info):
        """download the video in mp3 format from youtube"""
        # exists = os.path.exists(f"./music/{idx} - {track_info['artist_name']} - {yt.title}.mp3")
        # if exists:
        #     print("This file already exists.")
        #     return False
        try:
            yt = YouTube(yt_link, on_progress_callback=self.on_progress)
            # download the music
            yt.title = "".join([c for c in yt.title if c not in ['/', '\\', '|', '?', '*', ':', '>', '<', '"']])
            safe_artist_name = track_info['artist_name'].replace("/", "-").replace("\\", "-")
            safe_title = yt.title.replace("/", "-").replace("\\", "-")
            self.final_path = f"./{self.folder_name}/{idx + 1} - {safe_artist_name} - {safe_title}.mp3"
            exists = os.path.exists(self.final_path)
            if exists:
                # print("This file already exists.")
                return False
            video = yt.streams.filter(only_audio=True).first()
            vid_file = video.download("./tmp/")  # By default, this saves to the current directory
        except AgeRestrictedError:
            self.ageRestricted.append(track_info)
            json_object = json.dumps(self.ageRestricted, indent=4)
 
            # Writing to sample.json
            with open("ageRestricted.json", "w") as outfile:
                outfile.write(json_object)
            print(f"Video {yt_link} is age restricted and cannot be downloaded.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        # remove chars that can't be in a windows file name
        yt.title = "".join([c for c in yt.title if c not in ['/', '\\', '|', '?', '*', ':', '>', '<', '"']])
        # don't download existing files if the user wants to skip them
        # exists = os.path.exists(f"./music/{idx} - {track_info['artist_name']} - {yt.title}.mp3")
        # if exists:
        #     print("This file already exists.")
        #     return False

        # download the music
        # video = yt.streams.filter(only_audio=True).first()
        # vid_file = video.download("./tmp/")  # By default, this saves to the current directory
        # convert the downloaded video to mp3
        base = os.path.splitext(vid_file)[0]
        audio_file = base + ".mp3"
        mp4_no_frame = AudioFileClip(vid_file)
        mp4_no_frame.write_audiofile(audio_file, logger=None)
        mp4_no_frame.close()
        os.remove(vid_file)  # Remove the original download (.mp4)
        os.replace(audio_file, self.final_path)  # Move/rename the .mp3 to the current directory
        audio_file = self.final_path
        return audio_file
    
    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_compeletion = math.floor(bytes_downloaded / total_size * 100)
        side_size = 100 - percentage_of_compeletion
        mes_len = len(str(percentage_of_compeletion)+'%')
        per_side_size = math.floor((5 - mes_len) / 2)
        print(f"{percentage_of_compeletion}%{' '* per_side_size} - |{'-'*percentage_of_compeletion}{' ' * side_size}|", end="\r")

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
            raise ValueError(
                "Can't download private playlists. Change your playlist's state to public."
            )
        print(", Done")
        tracks_list = []
        count = 0
        print("Prepering the song list", end="", flush=True)
        while count < 12:
            playlist = sp.playlist_tracks(sp_url, offset=count*100)
            # print(len(tracks_list))
            if len(playlist["items"]) == 0:
                break
            tracks_list.extend(playlist["items"])
            count += 1
        # playlist = sp.playlist_tracks(sp_url)
        tracks = [item["track"] for item in tracks_list]
        print(", Done,", f"Songs Count: {len(tracks)}")

        json_object = json.dumps(tracks, indent=4)
 
        # Writing to sample.json
        with open("tracks.json", "w") as outfile:
            outfile.write(json_object)

        tracks_info = []
        start = time.time()
        # for idx, track in enumerate(tracks):
        #     print(f"{idx+1}/{len(tracks)}", end="\r")
        #     # print(idx)
        #     track_url = f"https://open.spotify.com/track/{track['id']}"
        #     # print(track_url)
        #     track_info = self.get_track_info(track_url)
        #     tracks_info.append(track_info)
        print("Prepering the songs metadata")
        for idx, track in enumerate(tracks):
            print(f"{idx+1}/{len(tracks)}", end="\r")
            # print(track["album"]["images"][1])
            track_metadata = {
                "idx": idx,
                "artist_name": track["artists"][0]["name"],
                "track_title": track["name"],
                "track_number": track["track_number"],
                "isrc": track["external_ids"]["isrc"],
                "album_art": "",
                "album_name": track["album"]["name"],
                "release_date": track["album"]["release_date"],
                "artists": [artist["name"] for artist in track["artists"]],
            }
            if track["album"]["images"][1]["url"]:
                track_metadata["album_art"] = track["album"]["images"][1]["url"]
            if track["external_ids"]["isrc"]:
                track_metadata["isrc"] = track["external_ids"]["isrc"]
            tracks_info.append(track_metadata)

        end = time.time()
        print("Done,", f"(Time to run: {end-start} Seconds)")
        # print(end - start)

        json_object = json.dumps(tracks_info, indent=4)
 
        # Writing to sample.json
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
        # print("Checking if playlist is public", end="", flush=True)
        # if not pl["public"]:
        #     raise ValueError(
        #         "Can't download private playlists. Change your playlist's state to public."
        #     )
        # print(", Done")
        tracks_list = []
        count = 0
        print("Prepering the song list", end="", flush=True)
        offset = 0
        limit = 50  # Maximum allowed by Spotify

        while True:
            results = sp.show_episodes(sp_url, offset=offset, limit=limit)
            tracks_list.extend(results['items'])
            if results['next'] is not None:
                offset += limit
            else:
                break
        # playlist = sp.playlist_tracks(sp_url)
        print(tracks_list)
        # tracks = [item["track"] for item in tracks_list]
        print(", Done,", f"Shows Count: {len(tracks_list)}")

        json_object = json.dumps(tracks_list, indent=4)

        # Writing to sample.json
        with open("shows.json", "w") as outfile:
            outfile.write(json_object)

        tracks_info = []
        start = time.time()
        # for idx, track in enumerate(tracks):
        #     print(f"{idx+1}/{len(tracks)}", end="\r")
        #     # print(idx)
        #     track_url = f"https://open.spotify.com/track/{track['id']}"
        #     # print(track_url)
        #     track_info = self.get_track_info(track_url)
        #     tracks_info.append(track_info)
        print("Prepering the songs metadata")
        
        for idx, track in enumerate(tracks_list):
            print(f"{idx+1}/{len(tracks_list)}", end="\r")
            # print(track["album"]["images"][1])
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
            if track["images"][1]["url"]:
                track_metadata["album_art"] = track["album"]["images"][1]["url"]
            
            tracks_info.append(track_metadata)

        end = time.time()
        print("Done,", f"(Time to run: {end-start} Seconds)")
        # print(end - start)

        json_object = json.dumps(tracks_info, indent=4)
 
        # Writing to sample.json
        with open("tracks-info.json", "w") as outfile:
            outfile.write(json_object)

        return tracks_info
    
    def set_metadata(self, metadata, file_path):
        """adds metadata to the downloaded mp3 file"""

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
        print("Downloader stopped Goodbye!...")
    