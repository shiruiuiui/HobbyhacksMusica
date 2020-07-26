from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, session
)
import spotipy
from spotipy import oauth2

bp = Blueprint('spotify', __name__)

SCOPE = 'user-top-read user-read-currently-playing user-modify-playback-state user-read-playback-state'
CACHE = '.spotifycache'
# Reads client id and client secret from environment variables
sp_oauth = oauth2.SpotifyOAuth(scope=SCOPE,cache_path=CACHE )

@bp.route('/', methods=['GET'])
def login():
    # If auth token is already cached and not expired, use that else redirect
    # user to login or refresh token
    token_info = sp_oauth.get_cached_token()
    if token_info and not sp_oauth.is_token_expired(token_info):
        access_token = token_info['access_token']
        session['access_token'] = access_token
        return redirect(url_for('spotify.top_tracks'))
    else:
        login_url = sp_oauth.get_authorize_url()
        return redirect(login_url)

# After generating code, Spotify redirects to this endpoint
@bp.route('/oauth/callback', methods=['GET'])
def set_token():
    code = request.args['code']
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']
    session['access_token'] = access_token
    return redirect(url_for('spotify.top_tracks'))

# Get all of your top tracks and your currently playing song
@bp.route('/top_tracks', methods=['GET'])
def top_tracks():
    access_token = session['access_token']
    sp_api = spotipy.Spotify(access_token)
    top_tracks_result = sp_api.current_user_top_tracks()
    
    all_top_tracks = []
    for t in top_tracks_result['items']:
        top_track = {}
        top_track['artist_name'] = t['artists'][0]['name']
        top_track['track_name'] = t['name']
        top_track['album_name'] = t['album']['name']
        top_track['album_image'] = t['album']['images'][0]['url']
        top_track['track_id'] = t['id']
        all_top_tracks.append(top_track)

    current_playing = {}
    result = sp_api.current_user_playing_track()
    imgurl = []
    if result:
        current_song_result = result['item']
        current_playing['song'] = current_song_result['name']
        current_playing['image'] = current_song_result['album']['images'][0]['url']
        current_playing['artist'] = current_song_result['artists'][0]['name']
        #get the audio features of the current song playing
        audiofeat = sp_api.audio_features(tracks=[current_song_result['id']])
        print('audiofeatures', audiofeat)
        danceability = audiofeat[0]['danceability']
        imgurls= ['https://res.cloudinary.com/dqa1ouesy/image/upload/v1595698637/chill.jpg', 'https://res.cloudinary.com/dqa1ouesy/image/upload/v1595698192/Jazz.jpg',
        'https://res.cloudinary.com/dqa1ouesy/image/upload/v1595698364/Summer.jpg', 'https://res.cloudinary.com/dqa1ouesy/image/upload/v1595698305/EDM.jpg', 'https://f4.bcbits.com/img/0010300360_0']
        if danceability < 0.2: imgurl = imgurls[0]
        elif danceability >= 0.2 and danceability < 0.4: imgurl = imgurls[1]
        elif danceability >= 0.4 and danceability < 0.6: imgurl = imgurls[2]
        elif danceability >= 0.6 and danceability < 0.8: imgurl = imgurls[3]
        elif danceability >= 0.8: imgurl = imgurls[4]
    
    return render_template('top_tracks.html', top_tracks=all_top_tracks, 
    current_playing=current_playing, imgurl=imgurl)

# Add one of your top songs to the back of your queue
@bp.route('/add_to_queue/<track_id>', methods=['POST'])
def add_to_queue(track_id):
    access_token = session['access_token']
    sp_api = spotipy.Spotify(access_token)
    sp_api.add_to_queue(track_id)
    return redirect(url_for('spotify.top_tracks'))