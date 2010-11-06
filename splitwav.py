
import os
import sys
import getopt
import struct
import cProfile
import wave
import csv

songsinfo = None
threshold = 1.0

option_list, args = getopt.getopt( sys.argv[1:], "", [ "songsinfo=", "threshold=" ] )
for option in option_list:
    if option[0]=="--songsinfo":
        songsinfo = csv.reader(file(option[1],"rb"))
    elif option[0]=="--threshold":
        threshold = float(option[1])

src_filename = args[0]

songinfo_list = []

def parseMinSecond(s):
    minute, second = s.split(":")
    return int(minute) * 60 + int(second)

for info in songsinfo:
    #print info
    songinfo_list.append( ( unicode( info[0], "utf8" ).strip(), parseMinSecond(info[1]) ) )

src_wave = wave.open( src_filename, "rb" )
nframes = src_wave.getnframes()
framerate = src_wave.getframerate()

def openNextDestination():
    global dst_wave
    global dst_wave_list
    
    dst_wave = wave.open( u"%02d %s.wav" % ( len(dst_wave_list)+1, songinfo_list[len(dst_wave_list)][0] ), "wb" )
    dst_wave.setnchannels(2)
    dst_wave.setsampwidth(2)
    dst_wave.setframerate(framerate)
    
    dst_wave_list.append(dst_wave)

dst_wave = None
dst_wave_list = []
openNextDestination()

def minSecondString( sec ):
    minute = sec / 60
    second = sec % 60
    return "%02d:%02d" % (minute, second)

def main():

    pos = 0
    last_sound_pos = 0
    last_silent_pos = 0
    last_split_pos = 0
    
    dst_frames = ""

    while True:

        frames = src_wave.readframes( framerate * 60 )
    
        if not frames : break
    
        for i in xrange( len(frames)/4 ):
    
            frame = frames[ i*4 : i*4+4 ]
        
            left, right = struct.unpack("HH",frame)
    
            if left>60000 and right>60000:
                last_silent_pos = pos
            else:
                if (pos-last_sound_pos) > (framerate * threshold) and last_sound_pos>0:

                    split_pos = (pos+last_sound_pos)/2
                    
                    second = (split_pos - last_split_pos) / framerate
                    print minSecondString( second )

                    acceptable_time_difference = 5
                    if len(dst_wave_list)==1 or len(dst_wave_list)==len(songinfo_list):
                        acceptable_time_difference = 20

                    if abs( songinfo_list[len(dst_wave_list)-1][1] - second ) > acceptable_time_difference:
                        print "WARNING : time is differ from csv file.", songinfo_list[len(dst_wave_list)-1][1], second, acceptable_time_difference, len(dst_wave_list)-1
                        #sys.exit(1)
                    
                    bak = src_wave.tell()
                    src_wave.setpos( last_split_pos )
                    buf = src_wave.readframes( split_pos - last_split_pos )
                    dst_wave.writeframesraw(buf)
                    dst_wave.close()
                    src_wave.setpos(bak)
                    
                    openNextDestination()
                    
                    last_split_pos = split_pos

                last_sound_pos = pos
        
            pos += 1

    src_wave.setpos( last_split_pos )
    buf = src_wave.readframes( pos - last_split_pos )
    dst_wave.writeframesraw(buf)
    dst_wave.close()


#cProfile.runctx( "main()", globals(), locals() )

main()
