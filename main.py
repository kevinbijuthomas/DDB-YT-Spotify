import requests
from secrets import user_id, access_token, youtube_api_key
from pprint import pprint
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl
from datetime import date, datetime

def create_playlist(name, public, description):
    response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers = {
            "Authorization": f"Bearer {access_token}"
        },
        json = {
            "name":name,
            "description":description,
            "public":public
        }
    )
    if response.status_code not in range(200, 299):
        print("Create Playlist Unsuccessful")
    else:
        r = response.json()
        print("Create Playlist Successful")
        return name

def get_song_id(track_name, artist_name):
    response = requests.get(
        f"https://api.spotify.com/v1/search?q=track%3A{track_name}+artist%3A{artist_name}&type=track&limit=10",
        headers = {
            "Authorization": f"Bearer {access_token}"
        },
    )
    if response.status_code not in range(200, 299):
        print("Search Song Unsuccessful")
        return
    else:
        r = response.json()
        print("Search Song Successful")
        return r['tracks']['items'][0]['id'] # returning id of first result

def get_playlist_id(playlist_name):
    response = requests.get(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers = {
            "Authorization": f"Bearer {access_token}"
        },
    )
    if response.status_code not in range(200, 299):
        print("Get Playlist ID Unsuccessful")
        return
    else:
        r = response.json()
        print("Get Playlist ID Successful")
        for i in r['items']:
            if i['name'] == playlist_name:
                return i['id']

def add_song_to_playlist(track_name, artist_name, playlist_name):
    playlist_id = get_playlist_id(playlist_name)
    if playlist_id == None:
        print("Could not find playlist")
        return
    song_id = get_song_id(track_name, artist_name)
    if song_id == None:
        return
    response = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris=spotify:track:{song_id}",
        headers = {
            "Authorization": f"Bearer {access_token}"
        },
    )

def get_youtube_client():
    api_service_name = "youtube"
    api_version = "v3"
    # Get credentials and create an API client
    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=youtube_api_key)
    return youtube

def get_uploads_id_from_channel(youtube, channelID):
    # returns the playlist id for uploads
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=f"UCNYJOAz1J80HEJy2HSM772Q"
    )
    response = request.execute()
    uploads_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return uploads_id

def get_video_details_from_playlist(youtube, playlistID):
    # returns list of video ids and corresponding video upload dates
    request = youtube.playlistItems().list(
        part="contentDetails",
        maxResults=100,
        playlistId=f"{playlistID}"
    )
    response = request.execute()
    video_ids, video_upload_dates = [], []
    for i in response['items']:
        video_ids.append(i['contentDetails']['videoId'])
        video_upload_dates.append(i['contentDetails']['videoPublishedAt'])

    video_details = [video_ids, video_upload_dates]
    return video_details

def get_song_details(youtube, uploads_video_ids):
    request_id = ""
    for i in uploads_video_ids:
        request_id = request_id + i + ","
    request_id = request_id[:-1]
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=request_id
    )
    response = request.execute()
    song_names, artist_names = [], []
    for i in response['items']:
        title = i['snippet']['localized']['title'].split(" - ")
        if len(title) == 2:
            artist_names.append(title[0])
            song_names.append(title[1])
    song_details = [song_names, artist_names]
    return song_details

def convert_youtube_dates(uploads_video_dates):
    # FORMATING YOUTUBE DATE TO DATETIME OBJECTS
    format_spotify = "%Y-%m-%dT%H:%M:%SZ"
    for i in range(len(uploads_video_dates)):
        uploads_video_dates[i] = datetime.strptime(uploads_video_dates[i], format_spotify)
    return uploads_video_dates

def get_video_ids_from_date_range(start_date, end_date, uploads_video_dates, uploads_video_ids):
    ids = []
    for i in range(len(uploads_video_dates)):
        if start_date <= uploads_video_dates[i] and end_date >= uploads_video_dates[i]:
            ids.append(uploads_video_ids[i])
    return ids

def main():
    youtube = get_youtube_client()
    uploads_playlist_id = get_uploads_id_from_channel(youtube, "UCNYJOAz1J80HEJy2HSM772Q") # Gets uploads from DDB channel
    uploads_video_details = get_video_details_from_playlist(youtube, uploads_playlist_id)
    uploads_video_ids = uploads_video_details[0]
    uploads_video_dates = convert_youtube_dates(uploads_video_details[1])
    valid = False
    # Validating input dates
    while not valid:
        s = input("Enter the start date (DD/MM/YYYY): ")
        e = input("Enter the end date (DD/MM/YYYY): ")
        format = "%d/%m/%Y"
        try:
          start_date = datetime.strptime(s, format)
          end_date = datetime.strptime(e, format)
        except ValueError:
          print("This is the incorrect date string format. It should be DD/MM/YYYY")
          continue
        valid = True
    uploads_video_ids = get_video_ids_from_date_range(start_date, end_date, uploads_video_dates, uploads_video_ids)
    song_details = get_song_details(youtube, uploads_video_ids)
    song_names = song_details[0]
    artist_names = song_details[1]
    playlist = create_playlist(f"DDB songs ({s} to {e})", False, f"Songs uploaded to David Dean Burkhart's channel from {s} to {e}")
    for i in range(len(song_names)):
        add_song_to_playlist(song_names[i], artist_names[i], playlist)

if __name__ == '__main__':
    main()
