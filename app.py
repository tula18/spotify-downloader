import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json

# Authentication - without user
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="3c1b217c1a6a49cea3789ab3b503d211", client_secret="38b6b43d6b6b46d3800a7322a93f5cf4"))

def get_all_show_episodes(show_id):
    episodes = []
    offset = 0
    limit = 50  # Maximum allowed by Spotify

    while True:
        results = sp.show_episodes(show_id, offset=offset, limit=limit)
        episodes.extend(results['items'])
        if results['next'] is not None:
            offset += limit
        else:
            break

    return episodes

# Example usage
show_id = 'https://open.spotify.com/show/2hm3NRGFO5rRVDEhA0stZI?si=4c2cc90fbac9414a'  # Replace with the show's Spotify ID
episodes = get_all_show_episodes(show_id)
episodes_json = json.dumps(episodes, indent=4)  # Convert the list of episodes to a JSON string

# Print or save the JSON
print(episodes_json) 
print(f"Found {len(episodes)} episodes.")

# Process the episodes as needed
for episode in episodes:
    print(episode['name'])  # Example: print each episode's name