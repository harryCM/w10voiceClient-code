#Prabhu Palanisamy

import os
import threading
import sys
import pyttsx
import client_for_WSserver_live
import socket

import settings
import client_for_WSserver_live

def main():

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

    # open a socket for talking to NLU/ATN and define some global variables
    settings.init()
    
    #os.system("killall -9 pocketsphinx_continuous.exe");
    os.remove("output.txt");
    #s.close()

    # open a socket for talking to NLU/ATN
    nluSocket = settings.nluSocket
    
    # Start a pre-defined use case to give the user a quick impression
    try:
        message='SPEECH Normal: turn on the lights in living room'         
        print("debug: sending (%s) to ATN\n" % message)
        settings.nluSocket.sendall(message)        
        # wait for a response from ATN/NLU
        while True:
            buf = settings.nluSocket.recv(500)
            if buf:
               print("Info: from ATN (%s)\n" % buf)
               break
        if buf.find("CHOSEN_SPEECH") == 0:
           settings.dialogState="GUI:" + buf[14:]
           print("Info: the opening dialog only shows GUI (state=%s)\n" % settings.dialogState)
        # wait for a second response from ATN/NLU           
        while True:
            buf = settings.nluSocket.recv(500)
            if buf:
               print("Info: from ATN (%s)\n" % buf)
               break
        if buf.find("CHOSEN_SPEECH") == 0:
           settings.dialogState="GUI:" + buf[14:]
           print("Info: the opening dialog only shows GUI (state=%s)\n" % settings.dialogState)

        # play a welcome-home prompt
        msg="Welcome home. I have turned on the light in the living room for you."
        sayText(msg)
        
    except KeyboardInterrupt, e:
        sys.exit()
                               
    # open a socket for receiving Sphinx recog results (not working)
    #asrSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #portASR=9000
    #asrSocket.bind(('localhost', portASR))
    #asrSocket.listen(1) # become a server socket, maximum 1 connection
    #print("Info: open a port(%d) for receiving recog result from Sphinx" % portASR)
    #server_address=('localhost',portASR)
    #asrSocket.connect(server_address)
    #buf = connection.recv(1300)
		
    try:
      while(1):
        print "\nWaiting for a trigger phrase \"hello lyrics\" ...\n"
        result = os.system("pocketsphinx_continuous.exe -inmic yes -hmm en-us -jsgf en-us/hello.gram -dict en-us/cmudict-en-us.dict > runPocketSphinx.log")
        #print "Recognized trigger word..."  
        client_for_WSserver_live.main() # Calling cloud speech server for command recognition
        print "\nDialog state code = ", settings.dialogState, " ==\n"
        os.remove("output.txt")

        #message="SPEECH Normal: set the security system to stay in 5 minutes"
        #clientSocket.sendall(message)
        # receive the prompt text from ATN for TTS playback
        #while(1):
        #   nluResult=clientSocket.recv(1000)
        #   if len(nluResult) > 0:
        #        break
        #print("NLU result: %s\n" % nluResult)
         
      trigger_again()

    except KeyboardInterrupt, e:
       sys.exit()
       #trigger_again()
       #except SystemExit:
       #   os._exit(0)

#threading.Thread(target=cread).start()
    
def trigger_again():
    main()
    #return

if __name__ == "__main__":
    main()

