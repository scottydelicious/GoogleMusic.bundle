import random
from gmusic import GMusic, CallFailure

ART            = 'art-default.jpg'
ICON           = 'icon-default.png'
SEARCH_ICON    = 'icon-search.png'
PREFS_ICON     = 'icon-prefs.png'
PREFIX         = '/music/googlemusic'
API            = GMusic()

################################################################################
def Prettify(str):
    return str.lower().replace('_', ' ').title()

################################################################################
def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = L('Title')
    DirectoryObject.thumb = R(ICON)
    ArtistObject.thumb = R(ICON)
    AlbumObject.thumb = R(ICON)
    TrackObject.thumb = R(ICON)

################################################################################
def ValidatePrefs():
    return True

################################################################################
@handler(PREFIX, L('Title'), art=ART, thumb=ICON)
def MainMenu():
    oc = ObjectContainer(title2=L('Title'))

    if Prefs['email'] and Prefs['password']:
        if API.authenticate(Prefs['email'], Prefs['password']):
            oc.add(DirectoryObject(key=Callback(LibraryMenu), title=L('My Library')))
            oc.add(DirectoryObject(key=Callback(PlaylistsMenu), title=L('Playlists')))
            oc.add(DirectoryObject(key=Callback(StationsMenu), title=L('Stations')))

            if API.all_access:
                oc.add(DirectoryObject(key=Callback(GenresMenu), title=L('Genres')))
                oc.add(InputDirectoryObject(key=Callback(SearchMenu), title=L('Search'), prompt=L('Search Prompt'), thumb=R(SEARCH_ICON)))

    oc.add(PrefsObject(title=L('Prefs Title'), thumb=R(PREFS_ICON)))
    return oc

################################################################################
@route(PREFIX + '/{name}/recentlyAdded')
def RecentlyAdded(name, stack):
    return ObjectContainer(title2=L('Title'))

################################################################################
@route(PREFIX + '/librarymenu')
def LibraryMenu():
    oc = ObjectContainer(title2=L('My Library'))
    oc.add(DirectoryObject(key=Callback(LibrarySubMenu, title='Artists'), title=L('Artists')))
    oc.add(DirectoryObject(key=Callback(LibrarySubMenu, title='Albums'), title=L('Albums')))
    oc.add(DirectoryObject(key=Callback(ShowSongs, title='Songs'), title=L('Songs')))
    oc.add(DirectoryObject(key=Callback(LibrarySubMenu, title='Genres'), title=L('Genres')))
    oc.add(DirectoryObject(key=Callback(ShowSongs, title='Shuffle All', shuffle=True), title=L('Shuffle All')))

    return oc

################################################################################
@route(PREFIX + '/playlistsmenu')
def PlaylistsMenu():
    oc = ObjectContainer(title2=L('Playlists'))

    playlists = API.get_all_playlists()
    for playlist in playlists:
        if 'type' in playlist and playlist['type'].lower() == 'user_generated':
            oc.add(DirectoryObject(key=Callback(GetTrackList, name=playlist['name'], id=playlist['id']), title=playlist['name']))
        else:
            oc.add(DirectoryObject(key=Callback(GetSharedPlaylist, name=playlist['name'], token=playlist['shareToken']), title=playlist['name']))

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

################################################################################
@route(PREFIX + '/stationsmenu')
def StationsMenu():
    oc = ObjectContainer(title2=L('Stations'))
    oc.add(DirectoryObject(key=Callback(GetStationTracks, name=L('Lucky Radio'), id='IFL'), title=L('Lucky Radio')))

    stations = API.get_all_stations()
    for station in stations:
        do = DirectoryObject(key=Callback(GetStationTracks, name=station['name'], id=station['id']), title=station['name'])
        if 'imageUrl' in station:
            do.thumb = station['imageUrl']
        oc.add(do)

    return oc

################################################################################
@route(PREFIX + '/genresmenu')
def GenresMenu():
    oc = ObjectContainer(title2=L('Genres'))

    genres = API.get_genres()
    for genre in genres['genres']:
        if 'children' in genre:
            children = genre['children']
        else:
            children = None
        do = DirectoryObject(key=Callback(GenresSubMenu, name=genre['name'], id=genre['id'], children=children), title=genre['name'])
        if 'images' in genre:
            do.thumb = genre['images'][0]['url']
        oc.add(do)

    return oc

################################################################################
@route(PREFIX + '/searchmenu')
def SearchMenu(query):
    oc = ObjectContainer(title2=L('Search'))

    results = API.search_all_access(query)
    for key, values in results.iteritems():
        if key == 'song_hits':
            for song in values:
                oc.add(GetTrack(song['track'], song['track']['nid']))

        if key == 'artist_hits':
            for artist in values:
                artist = artist['artist']
                artistObj = ArtistObject(
                    key=Callback(GetArtistInfo, name=artist['name'], id=artist['artistId']),
                    rating_key=artist['artistId'],
                    title=artist['name']
                )
                if 'artistArtRef' in artist:
                    artistObj.thumb = artist['artistArtRef']

                oc.add(artistObj)

        if key == 'album_hits':
            for album in values:
                album = album['album']
                albumObj = AlbumObject(
                    key=Callback(GetAlbumInfo, name=album['name'], id=album['albumId']),
                    rating_key=album['albumId'],
                    artist=album['artist'],
                    title=album['name']
                )

                if 'albumArtRef' in album:
                    albumObj.thumb = album['albumArtRef']

                oc.add(albumObj)

    return oc

################################################################################
@route(PREFIX + '/librarysubmenu')
def LibrarySubMenu(title):
    oc = ObjectContainer(title2=L(title))
    items = {}

    if title == 'Artists':
        items = API.get_all_artists()
    elif title == 'Albums':
        items = API.get_all_albums()
    elif title == 'Genres':
        items = API.get_all_genres()

    for key, value in items.iteritems():
        do = DirectoryObject(key=Callback(GetTrackList, name=key, tracks=value), title=key)
        if 'thumb' in value[0]:
            do.thumb = value[0]['thumb']
        oc.add(do)

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

################################################################################
@route(PREFIX + '/showsongs', shuffle=bool)
def ShowSongs(title, shuffle=False):
    oc = ObjectContainer(title2=L(title))

    songs = API.get_all_songs()
    for song in songs:
        oc.add(GetTrack(song, song['id']))

    if shuffle == True:
        random.shuffle(oc.objects)
    else:
        oc.objects.sort(key=lambda obj: obj.title)

    return oc

################################################################################
@route(PREFIX + '/gettracklist', tracks=list)
def GetTrackList(name, id=None, tracks=None):
    oc = ObjectContainer(title2=name)

    if id and tracks == None:
        tracks = API.get_all_user_playlist_contents(id)

    for track in tracks:
        if 'track' in track:
            data = track['track']
        else:
            data = API.get_all_songs(track['trackId'])

        oc.add(GetTrack(data, track['id']))

    return oc

################################################################################
@route(PREFIX + '/getsharedplaylist')
def GetSharedPlaylist(name, token):
    oc = ObjectContainer(title2=name)

    tracks = API.get_shared_playlist_contents(token)
    for track in tracks:
        oc.add(GetTrack(track['track'], track['trackId']))

    return oc

################################################################################
@route(PREFIX + '/getstationtracks')
def GetStationTracks(name, id):
    oc = ObjectContainer(title2=name)

    tracks = API.get_station_tracks(id)
    for track in tracks:
        if API.all_access:
            if 'nid' in track:
                id = track['nid']
            else:
                id = track['id']
        else:
            id = track['id']
        oc.add(GetTrack(track, id))

    return oc

################################################################################
@route(PREFIX + '/genressubmenu', children=list)
def GenresSubMenu(name, id, children=None):
    oc = ObjectContainer(title2=name)
    oc.add(DirectoryObject(key=Callback(CreateStation, id=id), title='Play ' + name))

    if children != None:
        for child in children:
            oc.add(DirectoryObject(key=Callback(CreateStation, id=child), title='Play ' + Prettify(child)))
    return oc

################################################################################
@route(PREFIX + '/createstation')
def CreateStation(id):
    name = Prettify(id)
    station = API.create_station(name, id)
    return GetStationTracks(name=name, id=station)

################################################################################
@route(PREFIX + '/getartistinfo')
def GetArtistInfo(name, id):
    oc = ObjectContainer(title2=name)

    artist = API.get_artist_info(id)
    for album in sorted(artist['albums'], key = lambda x: x.get('year')):
        albumObj = AlbumObject(
            key=Callback(GetAlbumInfo, name=album['name'], id=album['albumId']),
            rating_key=album['albumId'],
            artist=album['artist'],
            title=album['name']
        )

        if 'albumArtRef' in album:
            albumObj.thumb = album['albumArtRef']

        oc.add(albumObj)

    return oc

################################################################################
@route(PREFIX + '/getalbuminfo')
def GetAlbumInfo(name, id):
    oc = ObjectContainer(title2=name)

    album = API.get_album_info(id)
    for track in album['tracks']:
        oc.add(GetTrack(track, track['nid']))

    return oc

################################################################################
@route(PREFIX + '/gettrack', song=dict)
def GetTrack(song, key, include_container=False):
    storeId = song['storeId'] if 'storeId' in song and API.all_access else 0
    id = song['id'] if 'id' in song else 0

    track = TrackObject(
        key = Callback(GetTrack, song=song, key=key, include_container=True),
        rating_key = key,
        title = song['title'],
        album = song['album'],
        artist = song['artist'],
        duration = int(song['durationMillis']),
        index = int(song.get('trackNumber', 0)),
        items = [
            MediaObject(
                parts = [PartObject(key=Callback(PlayAudio, id=id, storeId=storeId, ext='mp3'))],
                container = Container.MP3,
                audio_codec = AudioCodec.MP3
            )
        ]
    )

    if 'albumArtRef' in song:
        track.thumb = song['albumArtRef'][0]['url']

    if include_container:
        return ObjectContainer(objects=[track])
    else:
        return track

################################################################################
@route(PREFIX + '/playaudio.mp3')
def PlayAudio(id, storeId):
    if storeId != 0:
        try:
            song_url = API.get_stream_url(storeId)
        except CallFailure:
            song_url = API.get_stream_url(id)
    else:
        song_url = API.get_stream_url(id)

    return Redirect(song_url)
