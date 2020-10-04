from collections import deque
from imutils.video import VideoStream
from google.cloud import storage
import numpy as np
import cv2
import imutils
import time
import pyrebase
import os
import math
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="stryker-c841b-75f1a5f1a2f2.json"

# CONSTANTS
DEQUE_SIZE = 64
redLower = (0, 100, 108)
redUpper = (10, 200, 255)

# WHITE GOAL LINE
WHITE_GOAL_START = (880, 50)
WHITE_GOAL_END = (880, 520)
RIGHT_BOUNDARY_LOW = (917, 0)
RIGHT_BOUNDARY_HIGH = (917, 720)

# BLACK GOAL LINE
BLACK_GOAL_START = (57, 50)
BLACK_GOAL_END = (57, 520)
LEFT_BOUNDARY_LOW = (17, 0)
LEFT_BOUNDARY_HIGH = (17, 720)

GOAL_POST_HIGH = 345
GOAL_POST_LOW = 217

# POSSESSION LINES
LINE11 = (160, 50)
LINE12 = (263, 50)
LINE13 = (366, 50)
LINE14 = (469, 50)
LINE15 = (571, 50)
LINE16 = (674, 50)
LINE17 = (777, 50)

LINE21 = (160, 520)
LINE22 = (263, 520)
LINE23 = (366, 520)
LINE24 = (469, 520)
LINE25 = (571, 520)
LINE26 = (674, 520)
LINE27 = (777, 520)

def ms():
    return int(round(time.time() * 1000))

def msToSeconds(ms):
    return float(ms/1000)

def firebase():
    firebaseConfig = {
        "apiKey": "AIzaSyBSwh190vKk4hnE8Tfcewi-HpNeRLFv5XI",
        "authDomain": "stryker-c841b.firebaseapp.com",
        "databaseURL": "https://stryker-c841b.firebaseio.com",
        "projectId": "stryker-c841b",
        "storageBucket": "stryker-c841b.appspot.com",
        "messagingSenderId": "976906995305",
        "appId": "1:976906995305:web:99ec232f50695f8d0dc4f8",
        "measurementId": "G-TSX24R7V0P"
    }
    firebase = pyrebase.initialize_app(firebaseConfig)
    return {
        "store": firebase.storage(),
        "db": firebase.database()
    }

class Game:
    def __init__(self):
        self.DURATION = 0
        self.BLACK_SCORE = 0
        self.WHITE_SCORE = 0
        self.BLACK_POSSESSION = 0
        self.BLACK_POSSESSION_B = True
        self.JUST_SCORED = False
        self.WHITE_POSSESSION = 0
        self.WHITE_POSSESSION_B = True
        self.WHITE_TIME_START = ms()
        self.BLACK_TIME_START = ms()
        self.pts = deque(maxlen=DEQUE_SIZE)
        self.frames = deque(maxlen = 60)
        self.BLACK_GOAL_SPEEDS = []
        self.WHITE_GOAL_SPEEDS = []
        self.fb = firebase()
        self.GOALS = []

    def blackListener(self, event):
        self.BLACK_SCORE = event["data"]

    def whiteListener(self, event):
        self.WHITE_SCORE = event["data"]
    
    def resetListener(self, event):
        if (event and event["data"]):
            print(event)
            print(event["data"])
            self.clearGame()
        
    def clearGame(self):
        self.DURATION = 0
        self.BLACK_SCORE = 0
        self.WHITE_SCORE = 0
        self.BLACK_POSSESSION = 0
        self.BLACK_POSSESSION_B = True
        self.JUST_SCORED = False
        self.WHITE_POSSESSION = 0
        self.WHITE_POSSESSION_B = True
        self.WHITE_TIME_START = ms()
        self.BLACK_TIME_START = ms()
        self.pts = deque(maxlen=DEQUE_SIZE)
        self.frames = deque(maxlen = 60)
        self.BLACK_GOAL_SPEEDS = []
        self.WHITE_GOAL_SPEEDS = []
        self.fb = firebase()
        self.GOALS = []

        self.fb["db"].update({
            "BLACK_GOALS": 0,
            "WHITE_GOALS": 0,
            "WHITE_POSSESSION": 0.00,
            "BLACK_POSSESSION": 0.00,
            "DURATION": 0.00,
            "BLACK_GOAL_SPEEDS": [],
            "WHITE_GOAL_SPEEDS": [],
            "GOALS":[],
            "RESET": False
        })
        client = storage.Client()
        bucket = client.get_bucket('stryker-c841b.appspot.com')
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()

        print("Hello!!")

    
    def clearDeque(self):
        self.pts = deque(maxlen=DEQUE_SIZE)

    def createMask(self, frame):
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, redLower, redUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        return mask

    def annotateFrame(self, frame):
        cv2.line(frame, WHITE_GOAL_START, WHITE_GOAL_END, (255, 255, 0), 2)
        cv2.line(frame, RIGHT_BOUNDARY_LOW, RIGHT_BOUNDARY_HIGH, (255, 255, 0), 2)
        cv2.line(frame, BLACK_GOAL_START, BLACK_GOAL_END, (0, 255, 255), 2)
        cv2.line(frame, LEFT_BOUNDARY_LOW, LEFT_BOUNDARY_HIGH, (255, 255, 0), 2)
        cv2.line(frame, LINE11, LINE21, (255, 0, 0), 2)
        cv2.line(frame, LINE12, LINE22, (255, 0, 0), 2)
        cv2.line(frame, LINE13, LINE23, (255, 0, 0), 2)
        cv2.line(frame, LINE14, LINE24, (255, 0, 0), 2)
        cv2.line(frame, LINE15, LINE25, (255, 0, 0), 2)
        cv2.line(frame, LINE16, LINE26, (255, 0, 0), 2)
        cv2.line(frame, LINE17, LINE27, (255, 0, 0), 2)
        return frame

    def updateScore(self, scorer):
        if scorer.lower() == "black":
            self.BLACK_SCORE += 1
            self.fb["db"].update({"BLACK_GOALS": self.BLACK_SCORE})  
        elif scorer.lower() == "white":
            self.WHITE_SCORE += 1
            self.fb["db"].update({"WHITE_GOALS": self.WHITE_SCORE})
        self.JUST_SCORED = True
        self.goalSpeed(scorer)
        speed = self.BLACK_GOAL_SPEEDS[-1] if scorer.lower() == "black" else self.WHITE_GOAL_SPEEDS[-1]
        self.GOALS.append({
                "blackScore": self.BLACK_SCORE,
                "whiteScore": self.WHITE_SCORE,
                "scorer": "Black" if scorer.lower() == "black" else "White",
                "goalSpeed": speed
            })
        self.fb["db"].update({"GOALS": self.GOALS})
        self.clearDeque()
        self.fb["db"].update({"DURATION": msToSeconds(self.DURATION)})
        print(f"{scorer} SCORED".upper())
        print("BLACK SCORE: {}".format(self.BLACK_SCORE))
        print("WHITE SCORE: {}".format(self.WHITE_SCORE))


    def evaluateScore(self, x, y):
        i = 0
        if (len(self.pts) and 917 > x >= 880 and GOAL_POST_LOW < y < GOAL_POST_HIGH):
            self.updateScore("BLACK")
            videoName = 'BLACK_GOAL_' + str(self.BLACK_SCORE) + '.mp4'
            video = cv2.VideoWriter(videoName, cv2.VideoWriter_fourcc(*'mp4v'), 20, (1280,720))
            while (len(self.frames)):
                video.write(self.frames.pop())
                i+=1
            video.release()
            fileName = 'BLACK_GOAL_' + str(self.BLACK_SCORE) + '.mp4'
            client = storage.Client()
            bucket = client.get_bucket('stryker-c841b.appspot.com')
            blob = bucket.blob("/")
            videoPath = fileName
            blob = bucket.blob(fileName)
            blob.upload_from_filename(videoPath)
            #os.remove(fileName)

        elif(len(self.pts) and 17 < x <= 52 and GOAL_POST_LOW < y < GOAL_POST_HIGH):
            self.updateScore("WHITE")
            videoName = 'WHITE_GOAL_' + str(self.WHITE_SCORE) + '.mp4'
            video = cv2.VideoWriter(videoName, cv2.VideoWriter_fourcc(*'mp4v'), 20, (1280,720))
            while (len(self.frames)):
                video.write(self.frames.pop())
                i+=1
            video.release()
            fileName = 'WHITE_GOAL_' + str(self.WHITE_SCORE) + '.mp4'
            client = storage.Client()
            bucket = client.get_bucket('stryker-c841b.appspot.com')
            blob = bucket.blob("/")
            videoPath = fileName
            blob = bucket.blob(fileName)
            blob.upload_from_filename(videoPath)
            os.remove(fileName)

    def evaluatePossession(self, x, y):
        if (len(self.pts) == 1):
            self.BLACK_TIME_START = ms()
            self.WHITE_TIME_START = ms()
        if (not len(self.pts) and self.JUST_SCORED):
            if (self.BLACK_POSSESSION_B):
                self.WHITE_POSSESSION = self.WHITE_POSSESSION + ms() - self.WHITE_TIME_START
                self.fb["db"].update({"WHITE_POSSESSION": msToSeconds(self.WHITE_POSSESSION)})
            else:
                self.BLACK_POSSESSION = self.BLACK_POSSESSION + ms() - self.BLACK_TIME_START
                self.fb["db"].update({"BLACK_POSSESSION": msToSeconds(self.BLACK_POSSESSION)})
            self.JUST_SCORED = False
            self.BLACK_POSSESSION_B = True
            self.WHITE_POSSESSION_B = True

        elif (((BLACK_GOAL_START[0] < x < LINE12[0]) or (LINE13[0] < x < LINE14[0]) or (LINE15[0] < x < LINE16[0])) and self.BLACK_POSSESSION_B):
            self.WHITE_POSSESSION = self.WHITE_POSSESSION + ms() - self.WHITE_TIME_START
            self.fb["db"].update({"WHITE_POSSESSION": msToSeconds(self.WHITE_POSSESSION)})
            self.BLACK_TIME_START = ms()
            self.BLACK_POSSESSION_B = False
            self.WHITE_POSSESSION_B = True
        elif (((LINE12[0] < x < LINE13[0]) or (LINE14[0] < x < LINE15[0]) or (LINE16[0] < x < WHITE_GOAL_START[0])) and self.WHITE_POSSESSION_B):
            self.BLACK_POSSESSION = self.BLACK_POSSESSION + ms() - self.BLACK_TIME_START
            self.fb["db"].update({"BLACK_POSSESSION": msToSeconds(self.BLACK_POSSESSION)})
            self.WHITE_TIME_START = ms()
            self.BLACK_POSSESSION_B = True
            self.WHITE_POSSESSION_B = False

        self.DURATION = self.BLACK_POSSESSION + self.WHITE_POSSESSION
        self.fb["db"].update({"DURATION": msToSeconds(self.DURATION)})


    def renderContrail(self, frame):
        for i in range(1, len(self.pts)):
            # if either of the tracked points are None, ignore them
            if self.pts[i - 1] is None or self.pts[i] is None:
                continue
            # otherwise, compute the thickness of the line and draw the connecting lines
            thickness = int(np.sqrt(DEQUE_SIZE / float(i + 1)) * 2.5)
            cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 255, 0), thickness)
        return frame

    def goalSpeed(self, scorer):
        xDist1 = ((float) (self.pts[0][0] - self.pts[5][0])) * ((float) (3.83333/823))
        yDist1 = ((float) (self.pts[0][1] - self.pts[5][1])) * ((float) (3.83333/823))
        xDist2 = ((float) (self.pts[5][0] - self.pts[10][0])) * ((float) (3.83333/823))
        yDist2 = ((float) (self.pts[5][1] - self.pts[10][1])) * ((float) (3.83333/823))
        xDist3 = ((float) (self.pts[10][0] - self.pts[15][0])) * ((float) (3.83333/823)) 
        yDist3 = ((float) (self.pts[10][1] - self.pts[15][1])) * ((float) (3.83333/823))
        velocity1 = ((xDist1 / ((float) (1/5))), (yDist1 / ((float) (1/5))))
        velocity2 = ((xDist2 / ((float) (1/5))), (yDist2 / ((float) (1/5))))
        velocity3 = ((xDist3 / ((float) (1/5))), (yDist3 / ((float) (1/5))))
        speed = (.8 * (math.sqrt((velocity1[0] ** 2) + (velocity1[1] ** 2))) + 1 * (math.sqrt((velocity2[0] ** 2) + (velocity2[1] ** 2))) + 1.2 * (math.sqrt((velocity3[0] ** 2) + (velocity3[1] ** 2)))) / 3.0
        if scorer.lower() == "black":
            self.BLACK_GOAL_SPEEDS.append(round(speed, 3))
            self.fb["db"].update({'BLACK_GOAL_SPEEDS': self.BLACK_GOAL_SPEEDS})
        elif scorer.lower() == "white":
            self.WHITE_GOAL_SPEEDS.append(round(speed, 3))
            self.fb["db"].update({'WHITE_GOAL_SPEEDS': self.WHITE_GOAL_SPEEDS})

    def gameOver(self):
        if (self.BLACK_SCORE >= self.winCap or self.WHITE_SCORE >= self.winCap) and (abs(self.BLACK_SCORE - self.WHITE_SCORE) >= self.winBy):
            return "BLACK WINS!" if self.BLACK_SCORE > self.WHITE_SCORE else "WHITE WINS!"
        return False


    def startGame(self):
        streamB = self.fb["db"].child("BLACK_GOALS").stream(self.blackListener)
        streamW = self.fb["db"].child("WHITE_GOALS").stream(self.whiteListener)
        streamR = self.fb["db"].child("RESET").stream(self.resetListener)


        cap = cv2.VideoCapture(1)
        cap.set(3, 1280)
        cap.set(4, 720)

        self.clearGame()

        # keep looping
        while True:
            ret, frame = cap.read()

            if frame is None:
                print("No frame detected")
                break

            self.frames.appendleft(frame)

            frame = imutils.resize(frame, width=1000)
            mask = self.createMask(frame)
            contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)
            center = None

            frame = self.annotateFrame(frame)

            # only proceed if at least one contour was found
            if len(contours):
                # find the largest contour in the mask, then use it to compute the minimum enclosing circle and centroid
                c = max(contours, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # only proceed if the radius meets a minimum size
                if 1 <= radius <= 15 and 52 < x < 880:
                    # draw the circle and centroid on the frame, then update the list of tracked points
                    cv2.circle(frame, (int(x), int(y)),
                            int(radius), (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (255, 0, 0), -1)
                    self.pts.appendleft(center)

                
                self.evaluateScore(x, y)
                self.evaluatePossession(x, y)
                

            frame = self.renderContrail(frame)
            # show the frame to our screen
            cv2.imshow("STRYKER V1", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break
        streamW.close()
        streamB.close()
        streamR.close()

        cap.release()
        cv2.destroyAllWindows()


game = Game()
game.startGame()