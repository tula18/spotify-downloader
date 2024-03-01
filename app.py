playlist_id = "2QTfJGAK3svKfuo2dhQHRq"

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
 
import json, urllib.request, re

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="4c58ade0e9a74181a9e648d7dd504c5d",
                                                           client_secret="0a94e430ad87413da14e708b0901d0c2"))

curr = sp.current_user()
track = sp.track("https://open.spotify.com/track/285pBltuF7vW8TeWk8hdRR")
print(curr)
# def get_playlist_tracks(playlist_id):
#     tracks = []
#     results = sp.playlist_tracks(playlist_id)
#     while results['next']:
#         tracks.extend(results['items'])
#         results = sp.next(results)
#     tracks.extend(results['items'])
#     return tracks

# print(get_playlist_tracks(playlist_id)[0]["track"]["name"])

# json_object = json.dumps(get_playlist_tracks(playlist_id)[0]["track"], indent=4)
# with open("sample.json", "a") as outfile:
#     outfile.write(json_object)

# from pytube import YouTube 
# import os 
# inp = input("Enter the URL of the video you want to download: \n>> ")
  
# inp = inp.replace(" ", "+")
# search_link = "https://www.youtube.com/results?search_query=" + inp
# count = 0
# while count < 3:
#     try:
#         response = urllib.request.urlopen(search_link)
#         break
#     except:
#         count += 1

# search_res = re.findall(r"watch\?v=(\S{11})", response.read().decode())
# first_vid = "https://www.youtube.com/watch?v=" + search_res[0]
# print(first_vid)


# # url input from user 
# # yt = YouTube( 
# #     str(input("Enter the URL of the video you want to download: \n>> "))) 
  
# # # extract only audio 
# # video = yt.streams.filter(only_audio=True).first() 
  
# # # check for destination to save file 
# # print("Enter the destination (leave blank for current directory)") 
# # destination = str(input(">> ")) or '.'
  
# # # download the file 
# # out_file = video.download(output_path=destination) 
  
# # # save the file 
# # base, ext = os.path.splitext(out_file) 
# # new_file = base + '.mp3'
# # os.rename(out_file, new_file) 
  
# # # result of success 
# # print(yt.title + " has been successfully downloaded.")