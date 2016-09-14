#Prabhu

import argparse
from ws4py.client.threadedclient import WebSocketClient
import threading
import sys
import urllib
import Queue
import json
import os
import signal
import socket
import pyttsx
import thread
import time
from time import sleep
import logging

import settings

logging.basicConfig()

#atnConnection=0
#logPCM=0
playTTS=0.0

class textTool():

    def __init__(self, text='hello world'):
        self.text=text
        #print ("textTool: sent=%s" % text)

    def wCount(self,text):
        #print ("textTool: sent=%s" % text)
        i=0; slen=len(text); wordCount=0
        while i < slen:
           if text[i] == ' ':
              wordCount = int(wordCount) + 1
           i=i+1
        if wordCount == 0:
           wordCount=1
        return wordCount

class MyClient(WebSocketClient):

    #global atnConnection
    #global logPCM
    global outPCM
    global playTTS

    def __init__(self, url, mic=1, protocols=None, extensions=None, heartbeat_freq=None, byterate=16000,
                 show_hypotheses=True,
                 save_adaptation_state_filename=None, send_adaptation_state_filename=None):

        super(MyClient, self).__init__(url, protocols, extensions, heartbeat_freq)
        self.mic = mic
        self.show_hypotheses = show_hypotheses
        self.byterate = byterate
        self.save_adaptation_state_filename = save_adaptation_state_filename
        self.send_adaptation_state_filename = send_adaptation_state_filename
        self.dialogState = settings.dialogState
        #atnConnection=1
        #logPCM=1
        #print("Info: open a local file to log audio\n")
        #outPCM=open("c:/tmp/test.pcm","wb")

    def send_data(self, data):
        #global logPCM
        #try:
        self.send(data, binary=True)

        # log audio to a local file
        #if logPCM == 1:
        #   outPCM.write(data)
        
        #except (KeyboardInterrupt, SystemExit):
        #print "testing 1 here"

    def opened(self):
        # set up a queue so data can be grabbed from pyaudio and put here 
        # right away without blocking (we must poll pyaudio quickly)
        Q = Queue.Queue()

        def mic_to_ws():

            #global logPCM
            
            import pyaudio
            pa = pyaudio.PyAudio()
            if self.mic == -1:
                #print >> sys.stderr, "Using default mic"
                stream = pa.open(rate = self.byterate, format = pyaudio.paInt16, channels = 1, input = True)
            else:
                print >> sys.stderr, "Using mic #", self.mic
                stream = pa.open(rate = self.byterate, format = pyaudio.paInt16, channels = 1, input = True, input_device_index = self.mic)

            try:
                #print "\n\n"
                print >> sys.stderr, "\nListening... say your request."
                print "\n\n======================================================"
                while True:
                   if playTTS <= 0:
                      time.sleep(playTTS)
                      data = stream.read(2048*2)
                      #self.send_data(data)
                      Q.put(data)
                   #a=raw_input("Does interrupt here?")
                    
            #except KeyboardInterrupt and IOError, :
            except Exception, e:
                #a=raw_input(" Or here?")
                #print e
                #sys.exit()
                print "Error: in sending data to ws peer\n"
                os._exit()
            #self.send_data("")
            #self.send("EOS")
            print("Mic: streaming done\n")
            return
        
        try:
            threading.Thread(target=mic_to_ws).start()
            #signal.pause() 
        except (KeyboardInterrupt, SystemExit):
            print '\n! Received keyboard interrupt, quitting threads.\n'

        
        def send_on():
            try:
               while True:
                  if playTTS <= 0:
                     time.sleep(playTTS)
                     #print >> sys.stderr, "send"
                     q = Q.get()
                     self.send_data(q)
                    
            #except KeyboardInterrupt and IOError, e:
            except Exception, e:
                
                #os._exit(1)
                sys.exit()
                return
        try:
            threading.Thread(target=send_on).start()
        except (KeyboardInterrupt, SystemExit):
            print '\n! Received keyboard interrupt, quitting threads.\n'


    def received_message(self, m):

        global clientSocket
        global port
        global playTTS
        #global atnConnection

        def sayText(message):
            # init tts engine
            print('starting tts ...')
            ttsEngine=pyttsx.init()
            ttsEngine.setProperty('rate',120)
            voices=ttsEngine.getProperty('voices')
            ttsEngine.setProperty('voice',voices[1].id)   # id=1 is for Zira (female)
            #self.ttsEngine=ttsEngine
            ttsEngine.say(message)
            ttsEngine.runAndWait()
            ttsEngine.stop()
            print(' done with tts.\n')

        buf = []
        response = json.loads(str(m))
        #print >> sys.stderr, "RESPONSE:", response
        #print >> sys.stderr, "JSON was:", m
        if response['status'] == 0:
           if 'result' in response:
              trans = response['result']['hypotheses'][0]['transcript']
              if response['result']['final']:
                 try:
                   if self.show_hypotheses and len(trans) > 5:
                      print 'SPEECH: %s\n' % trans    # final result!                       
                      message='SPEECH Normal: ' + trans
                      #a=raw_input("something ")
                      #sayText(trans)
                      # send this recog result to ATN/NLU
                      atnConnection=1                      
                      if atnConnection == 0:
                         port=9034
                         print("Info: open a port(%d) for sending the asr results to ATN\n" % port)
                         clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                         server_address=('localhost',port)
                         clientSocket.connect(server_address)
                      else:
                         print("Info: port to ATN is already open\n")
                           
                      try:
                         print("debug: sending (%s) to NLU/ATN\n" % message)
                         #nluSocket=settings.nluSocket
                         settings.nluSocket.sendall(message) 
                         #clientSocket.sendall(message)

                         # Expect two messages from ATN/NLU (one for GUI and one for TTS)
                         settings.dialogState=0
                         while settings.dialogState < 2:
                            settings.dialogState = int(settings.dialogState) + 1
                            while True:
                               #buf = clientSocket.recv(500)
                                buf = settings.nluSocket.recv(500)
                                if buf:
                                   print("Info: from ATN (%s)\n" % buf)
                                   break

                            if buf.find("CHOSEN_SPEECH") < 0:
                               nlp=textTool(); wordCount = nlp.wCount(buf)
                               promptDur= wordCount / 2.5  # assume 2.5 words/second
                               print("msg(%s) has %d words and need %.1f second to speak\n" % (buf, wordCount, promptDur))
                               playTTS=promptDur
                               sayText(buf)
                               playTTS=0
                               if buf.find("Ok") >= 0 or buf.find("Alright") >= 0:
                                  settings.dialogState=3
                                  # there will be a 3rd message after performing a task
                            else:
                               msg=buf[14:]
                               nlp=textTool(); wordCount = nlp.wCount(msg)
                               print("Info: the msg (%s|%d words) indicates the end of this dialog" %
                                     (msg, wordCount))
                               #if msg.lower() == trans.lower() or  msg.lower() == "never mind":
                               if msg.lower() == "never mind" or wordCount <= 4:
                                  settings.dialogState = int(settings.dialogState) + 1
                                   
                         # end of this dialog for any simple request with all slots filled
                         
                      except KeyboardInterrupt, e:
                               sys.exit()

                      # This is for more complex dialogs
                      if settings.dialogState == 3:
                         msg=buf[14:]
                         # if the message in the NLU response is the same as the text recognized, it is the end of dialog
                         if msg.lower() == trans.lower():
                            settings.dialogState = 0 
                         else:
                           try:
                             print("debug: wait for a follow-up prompt")
                             # wait for a response from ATN/NLU
                             while True:
                                #buf = clientSocket.recv(1000)
                                buf = settings.nluSocket.recv(1000)                                 
                                print("Info: from ATN (%s|len=%d\n" % (buf,len(buf)))
                                if buf.find("CHOSEN_SPEECH") < 0:
                                   nlp=textTool(); wordCount = nlp.wCount(buf)
                                   promptDur= wordCount / 2.5  # assume 2.5 words/second
                                   print("sent(%s) has %d words and need %.1f second to speak\n" % (buf, wordCount, promptDur))
                                   playTTS=promptDur
                                   sayText(buf)
                                   playTTS=0      
                                # Send a control to the mic thread to stop streaming
                                #G.can_run = False         # stop mic recording
                                #G.wcond.notify()
                                #G.can_run = True         # resume mic recording
                                #G.wcond.notify()
                                break
                           except KeyboardInterrupt, e:
                               sys.exit()
             
                 except KeyboardInterrupt, e:
                     sys.exit()
                
                 sys.stdout.flush()
            
              elif self.show_hypotheses:
                   print_trans = trans.replace("\n", "\\n")
                   if len(print_trans) > 80:
                      print_trans = "... %s" % print_trans[-76:]
                   #print >> sys.stderr, 'asr: %s\n\n' % print_trans,
                
           if 'adaptation_state' in response:
              if self.save_adaptation_state_filename:
                 print >> sys.stderr, "Saving adaptation state to %s" % self.save_adaptation_state_filename
                 with open(self.save_adaptation_state_filename, "w") as f:
                     f.write(json.dumps(response['adaptation_state']))
        else:
           print >> sys.stderr, "Received error from server (status %d)" % response['status']
           if 'message' in response:
              print >> sys.stderr, "Error message:",  response['message']


    def closed(self, code, reason=None):
        global outPCM
        #print "Websocket closed() called"
        #print >> sys.stderr
        #if logPCM == 1:
        #   outPCM.close()
        pass


def main():
    content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"
    path = 'client/ws/speech'

    parser = argparse.ArgumentParser(description='Microphone client')
    parser.add_argument('-s', '--server', default="199.63.246.95", dest="server", help="Speech-recognition server")
	#parser.add_argument('-s', '--server', default="199.63.246.95", dest="server", help="Speech-recognition server")
    parser.add_argument('-p', '--port', default="8080", dest="port", help="Server port")
    parser.add_argument('-r', '--rate', default=16000, dest="rate", type=int, help="Rate in bytes/sec at which audio should be sent to the server.")
    parser.add_argument('-d', '--device', default="-1", dest="device", type=int, help="Select a different microphone (give device ID)")
    parser.add_argument('--save-adaptation-state', help="Save adaptation state to file")
    parser.add_argument('--send-adaptation-state', help="Send adaptation state from file")
    parser.add_argument('--content-type', default=content_type, help="Use the specified content type (default is " + content_type + ")")
    parser.add_argument('--hypotheses', default=True, type=int, help="Show partial recognition hypotheses (default: 1)")
    args = parser.parse_args()

    content_type = args.content_type
    #print >> sys.stderr, "Content-Type:", content_type

    uri = "ws://%s:%s/%s?%s" % (args.server, args.port, path, urllib.urlencode([("content-type", content_type)]))
    #print >> sys.stderr, "Connecting to", uri

    ws = MyClient(uri, byterate=args.rate, mic=args.device, show_hypotheses=args.hypotheses,
                  save_adaptation_state_filename=args.save_adaptation_state, send_adaptation_state_filename=args.send_adaptation_state)
    ws.connect()
    #result = ws.get_full_hyp()
    #print result.encode('utf-8')
    
    ws.run_forever()

if __name__ == "__main__":
    main()

