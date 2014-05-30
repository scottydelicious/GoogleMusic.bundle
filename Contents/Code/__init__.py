import random
from gmusic import GMusic

ART     = 'art-default.jpg'
ICON    = 'icon-default.png'
PREFIX  = '/music/googlemusic'
API     = GMusic()

################################################################################
def Prettify(str):
    return str.lower().title().replace('_', ' ')

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
            oc.add(DirectoryObject(key=Callback(GenresMenu), title=L('Genres')))
            oc.add(InputDirectoryObject(key=Callback(SearchMenu), title=L('Search'), prompt=L('Search Prompt')))

    oc.add(PrefsObject(title=L('Prefs Title')))
    return oc

################################################################################
@route(PREFIX + '/showlibrary')
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
    for playlist in sorted(playlists, key = lambda x: x.get('name')):
        if playlist['type'].lower() == 'user_generated':
            oc.add(DirectoryObject(key=Callback(GetTrackList, name=playlist['name'], id=playlist['id']), title=playlist['name']))
        else:
            oc.add(DirectoryObject(key=Callback(GetSharedPlaylist, name=playlist['name'], token=playlist['shareToken']), title=playlist['name']))

    return oc

################################################################################
@route(PREFIX + '/stationsmenu')
def StationsMenu():
    oc = ObjectContainer(title2=L('Stations'))

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
@route(PREFIX + '/showartists')
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
    for song in sorted(songs, key = lambda x: x.get('title')):
        oc.add(GetTrack(song, song['id']))

    if shuffle == True:
        random.shuffle(oc.objects)

    return oc

################################################################################
@route(PREFIX + '/gettracklist', tracks=dict)
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
        oc.add(GetTrack(track, track['nid']))

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
    if 'storeId' in song:
        id = song['storeId']
    else:
        id = song['id']

    track = TrackObject(
        key = Callback(GetTrack, song=song, key=key, include_container=True),
        rating_key = key,
        title = song['title'],
        album = song['album'],
        artist = song['artist'],
        duration = int(song['durationMillis']),
        index = int(song.get('trackType', 0)),
        items = [
            MediaObject(
                parts = [PartObject(key=Callback(PlayAudio, id=id, ext='mp3'))],
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
@route(PREFIX + '/playaudio')
def PlayAudio(id):
    song_url = API.get_stream_url(id)
    return Redirect(song_url)
