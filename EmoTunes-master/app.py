from flask import Flask, render_template

 
import spotipy.util as util
import threading
import os
import tempfile

from moodtape_functions import authenticate_spotify, aggregate_top_artists, aggregate_top_tracks, select_tracks, create_playlist
from deepface import DeepFace


import cv2



client_id = "63861abc02b34ce8b324f62f4659ee05"
client_secret = "5317e38281be495ebcc150df7eeded7f"
redirect_uri = "https://localhost:3000"



scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

username = "mohithms"
token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)



app = Flask(__name__)



global emotion, capturing,mood1
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)
capturing = True



def process_video():
    global emotion,capturing,mood1
    count=0

    while True:
        ret,frame = cap.read()
		
        temp_path = os.path.join(tempfile.gettempdir(), 'temp_frame.jpg')
        cv2.imwrite(temp_path, frame)
		
        result = DeepFace.analyze(img_path=temp_path, actions=['emotion'], enforce_detection=False)

        if isinstance(result, list) and len(result) > 0:
            emotion = result[0]["dominant_emotion"]
        else:
            emotion = "Unknown"

        gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray,1.1,4)

        count+=1

        for (x,y,w,h) in faces:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),3)

        txt = str(emotion)

        cv2.putText(frame,txt,(50,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)
        cv2.imshow('frame',frame)

        if cv2.waitKey(1) & 0xff == ord('q'):
            capturing=False
            break

        if count>=20:
             break
		
    cap.release()
    cv2.destroyAllWindows()




@app.route('/start_camera', methods=['POST'])
def start_camera():
    global capturing
    with app.app_context():
        capturing = True
        video_thread = threading.Thread(target=process_video)
        video_thread.start()
    return "Camera started"



@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global capturing
    with app.app_context():
        capturing = False
        video_end = threading.Thread(target=moodtape)
        video_end.start()
    return "Camera Stopped"
	


@app.route("/", methods=['POST'])
def moodtape():
    with app.app_context():
        global emotion, capturing, mood1,emoji
        if emotion=='sad':
              mood1=0.07
              emoji="\U0001f614"
        elif emotion=='fear':
             mood1=0.22
             emoji="\U0001f628"
        elif emotion=='angry':
               mood1=0.45
               emoji="\U0001f621"
        elif emotion=='neutral':
               mood1=0.63
               emoji="\U0001f610"
        elif emotion=='surprise':
               mood1=0.80
               emoji="\U0001f632"
        elif emotion=='happy':
               mood1=0.98
               emoji="\U0001f601"
        spotify_auth = authenticate_spotify(token)
        top_artists = aggregate_top_artists(spotify_auth)
        top_tracks = aggregate_top_tracks(spotify_auth, top_artists)
        selected_tracks = select_tracks(spotify_auth, top_tracks, mood1)
        playlist = create_playlist(spotify_auth, selected_tracks, mood1)
    print("Created playlist!")
    print("Check your Spotify!")


@app.route('/')
def my_form():
    return render_template('input.html')

if __name__ == "__main__":
	app.run(host='0.0.0.0')