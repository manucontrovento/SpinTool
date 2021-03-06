import numpy as np
import soundfile as sf
from PyQt5 import QtCore
import configparser, json
from zipfile import ZipFile
from io import BytesIO, StringIO, TextIOWrapper
from collections import OrderedDict as OrderedDict_
import unicodedata
import settings
import common
import copy
from superboucle.mixer import Mixer


class OrderedDict(OrderedDict_):
    def insert(self, key, value, index=-1):
        move_keys = list(self.keys())[index:]
        self[key] = value
        for k in move_keys:
            self.move_to_end(k)


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def basename(s):
    if s is None:
        return None
    else:
        str = strip_accents(s)
        return str.split('/')[-1]


def verify_ext(file, ext):
    if file[-4:] == (".%s" % ext):
        return file
    else:
        return "%s.%s" % (file, ext)


class Communicate(QtCore.QObject):
    updateUI = QtCore.pyqtSignal()


class Clip():
    STOP = 0
    STARTING = 1
    START = 2
    STOPPING = 3
    PREPARE_RECORD = 4
    RECORDING = 5

    TRANSITION = {STOP: STARTING,
                  STARTING: STOP,
                  START: STOPPING,
                  STOPPING: START,
                  PREPARE_RECORD: RECORDING,
                  RECORDING: PREPARE_RECORD}
    
    RECORD_TRANSITION = {STOP: PREPARE_RECORD,
                         PREPARE_RECORD: STOP,
                         STARTING: STOP,
                         START: STOP,
                         STOPPING: STOP,
                         RECORDING: STOP}      
    
    STATE_DESCRIPTION = {0: "STOP",
                         1: "STARTING",
                         2: "START",
                         3: "STOPPING",
                         4: "PREPARE_RECORD",
                         5: "RECORDING"}

    def __init__(self, audio_file=None, name='',
                 volume=1, 
                 frame_offset=0, beat_offset=0.0, beat_diviser=1,
                 output=common.DEFAULT_PORT, 
                 mute_group=0, one_shot = False, lock_rec = False, always_play = False):

        if name == '' and audio_file:
            self.name = audio_file
        else:
            self.name = name
            
        self.volume = volume
        self.frame_offset = frame_offset
        self.beat_offset = beat_offset
        self.beat_diviser = beat_diviser
        self.state = Clip.STOP
        self.audio_file = audio_file

        # clip playhead
        self.last_offset = 0

        self.output = output
        self.mute_group = mute_group
        self.one_shot = one_shot
        self.always_play = always_play
        self.lock_rec = lock_rec
        self.shot = False   # When one_shot clip is shot, this becomes True
        self.selected = False

    def stop(self):
        self.state = Clip.STOPPING if self.state == Clip.START \
            else Clip.STOP if self.state == Clip.STARTING \
            else self.state

    def start(self):
        if self.one_shot == True:
            self.shot = False
            
        self.state = Clip.STARTING if self.state == Clip.STOP \
            else Clip.START if self.state == Clip.STOPPING \
            else self.state




class Song():

    def __init__(self, 
                 width, 
                 height, 
                 volume = 1.0, 
                 bpm = 120, 
                 beat_per_bar = 4):
        self.clips_matrix = [[None for y in range(height)]
                             for x in range(width)]

        self.clips = []
        self.data, self.samplerate = {}, {}

        # song volume
        self.volume = volume #1.0

        self.bpm = bpm #120
        self.beat_per_bar = beat_per_bar #4
        self.width = width
        self.height = height
        self.file_name = None
        self.is_record = False
        self.scenes = OrderedDict()
        self.initial_scene = None
        self.annotation = ""
        self.initial_row_with_clips = 0


    def addScene(self, name, clip_start = True, clip_selected = False):
        # if clip_start == True: includes clips in state Start / starting
        # if clip_selected == True: includes clips Selected from user (shift + left click)        
        clip_ids = [i for i, c in enumerate(self.clips) if
                    (((c.state == Clip.START or c.state == Clip.STARTING) and clip_start == True) or
                      (c.selected == True and clip_selected == True))]
        self.scenes[name] = clip_ids

    def renameScene(self, old_name, new_name): ##### TESTA SE FUNZIONA!
        old_scenes = copy.deepcopy(self.scenes)
        self.scenes = common.renameDictItem(old_scenes, old_name, new_name)

    def removeScene(self, name):
        del self.scenes[name]

    def getSceneDesc(self, name):
        res = [[None for y in range(self.height)]
                    for x in range(self.width)]
        clip_ids = self.scenes[name]
        for i, c in enumerate(self.clips):
            res[c.x][c.y] = i in clip_ids
        return res

    def loadScene(self, name):
        clip_ids = self.scenes[name]
        self._loadScene(clip_ids)

    def loadSceneId(self, index):
        clip_ids = list(self.scenes.values())[index]
        self._loadScene(clip_ids)

    def _loadScene(self, clip_ids):
        for i, c in enumerate(self.clips):
            if i in clip_ids:
                c.start()
            else:
                c.stop()
                
    # ------------------------------------------------------------------------------------------

    def _stopAllClips(self):
        for i, c in enumerate(self.clips):
            c.stop()        

    # sets all Clips in Stop state
    def stopAllClips(self):
        self._stopAllClips()

    # returns selected clips
    def selectedClips(self):
        selected_clips = []

        for x in range(self.width):
            for y in range(self.height):
                clip = self.clips_matrix[x][y]
                if clip and clip.selected == True:
                    selected_clips.append(clip)
        
        return selected_clips

    def addClip(self, clip, x, y):
        if self.clips_matrix[x][y]:
            self.clips.remove(self.clips_matrix[x][y])
        self.clips_matrix[x][y] = clip
        self.clips.append(clip)
        clip.x = x
        clip.y = y

    def removeClip(self, clip):
        if clip.audio_file is not None:
            current_audio_file = clip.audio_file
            clip.audio_file = None
            if current_audio_file not in [c.audio_file for c in self.clips]:
                del self.data[current_audio_file]

        self.clips_matrix[clip.x][clip.y] = None
        self.clips.remove(clip)

    def toggle(self, x, y):
        clip = self.clips_matrix[x][y]
        if clip is None:
            return
        if self.is_record:
            clip.state = Clip.RECORD_TRANSITION[clip.state]
        else:
            clip.state = Clip.TRANSITION[clip.state]
            
            if clip.one_shot == True:
                clip.shot = False
            
            if clip.mute_group:
                for c in self.clips:
                    if c and c.mute_group == clip.mute_group and c != clip:
                        c.stop()

    def channels(self, clip):
        '''Return channel count for specified clip'''
        if clip.audio_file is None:
            return 0
        else:
            return self.data[clip.audio_file].shape[1]

    def length(self, clip):
        if clip.audio_file is None:
            return 0
        else:
            return self.data[clip.audio_file].shape[0]
    

    def getData(self, clip, channel, offset, length):
        if clip.audio_file is None:
            return []

        channel %= self.channels(clip)
        if offset > (self.length(clip) - 1) or offset < 0 or length < 0:
            raise Exception("Invalid length or offset: {0} {1} {2}".
                            format(length, offset, self.length(clip)))
        if (length + offset) > self.length(clip):
            raise Exception("Index out of range : {0} + {1} > {2}".
                            format(length, offset, self.length(clip)))

        return (self.data[clip.audio_file][offset:offset + length, channel]
                * clip.volume)

    def writeData(self, clip, channel, offset, data):
        if clip.audio_file is None:
            raise Exception("No audio buffer available")

        if offset + data.shape[0] > self.length(clip):
            data = data[0:data.shape[0] - 2]


        self.data[clip.audio_file][offset:offset + data.shape[0],
        channel] = data


    def init_record_buffer(self, clip, channel, size, samplerate):
        i = 0
        audio_file_base = basename(clip.name) or 'audio'

        # remove old audio if not used
        if clip.audio_file is not None:
            current_audio_file = clip.audio_file
            clip.audio_file = None
            if current_audio_file not in [c.audio_file for c in self.clips]:
                del self.data[current_audio_file]

        while '%s-%02d.wav' % (audio_file_base, i) in self.data:
            i += 1
        audio_file = '%s-%02d.wav' % (audio_file_base, i)
        self.data[audio_file] = np.zeros((size, channel),
                                         dtype=np.float32)
        self.samplerate[audio_file] = samplerate
        clip.audio_file = audio_file

    def save(self):
        if self.file_name:
            self.saveTo(self.file_name)
        else:
            raise Exception("No file specified")

    def saveTo(self, file):
        
        with ZipFile(file, 'w') as zip:
            song_file = configparser.ConfigParser()
            song_file['DEFAULT'] = {'volume': self.volume,
                                    'annotation': self.annotation,
                                    'bpm': self.bpm,
                                    'beat_per_bar': self.beat_per_bar,
                                    'width': self.width,
                                    'height': self.height,
                                    'scenes': json.dumps(self.scenes)}
            if self.initial_scene is not None:
                song_file['DEFAULT']['initial_scene'] = self.initial_scene
            for clip in self.clips:
                clip_file = {'name': clip.name,
                             'volume': str(clip.volume),
                             'frame_offset': str(clip.frame_offset),
                             'beat_offset': str(clip.beat_offset),
                             'beat_diviser': str(clip.beat_diviser),
                             'output': clip.output,
                             'mute_group': str(clip.mute_group),
                             'one_shot': str(clip.one_shot),
                             'lock_rec': str(clip.lock_rec),
                             'always_play': str(clip.always_play),
                             'audio_file': basename(
                                 clip.audio_file)}
                if clip_file['audio_file'] is None:
                    clip_file['audio_file'] = 'no-sound'
                song_file["%s/%s" % (clip.x, clip.y)] = clip_file

            buffer = StringIO()
            song_file.write(buffer)
            zip.writestr('metadata.ini', buffer.getvalue())

            for member in self.data:
                buffer = BytesIO()
                sf.write(buffer, self.data[member],
                         self.samplerate[member],
                         subtype=sf.default_subtype('WAV'),
                         format='WAV')
                zip.writestr(member, buffer.getvalue())

        self.file_name = file


# this function is NOT in song Class
def load_song_from_file(file):
    with ZipFile(file) as zip:
        with zip.open('metadata.ini') as metadata_res:
            metadata = TextIOWrapper(metadata_res)
            parser = configparser.ConfigParser()
            parser.read_file(metadata)
            
            res = Song(parser['DEFAULT'].getint('width'),
                       parser['DEFAULT'].getint('height'))
            res.file_name = file
            res.volume = parser['DEFAULT'].getfloat('volume', 1.0)
            res.annotation = parser['DEFAULT'].get('annotation', '')
            res.bpm = parser['DEFAULT'].getfloat('bpm', 120.0)
            res.beat_per_bar = parser['DEFAULT'].getint('beat_per_bar', 4)

            scenes = parser['DEFAULT'].get('scenes', '{}')
            jsDecoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
            res.scenes = jsDecoder.decode(scenes)
            res.initial_scene = parser['DEFAULT'].get('initial_scene', None)

            # Loading wavs
            for member in zip.namelist():
                if member == 'metadata.ini':
                    continue
                buffer = BytesIO()
                wav_res = zip.open(member)
                buffer.write(wav_res.read())
                buffer.seek(0)
                data, samplerate = sf.read(buffer, dtype=np.float32, always_2d=True)
                res.data[member] = data
                res.samplerate[member] = samplerate

            # loading clips
            for section in parser:
                if section == 'DEFAULT':
                    continue
                x, y = section.split('/')
                x, y = int(x), int(y)
                
                if parser[section]['audio_file'] == 'no-sound':
                    audio_file = None
                else:
                    audio_file = parser[section]['audio_file']
                clip = Clip(audio_file,
                            parser[section]['name'],
                            parser[section].getfloat('volume', 1.0),
                            parser[section].getint('frame_offset', 0),
                            parser[section].getfloat('beat_offset', 0.0),
                            parser[section].getint('beat_diviser'),
                            parser[section].get('output', common.DEFAULT_PORT),
                            parser[section].getint('mute_group', 0),
                            parser[section].getboolean('one_shot', False),
                            parser[section].getboolean('lock_rec', False),
                            parser[section].getboolean('always_play', False))
                
                # if trying to read a non existing port, assigning Defalt.
                # This will also convert to Default the old Main port:
                if clip.output not in settings.output_ports.keys():
                    clip.output = common.DEFAULT_PORT

                res.addClip(clip, x, y)
            
    return res
