import tkinter as tk
import cv2
from PIL import ImageTk, Image
import json
import google.generativeai as genai
import face_recognition
import numpy as np
from config import GEMINI_API
import speech_recognition as sr
import threading

IMAGE_PATH = './assets/face_cam.png'
USER_INPUT = None
AI_RESPONSE = None
cam_on = False
cap = None
count = 1
current_y = 170  # Starting y-coordinate for the first text message
unknown_face_dict = {}
conversation = []
recognizer = sr.Recognizer()


with open("./known_face_encoding.json") as file:
    known_faces_encodings = json.load(file)
    if known_faces_encodings is None:
        known_faces_encodings = {}

      
def ai_model(prompt):
    global GEMINI_API
    genai.configure(api_key=GEMINI_API)
    
    generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 0,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction=f"you are david, a virtual assistant, built by 'Darshan Choudhary'. you are provided with conversation history {conversation} and your work is to go through the history and analyze it. if your input prompt is available in history then answer the input from conversation history and if the question is new to you then answer how you normally answer. answers should be to the point and short. act friendly with user, give polite replies and act similar to humans",
    )
    
    
    chat_session = model.start_chat()

    response = chat_session.send_message(prompt)
    
    return response.text
    
def new_face_show():
    global text_container, current_y, unknown_face_dict

    canvas = tk.Canvas(text_container,height=250,bg="pink",width=300)
    text_container.create_window((150,current_y+130),window=canvas,width=300)
    
    h_scrollbar = tk.Scrollbar(canvas, orient='horizontal', command=canvas.xview)
    h_scrollbar.place(x=0,y=233, width=300)
    
    canvas.config(xscrollcommand=h_scrollbar.set)
    
    canvas.image_list = []
    x = 0
    print(len(unknown_face_dict.items()))
    for name,image in unknown_face_dict.items():
        rgb_image_array = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        org_img = Image.fromarray(rgb_image_array).resize((200,200))
        img = ImageTk.PhotoImage(image=org_img)
        canvas.imgtk = img
        canvas.create_image(x,5, image = img, anchor="nw") #adding image
        canvas.image_list.append(img) #appending to image_list so that it is not discarded
        
        canvas.create_rectangle(x+5,210,x+70,230, fill="blue", outline="black") #adding save button

        x +=205
    
    canvas.config(scrollregion=canvas.bbox("all"))
    canvas.update_idletasks() 
    current_y +=270
        
def voice_command():
    global recognizer
    with sr.Microphone() as source:
        audio_data = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio_data)
        if text:
            text_adder(text,role="User")
            ai_response = ai_model(text)
            text_adder(ai_response,role="David")
            conversation.append({"user": text, "david": ai_response})
            
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
        
    except sr.RequestError as e:
        print("Error: Could not request results from Google Speech Recognition service")
        
def voice_command_thread():
    threading.Thread(target=voice_command).start()        

def text_adder(text=True, role=None):
    global current_y
    if role:
        text = text_container.create_text((10, current_y),width=300, text=f"{role} : {text}", fill="white", font=("Merriweather", 10, "bold"), anchor="nw")
    else:
        text = text_container.create_text((10, current_y),width=300, text=f"{text}", fill="white", font=("Merriweather", 10, "bold"), anchor="nw")
    text_container.config(scrollregion=text_container.bbox("all"))  # Update scroll region
    
    #finding height
    bounds = text_container.bbox(text)
    text_height = bounds[3] - bounds[1]
    current_y += text_height+10  


def submit():
    text_var = text_input.get()
    text_adder(text_var,role="User")
    ai_response = ai_model(text_var)
    text_adder(ai_response,role="David")

def submit_thread():
    threading.Thread(target=submit).start()

def start_face_recognition():
    global count, cap, cam_on
    if cam_on:
        ret, frame = cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_location, face_encoding in zip(face_locations,face_encodings):
                y1, x2, y2, x1 = face_location
                
                matches = face_recognition.compare_faces(list(known_faces_encodings.values()), face_encoding)
                face_distance = face_recognition.face_distance(list(known_faces_encodings.values()), face_encoding)
                
                best_match = np.argmin(face_distance)
                    
                if(matches[best_match]):
                    try:
                        org_name = list(known_faces_encodings.keys())[best_match]
                        name = org_name.split(".")[0]
                    except:
                        name = "unknown"
                else:
                    name = "unknown"
                
                if name=="unknown":
                    face_img = frame[y1:y2, x1:x2]
                    face_name = f"unknown{count}"
                    unknown_face_dict[face_name] = face_img
                    count += 1
                        
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 3)
                cv2.putText(frame, name, (x1 + 10, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

                    
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image).resize((822, 652))
            imgtk = ImageTk.PhotoImage(image=img)
            canvas_face_cam.imgtk = imgtk
            canvas_face_cam.create_image((302, 150), image=imgtk)
        
        canvas_face_cam.after(5, start_face_recognition)


def show_frame():
    if cam_on:
        ret, frame = cap.read()
        if ret:
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image).resize((822, 652))
            imgtk = ImageTk.PhotoImage(image=img)
            canvas_face_cam.imgtk = imgtk
            canvas_face_cam.create_image((302, 150), image=imgtk)
        canvas_face_cam.after(10, show_frame)

def start_vid():
    global cam_on, cap
    if cam_on:
        stop_vid()
    cam_on = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture")
        return
    show_frame()


def start_vid_thread():
    threading.Thread(target=start_vid).start()

def stop_vid():
    global cam_on
    cam_on = False
    if cap and cap.isOpened():
        cap.release()
    # Display the custom image if available
    if camera_screen:
        canvas_face_cam.imgtk = camera_screen
        canvas_face_cam.create_image((302, 190), image=camera_screen)
    else:
        print("Custom image not found")

    
def enable_face_recognition():
    global cam_on, cap, count
    
    if cam_on:
        cap.release()
    cam_on = True

    cap = cv2.VideoCapture(0)
    start_face_recognition()
        
        
def face_recog_thread():
    threading.Thread(target=enable_face_recognition).start()    


# Create the main window
root = tk.Tk()
root.title("Main Window")
root.geometry("1000x600")
root.config(background="#576CA8")
root.resizable(False,False)
root.grid_columnconfigure(0, minsize=600)
root.grid_columnconfigure(1, minsize=367)
root.grid_rowconfigure(0)
root.grid_rowconfigure(1, weight=1)

camera_screen = tk.PhotoImage(file=IMAGE_PATH).subsample(1)
rounded_frame2_bg = tk.PhotoImage(file="./assets/frame2bg.png")

header = tk.Label(root, text="Face-Recognition System", bg="#576CA8", fg="white", font=("Helvetica", 16, "bold"))
header.grid(row=0, columnspan=2, pady=10)

# Create and place the frames
frame1 = tk.Frame(root, bg='#576CA8', width=600, height=500)
frame2 = tk.Canvas(root, bg='#576CA8', width=367, height=500, borderwidth=0, highlightthickness=0)

# Add background image to the canvas
frame2.create_image((185, 250), image=rounded_frame2_bg)

# Create a text container canvas inside frame2
text_container = tk.Canvas(frame2, bg='#274690', width=300, height=420, borderwidth=0, highlightthickness=0)
text_container.place(x=20, y=20)

# Add a scrollbar to the text container
scrollbar = tk.Scrollbar(frame2, orient=tk.VERTICAL, command=text_container.yview)
scrollbar.place(x=335, y=20, height=420)
text_container.config(yscrollcommand=scrollbar.set)

#adding text input feature
text_input = tk.Entry(frame2,width=45)
text_input.place(x=20, y=450)

#adding voice command button 
voice_img = Image.open("./assets/microphone.png").resize((20,20))
resized_microphone_img = ImageTk.PhotoImage(image=voice_img)

button = tk.Button(frame2,command=voice_command_thread,image=resized_microphone_img,background="#274690",borderwidth=0)
button.place(x=305, y=448)

#adding send button
button_img = Image.open("./assets/send.png").resize((20,20))
resized_button_img = ImageTk.PhotoImage(image=button_img)

button = tk.Button(frame2,command=submit_thread,image=resized_button_img,background="#274690",borderwidth=0)
button.place(x=332, y=448)

# Add some initial conversation text
text_container.create_text((10,10),width=300,text="Welcome to DAVID, your personal assistant with a touch of innovation. Powered by face recognition technology, DAVID not only recognizes you but also assists you seamlessly. I can assist you with everything, making your experience intuitive and enjoyable. Let's get started and make your tasks easier together!\n__________________________________________", fill="white", font=("Merriweather", 10, "bold"), anchor="nw")

canvas_face_cam = tk.Canvas(frame1, width=600, height=380, borderwidth=0, highlightthickness=0)
canvas_face_cam.create_image((300, 190), image=camera_screen)

canvas_face_cam.pack(anchor="center", pady=50, fill=tk.BOTH)

# Buttons
TurnCameraOn = tk.Button(frame1, text="Start Video", command=start_vid_thread, anchor="center")
TurnCameraOn.place(anchor="center", x=200, y=460)
TurnCameraOff = tk.Button(frame1, text="Stop Video", command=stop_vid, anchor="center")
TurnCameraOff.place(anchor="center", x=310, y=460)
enableFaceRecognition = tk.Button(frame1,text="Enable Face Recognition",command=face_recog_thread,anchor="center")
enableFaceRecognition.place(anchor="center", x=450, y=460)
newFace = tk.Button(frame1,text="Show new face",command=new_face_show,anchor="center")
newFace.place(anchor="center", x=450, y=490)

frame1.grid(row=1, column=0, sticky="nsew", padx=(8, 8))
frame2.grid(row=1, column=1, sticky="nsew", padx=(8, 8))

# Run the main loop
root.mainloop()

# works after everything
def load_new_face_encoding():
    global new_faces_list, json_file, known_faces_dict
    for image in new_faces_list:
        name = image
        img = cv2.imread(f"./known_faces/{image}")
        rgb_img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        # img = face_recognition.load_image_file(f"./known_faces/{image}")
        face_location = face_recognition.face_locations(rgb_img)
        # print(face_location)
        img_encoding = numpy.array(face_recognition.face_encodings(rgb_img,face_location)[0])
        known_faces_dict[name] = img_encoding.tolist()
        
def load_known_face_encoding_dict():
    for image in (os.listdir("./known_faces/")):
        name = image
        img = cv2.imread(f"./known_faces/{image}")
        rgb_img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        # img = face_recognition.load_image_file(f"./known_faces/{image}")
        face_location = face_recognition.face_locations(rgb_img)
        img_encoding = numpy.array(face_recognition.face_encodings(rgb_img,face_location)[0])
        known_faces_dict[name] = img_encoding.tolist()
    # return known_faces_dict

def known_faces_json_creater():       
    global json_file, known_faces_dict
    json_file.seek(0)
    json.dump(known_faces_dict,json_file)
        
load_known_face_encoding_dict()
       
json_file = open("./known_face_encoding.json","r+")
json_data = json.load(json_file)

# json_dict = json.loads(json_data)
old_known_names_list = list(json_data.keys())
old_known_names_list = map(lambda img: img+".png", old_known_names_list )


known_faces_data = os.listdir("./known_faces/")
# new_known_names_list = list(map(lambda i: i.split(".")[0], known_faces_data))

diff = list(set(known_faces_data)-set(old_known_names_list))
new_faces_list = []
for new_face in diff:
    for face in known_faces_data:
        if new_face not in face:
            new_faces_list.append(face)


load_new_face_encoding() 
known_faces_json_creater() 
