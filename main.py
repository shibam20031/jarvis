import os
import eel

from engine.feature import *
from engine.command import *
from engine.auth import recoganize
def start():
    
    eel.init("www")
    @eel.expose
    def init():
        subprocess.call([r'device.bat'])
        eel.hideLoader()
        speak("Ready for Face Authentication")
        flag = recoganize.AuthenticateFace()()
        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            eel.hideFaceAuthSuccess()
            speak("Hello, Welcome Sir, How can i Help You")
            eel.hideStart()
        else:
            speak("Face Authentication Fail")
    os.system('start msedge.exe --app="http://127.0.0.1:5500/www/index.html"')

    eel.start('index.html', mode=None, host='localhost', block=True)