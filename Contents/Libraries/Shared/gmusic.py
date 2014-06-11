from gmusicapi import Webclient, Mobileclient
from gmusicapi.protocol import webclient
from gmusicapi.exceptions import AlreadyLoggedIn, NotLoggedIn, CallFailure

class GMusic(object):
    def __init__(self):
        self.authenticated = False
        self.all_access = False
        self.can_stream = True
        self._device = None
        self._webclient = Webclient(debug_logging=False)
        self._mobileclient = Mobileclient(debug_logging=False)
        self._playlists = []
        self._playlist_contents = []
        self._all_songs = []
        self._all_artists = {}
        self._all_albums = {}
        self._all_genres = {}
        self._stations = []

    def _get_device_id(self):
        if self.authenticated:
            devices = self._webclient.get_registered_devices()
            for dev in devices:
                if dev['type'] == 'PHONE':
                    self._device = dev['id'][2:]
                    break
                elif dev['type'] == 'IOS':
                    self._device = dev['id']
                    break
                else:
                    raise CallFailure('No registered devices could be found for your account')

    def _set_all_access(self):
        settings = self._webclient._make_call(webclient.GetSettings, '')
        self.all_access = True if 'isSubscription' in settings['settings'] and settings['settings']['isSubscription'] == True else False

    def authenticate(self, email, password):
        try:
            mcauthenticated = self._mobileclient.login(email, password)
        except AlreadyLoggedIn:
            mcauthenticated = True

        try:
            wcauthenticated = self._webclient.login(email, password)
        except AlreadyLoggedIn:
            wcauthenticated = True

        self.authenticated = mcauthenticated and wcauthenticated
        self._set_all_access()

        try:
            self._get_device_id()
        except CallFailure:
            self.can_stream = False

        return self.authenticated

    def get_all_songs(self, id=None):
        if len(self._all_songs) == 0:
            try:
                self._all_songs = self._mobileclient.get_all_songs()
            except NotLoggedIn:
                if self.authenticate():
                    self._all_songs = self._mobileclient.get_all_songs()
                else:
                    return []

        if id:
            return [x for x in self._all_songs if x['id'] == id][0]
        else:
            return self._all_songs

    def get_all_artists(self):
        if not self._all_artists:
            songs = self.get_all_songs()
            for song in songs:
                artist = song['artist']
                thumb = None
                if artist not in self._all_artists:
                    self._all_artists[artist] = []

                track = {'title': song['title'],
                        'album': song['album'],
                        'artist': artist,
                        'durationMillis': song['durationMillis'],
                        'trackType': song['trackNumber'],
                        'id': song['id']}

                if 'albumArtRef' in song:
                    track['albumArtRef'] = song['albumArtRef']

                if 'artistArtRef' in song:
                    thumb = song['artistArtRef'][0]['url']

                if 'storeId' in song:
                    track['storeId'] = song['storeId']

                self._all_artists[artist].append({'track': track, 'thumb': thumb, 'id': song['id']})

        return self._all_artists

    def get_all_albums(self):
        if not self._all_albums:
            songs = self.get_all_songs()
            for song in songs:
                album = song['album']
                thumb = None
                if album not in self._all_albums:
                    self._all_albums[album] = []

                track = {'title': song['title'],
                        'album': album,
                        'artist': song['artist'],
                        'durationMillis': song['durationMillis'],
                        'trackType': song['trackNumber'],
                        'id': song['id']}

                if 'albumArtRef' in song:
                    track['albumArtRef'] = song['albumArtRef']
                    thumb = song['albumArtRef'][0]['url']

                if 'storeId' in song:
                    track['storeId'] = song['storeId']

                self._all_albums[album].append({'track': track, 'thumb': thumb, 'id': song['id']})

        return self._all_albums

    def get_all_genres(self):
        if not self._all_genres:
            songs = self.get_all_songs()
            for song in songs:
                genre = song['genre']
                if genre not in self._all_genres:
                    self._all_genres[genre] = []

                track = {'title': song['title'],
                        'album': song['album'],
                        'artist': song['artist'],
                        'durationMillis': song['durationMillis'],
                        'trackType': song['trackNumber'],
                        'id': song['id']}

                if 'albumArtRef' in song:
                    track['albumArtRef'] = song['albumArtRef']

                if 'storeId' in song:
                    track['storeId'] = song['storeId']

                self._all_genres[genre].append({'track': track, 'id': song['id']})

        return self._all_genres

    def get_all_playlists(self):
        if len(self._playlists) == 0:
            try:
                self._playlists = self._mobileclient.get_all_playlists()
            except NotLoggedIn:
                if self.authenticate():
                    self._playlists = self._mobileclient.get_all_playlists()
                else:
                    return []

        return self._playlists

    def get_all_user_playlist_contents(self, id):
        tracks = []
        if len(self._playlist_contents) == 0:
            try:
                self._playlist_contents = self._mobileclient.get_all_user_playlist_contents()
            except NotLoggedIn:
                if self.authenticate():
                    self._playlist_contents = self._mobileclient.get_all_user_playlist_contents()
                else:
                    return []

        for playlist in self._playlist_contents:
            if id == playlist['id']:
                tracks = playlist['tracks']
                break

        return tracks

    def get_shared_playlist_contents(self, token):
        playlist = []
        try:
            playlist = self._mobileclient.get_shared_playlist_contents(token)
        except NotLoggedIn:
            if self.authenticate():
                playlist = self._mobileclient.get_shared_playlist_contents(token)
            else:
                return []

        return playlist

    def get_all_stations(self):
        if len(self._stations) == 0:
            try:
                self._stations = self._mobileclient.get_all_stations()
            except NotLoggedIn:
                if self.authenticate():
                    self._stations = self._mobileclient.get_all_stations()
                else:
                    return []

        return self._stations

    def get_station_tracks(self, id, num_tracks=200):
        tracks = []
        try:
            tracks = self._mobileclient.get_station_tracks(id, num_tracks)
        except NotLoggedIn:
            if self.authenticate():
                tracks = self._mobileclient.get_station_tracks(id, num_tracks)
            else:
                return []

        return tracks

    def get_genres(self):
        genres = []
        try:
            genres = self._mobileclient.get_genres()
        except NotLoggedIn:
            if self.authenticate():
                genres = self._mobileclient.get_genres()
            else:
                return []

        return genres

    def create_station(self, name, id):
        station = None
        try:
            station = self._mobileclient.create_station(name=name, genre_id=id)
        except NotLoggedIn:
            if self.authenticate():
                station = self._mobileclient.create_station(name=name, genre_id=id)
            else:
                return []

        return station

    def search_all_access(self, query, max_results=50):
        results = None
        try:
            results = self._mobileclient.search_all_access(query, max_results)
        except NotLoggedIn:
            if self.authenticate():
                results = self._mobileclient.search_all_access(query, max_results)
            else:
                return []

        return results

    def get_artist_info(self, id, include_albums=True, max_top_tracks=5, max_rel_artist=5):
        results = None
        try:
            results = self._mobileclient.get_artist_info(id, include_albums=include_albums, max_top_tracks=max_top_tracks, max_rel_artist=max_rel_artist)
        except NotLoggedIn:
            if self.authenticate():
                results = self._mobileclient.get_artist_info(id, include_albums=include_albums, max_top_tracks=max_top_tracks, max_rel_artist=max_rel_artist)
            else:
                return []

        return results

    def get_album_info(self, id, include_tracks=True):
        results = None
        try:
            results = self._mobileclient.get_album_info(id, include_tracks=include_tracks)
        except NotLoggedIn:
            if self.authenticate():
                results = self._mobileclient.get_album_info(id, include_tracks=include_tracks)
            else:
                return []

        return results

    def get_stream_url(self, id):
        try:
            stream_url = self._mobileclient.get_stream_url(id, self._device)
        except NotLoggedIn:
            if self.authenticate():
                stream_url = self._mobileclient.get_stream_url(id, self._device)
            else:
                return ''
        except CallFailure:
            raise CallFailure('Could not play song with id: ' + id, 'get_stream_url')

        return stream_url