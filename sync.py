import gmusicapi
import os
import time
import re

def get_songs(user, password):
    music = gmusicapi.Webclient()
    music.login(user, password)
    songs = music.get_all_songs()
    return songs

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
            badsongs.append({"name":song["name"].encode('ascii', 'ignore'), "artist":song["artist"].encode('ascii', 'ignore')})
            music.delete_songs(song["id"])
    fh_bad.close()
    return badsongs

def delete_bad_songs(songs):
    for song in songs:
        if(song["rating"]==1):
            music.delete_songs(song["id"])
    return


#This works, but it's more effective to build a tree and search that for deleting multiple songs.
def find_song_by_disk(search, path):
	files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
	folders = [os.path.join(path,f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
	finds = []
	for phile in files:
		if(len(re.findall(".*"+search+".*", phile))!=0):
			finds.append(os.path.join(path, phile))
	for folder in folders:
		ret = find_song(search, folder)
		if(len(ret) !=0):
			finds.extend(ret)
	return finds

def build_tree():
    t = tree()
    t.add_branch("C:\\.D\\Music")
    t.add_branch("C:\\Users\\Rand\\Desktop")
    t.add_branch("C:\\Users\\Rand\\Downloads")
    t.add_branch("C:\\Users\\Rand\\Music")
    return t


class treeBranch():
    def __init__(self, name):
        self.children = []
        self.files = []
        self.name = name
        self.path = ""
    def addChild(self, path):
        full_size = 0
        self.path = path
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        for phile in files:
            if(len(re.findall(".*(mp3|wav|mp4)+", phile)) != 0):
                self.files.append(phile)
                full_size+=1
        for folder in folders:
            t = treeBranch(folder)
            size = t.addChild(os.path.join(path, folder))
            full_size+=size
            self.children.append(t)
        return full_size
    def find_song(self, search):
        finds = []
        for phile in self.files:
            if(len(re.findall(".*"+search+".*", phile))!=0):
                finds.append(os.path.join(self.path, phile))
        for folder in self.children:
            ret = folder.find_song(search)
            if(len(ret)!=0):
                finds.extend(ret)
        return finds
    def song_exists(self, search):
        for phile in self.files:
            if(len(re.findall(".*"+search+".*", phile))!=0):
                return True
        ret = False
        for folder in self.children:
            ret = ret or folder.song_exists(search)
        return ret

class tree():
    def __init__(self):
        self.root = []
        self.size= 0
    def find_song(self, search):
        ret = []
        for branch in self.root:
            ret.extend(branch.find_song(search))
        return ret
    def add_branch(self, path):
        t = treeBranch(path)
        size = t.addChild(path)
        self.size += size
        self.root.append(t)
    def song_exists(self, search):
        ret = False
        for branch in self.root:
            ret = ret or branch.song_exists(search)
        return ret


print "Beginning program"

print "Building tree"
start = time.clock()
trie = build_tree()
print "Done building"
print "Time taken", time.clock()-start
print "Size is: ", trie.size

print "Getting music from google"
songs = get_songs("username@gmail.com", "password")
good_songs = get_good_songs(songs)
bad_songs = get_bad_songs(songs)
delete_bad_songs(songs)

print "Now attempting to find",
results = []
for song in bad_songs:
    if(len(song["name"]) > 3):
        print "Now attempting to find", song["name"]
        try:  
            results.extend(trie.find_song(song["name"]))
        except:
            print "Failed to get", song["name"]
    else:
        print "Song name is too short"

for result in results:
    response = raw_input( "Do you want to delete"+ result+"? (y/n): ")
    if(response=="n"):
        print "Not deleted"
    else:
        os.remove(result)

print "Completed"
