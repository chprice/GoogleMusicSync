import gmusicapi
import os
import time
import re
from mutagen.id3 import ID3, POPM

def get_good_songs(songs):
    goodsongs = []
    for song in songs:
        if(song["rating"]==5):
            goodsongs.append({"name":song["name"].encode('ascii', 'ignore'), "artist":song["artist"].encode('ascii', 'ignore')})
    return goodsongs

def get_bad_songs(songs):
    fh_bad = open("bad_songs.txt", "a")
    badsongs = []
    for song in songs:
        if(song["rating"]==1):
            fh_bad.write(song["name"].encode('ascii', 'ignore')+"::"+song["artist"].encode('ascii', 'ignore')+"\n")
            song["name"] = song["name"].encode('ascii', 'ignore')
            song["artist"] = song["artist"].encode('ascii', 'ignore')
            badsongs.append(song)
    fh_bad.close()
    return badsongs

def delete_bad_songs(bad_songs, google_music): 
    google_music.delete_songs([song['id'] for song in bad_songs])

def set_local_rating_fivestars(songfile):
    audio = ID3()
    audio.load(songfile, translate= False, v2_version=3)
    frame = POPM(email="Windows Media Player 9 Series", rating=255)
    audio.add(frame)
    audio.save(songfile, v1=1, v2_version=3)

def set_remote_rating_thumbup(google_music, songs):
    for song in songs:
        song['rating'] = 5
    google_music.change_song_metadata(songs)

def get_local_info(song_info):
    song_info['rating'] = -1
    song_info['title'] = song_info['filename']
    song_info['artist'] = ''
    if(song_info['type'] == 'mp3'):
        try:
            audio = ID3(song_info['path'])
            rate_temp = audio.getall('POPM')
            if(len(rate_temp) >= 1):
                song_info['rating'] = rate_temp[0].rating
            song_info['title'] = audio.get('TIT2').text[0]
            song_info['artist'] = audio.get('TPE1').text[0]
        except:
            return
    else:
        return

def get_remote_info(google_music_dict, song_info):
    if (song_info['title'], song_info['artist']) in google_music_dict:
        return google_music_dict[(song_info['title'], song_info['artist'])]
    else:
        return {}

def build_dict():
    t = MusicDict()
    t.add_folder("C:\\.D\\Music")
    #t.add_folder("C:\\Users\\Random\\Desktop")
    #t.add_folder("C:\\Users\\Random\\Downloads")
    #t.add_folder("C:\\Users\\Random\\Music")
    return t


# songs: (title, artist) = [rating, path, title, artist]
class MusicDict():
    def __init__(self):
        self.songs = {}
        self.size= 0
        
    def find_song(self, title, artist=''):
        if (title, artist) in self.songs:
            return self.songs[(title, artist)]
        return {}
        
    def add_folder(self, path):
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        for phile in files:
            if(len(re.findall(".*(mp3|wav|mp4)+", phile)) != 0):
                file_info = {'path': os.path.join(path, phile), 'filename': phile}
                if('wav' in phile):
                    file_info['type'] = 'wav'
                if('mp4' in phile):
                    file_info['type'] = 'mp4'
                if('mp3' in phile):
                    file_info['type'] = 'mp3'
                get_local_info(file_info)
                self.songs[(file_info['title'], file_info['artist'])] = file_info
                self.size+=1
                if(self.size % 1000 == 0):
                    print self.size, " songs found"
        for folder in folders:
            self.add_folder(os.path.join(path, folder))
            
    def song_exists(self, title, artist=''):
        return (title, artist) in self.songs


print "Beginning program"

print "Building dictionary of songs on computer"
start = time.clock()
music_dict = build_dict()
print "Done building"
print "Time taken", time.clock()-start
print "Songs found: ", music_dict.size

start = time.clock()
print "Getting music from google"
google_music = gmusicapi.Webclient()
google_music.login("username@gmail.com", "password")
google_songs = google_music.get_all_songs()
google_songs_dict = {}
print "Time taken", time.clock()-start

print 'Putting google songs in a dictionary'
for song in google_songs:
    google_songs_dict[(song["name"].encode('ascii', 'ignore'), song["artist"].encode('ascii', 'ignore'))] = song

print 'Getting good songs from google'
good_songs = get_good_songs(google_songs)
print 'Getting bad songs from google'
bad_songs = get_bad_songs(google_songs)

print "Finding all songs rated up on google play and updating on computer."
for song in good_songs:
    if music_dict.song_exists(song["name"].encode('ascii', 'ignore'), song["artist"].encode('ascii', 'ignore')):
        local_song = music_dict.find_song(song["name"].encode('ascii', 'ignore'), song["artist"].encode('ascii', 'ignore'))
        try:
            set_local_rating_fivestars(local_song['path'])
            print song["name"].encode('ascii', 'ignore') + ' by '+ song["artist"].encode('ascii', 'ignore')+' was given 5 stars.'
        except Exception as e:
            print e

print "Finding all songs rated up on computer and updating google play."
google_music_songs = []
for song_info in music_dict.songs.values():
    if(song_info['rating'] == 255):
        remote_song_info = get_remote_info(google_songs_dict, song_info)
        if(remote_song_info != {}):
            google_music_songs.append(remote_song_info)
try:
    set_remote_rating_thumbup(google_music, google_music_songs)
except Exception as e:
    print e

print "Finding all songs that are rated down on google play on this computer."
for song in bad_songs:
    if(music_dict.song_exists(song['name'], song['artist'])):
        response = raw_input( "Do you want to delete "+ song['name']+ ' by '+ song['artist']+"? (y/n): ")
        if(response=="n"):
            print "Not deleted"
        else:
            song_info = music_dict.find_song(song['name'], song['artist'])
            os.remove(song_info['path'])
    else:
        print "Could not find ", song['name'], " by ", song['artist']

print 'Deleting bad songs from google'
delete_bad_songs(bad_songs, google_music)

print "Removing music from google play that does not exist on computer."
delete_songs = []
for song in google_songs:
    if song['rating']!= 5 and not music_dict.song_exists(song["name"].encode('ascii', 'ignore'), song["artist"].encode('ascii', 'ignore')):
        print "Deleting "+song["name"].encode('ascii', 'ignore')+" by "+song["artist"].encode('ascii', 'ignore')+" remotely"
        #response = raw_input("Do you want to delete this song? (y/n): ")
        response = 'y'
        if(response!="n"):
                delete_songs.append(song["id"])
try:
    google_music.delete_songs(delete_songs)
except Exception as e:
    print e

print "Completed"
