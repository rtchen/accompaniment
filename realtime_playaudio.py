import pretty_midi  
import time
import threading, time
import matplotlib.pyplot as plt
from mingus.midi import fluidsynth   
from mingus.containers import Note
import sys

ACC_FILE = 'heyjude.mid'
BPM = 60
BPS = BPM/float(60) #beat per second
original_begin = time.clock()


#fluidsynth.init("soundfont.sf2")
# fluidsynth need some time to load sound file otherwise there is a 
# chance there is no sound
#tmp  = raw_input('press return key to begin this program')

pressed_key = "lol"
timeQueue = []
stop_thread = False
sQueue = []

'''
function: press_key_thread:
--------------------------------------------------------
init another thread, take in keyboard input
each tap on return/enter key is registered as a beat
and save to global queue timeQueue
'''
def press_key_thread():
    global pressed_key
    global stop_thread
    while not stop_thread:
        pressed_key = sys.stdin.readline()
        if pressed_key=='\n':
            timeQueue.append(time.clock()-original_begin)
            if len(timeQueue) == 3:
                b0 = 1
                t0 = timeQueue[-2]
                s0 = float(1)/(timeQueue[-1]-timeQueue[-2])
                sQueue.append(s0)
            if len(timeQueue)%2==0 and len(timeQueue)>3:
               b0,t0,s0=compute_tempo_ratio(b0,t0,s0)
            pressed_key = 'lol'



'''
function: compute_tempo_ratio:
----------------------------------------------------
scheduleing algo by NIME 2011 paper
'''
def compute_tempo_ratio(b0,t0,s0):
    l  =  0.1
    t1 = timeQueue[-1]
    b = b0+(t1+l-t0)*s0
    tn  = t1+l
    bn = b
    te = timeQueue[-2]
    se = float(1)/(timeQueue[-1]-timeQueue[-2])
    be = b0+1
    sn  =  (float(4)/(te*se-tn*se-be+bn+4))*se
    print 'sn %f'%sn
    sQueue.append(sn)
    return bn,tn,sn


class Player:
    def __init__(self, ACC_FILE, original_begin,BPM):
        self.ACC_FILE = ACC_FILE
        self.original_begin = original_begin
        self.midi_data = pretty_midi.PrettyMIDI(ACC_FILE)
        self.notes = sorted(self.midi_data.instruments[0].notes, key=lambda x: x.start, reverse=False)
        self.playTimes = []
        self.noteTimes = []
        self.midi_start_time = self.notes[0].start
        self.BPS = BPM/float(60)

    '''
    function: follow:
    -----------------------------------------------
    follow score from start point
    '''
    def follow(self,start):
        global sQueue
        global timeQueue
        begin = time.clock()

        for i in range(start,len(self.notes)):
            note = self.notes[i]       
            cur_time = time.clock()-begin
            wait_delta = note.start-cur_time


            tempo_ratio = float(self.BPS)/sQueue[-1]
            if  tempo_ratio < 1:
                begin -= wait_delta*(1-tempo_ratio)
                wait_delta = wait_delta* tempo_ratio
            elif tempo_ratio > 1:
                begin += wait_delta*(tempo_ratio-1)
                wait_delta = wait_delta *tempo_ratio


            target_start_time = time.clock() + wait_delta
            while time.clock() < target_start_time:
                 pass


            delta_time = note.end - (time.clock()-begin)
            #print 'delta_time%f'%(delta_time-note.end+note.start)
           
            self.playTimes.append(time.clock()-original_begin)
            self.noteTimes.append(note.start)

            
            
            tempo_ratio = float(self.BPS)/sQueue[-1]
            if  tempo_ratio < 1:
                print 'tempo faster with ratio %f'%tempo_ratio
                begin -= delta_time*(1-tempo_ratio)
                delta_time = delta_time * tempo_ratio
            elif tempo_ratio > 1:
                print 'tempo slower with ratio %f'%tempo_ratio
                begin += delta_time*(tempo_ratio-1)
                delta_time = delta_time *tempo_ratio


            n = Note(note.pitch-12)
            fluidsynth.play_Note(n)

            target_time = time.clock() + delta_time
            while time.clock() < target_time:
                 pass
            fluidsynth.stop_Note(n)



        tap_time = [t - self.original_begin for t in timeQueue]
        tap_beat= [t /float(self.BPS) for t in range(len(tap_time))]


        plt.scatter(x=self.playTimes,y=self.noteTimes,c = 'b',s = 10,marker = 'o')
        plt.plot(tap_time, tap_beat, marker= '+')
        plt.xlabel('audio time (seconds)')
        plt.ylabel('score time (seconds)')
        plt.show()
    
    '''
    function:jump
    ---------------------------------------
    jump to specified ith note
    '''
    def jump(self,i):
        self.follow(i)




if __name__ == '__main__':
    pk_thread = threading.Thread(target = press_key_thread)
    pk_thread.start()
    try:
        fluidsynth.init("soundfont.sf2")
        print 'tap three times to start'
        while True:
            if len(timeQueue)>=3:
                break
        player = Player(ACC_FILE, original_begin,BPM)
        player.follow(0)
    except KeyboardInterrupt:
        stop_thread = True
        pk_thread.killed = True
        pk_thread.join()
    finally:
        stop_thread = True
        pk_thread.killed = True
        pk_thread.join()



