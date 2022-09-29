
#use ESP32 bord for this project

import face_recognition
import numpy as np
import os
from datetime import datetime,date
import cv2
import mysql.connector
from pyzbar.pyzbar import decode
import gpiozero as gp
import sys
sys.path.append('/home/pi/codeajproject/disptest')
import lcd
from time import sleep


#Pi Display
lcd.lcd_init()

#Raspberry pi PIN
face_button = gp.Button(14)
qr_button = gp.Button(18)
redled = gp.LED(15)


path = "facedetection/media"
images = []
classname = []
mylist = os.listdir(path)
print(mylist)

for cl in mylist:
    curimg = cv2.imread(f"{path}/{cl}")
    images.append(curimg)
    classname.append(os.path.splitext(cl)[0])
print(classname)
try:
    mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database = "faceDetection"
            )


    print("Database is working ")
    mycursor = mydb.cursor()

except:
    print('Datatbase is not Working..')










def findencodings(images):
    encodelist =[]
    for img in images:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodelist.append(encode)
    return encodelist


def makeAttendance(name):
    with open('att.csv', 'r+') as f:
        myDataList = f.readlines()
        nameList = []
        for line in  myDataList:
            entry = line.split(',')
            nameList.append(entry[0])
        #if name not in nameList:
        now = datetime.now()
        dtString = now.strftime('%H:%M:%S')
        f.writelines(f'\n{name},{dtString}')


def addpaperotoDb(paperno):
    sql3 = f"UPDATE students SET paperNo = '{paperno}' WHERE name= '{name}' and date = '{date.today()}'"
    mycursor.execute(sql3)
    mydb.commit()
    print('paper no. : ',paperno)
    print('name : ',name)
    print('current date : ',date.today())

def attendanceonDb(name):
    try:
        sql1 = f"SELECT * FROM students WHERE name ='{name}' and date = '{date.today()}' "
        mycursor.execute(sql1)
        myresult = mycursor.fetchall()

        if len(myresult) == 0:
            sql = "INSERT INTO students (name, datetime,date) VALUES (%s, %s, %s)"
            val = (f"{name}", f"{datetime.now()}",f"{date.today()}")
            mycursor.execute(sql, val)

        print(myresult)
        mydb.commit()
    except:
        print("Server is not Running....................")




encodelistknown = findencodings(images)
print("Encoding complete")

try:
    cap = cv2.VideoCapture(0)
    while True:
        success, img = cap.read()
        imgS = cv2.resize(img,(0,0),None,0.25,0.25)
        imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)

        #QRcode detection
        if len(decode(img)) != 0:
            if qr_button.is_pressed:
                for barcode in decode(img):
                    myData = barcode.data.decode('utf-8')
                    pts = np.array([barcode.polygon],np.int32)
                    pts = pts.reshape((-1,1,2))
                    cv2.polylines(img,[pts],True,(255,0,255),5)
                    pts2 = barcode.rect
                    cv2.putText(img,myData,(pts2[0],pts2[1]),cv2.FONT_HERSHEY_COMPLEX,0.9,(200,0,100),2)
                    #adding to database
                    addpaperotoDb(myData)
                cv2.imshow('Webcam', img)
                cv2.waitKey(1)

        #face Detection
        else:
            # if the button is pressed then only face is detected
            if face_button.is_pressed:
                facesCurFrame = face_recognition.face_locations(imgS)
                encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

                for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                    matches = face_recognition.compare_faces(encodelistknown, encodeFace)
                    faceDis = face_recognition.face_distance(encodelistknown, encodeFace)
                    matchIndex = np.argmin(faceDis)
                    # print(faceDis)
                    # print(classname[matchIndex])
                    # print(faceDis[matchIndex])

                    if matches[matchIndex] and faceDis[matchIndex] < 0.5:
                        name = classname[matchIndex].upper()
                        # print(name)
                        y1, x2, y2, x1 = faceLoc
                        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                        #attendanceonDb(name)

                        # to displya name on pi screen
                        lcd.lcd_byte(lcd.LCD_LINE_1, lcd.LCD_CMD)
                        lcd.lcd_string(name,2)

                    else:
                        name = "unknown".upper()
                        # print(name)
                        y1, x2, y2, x1 = faceLoc
                        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 0, 255), cv2.FILLED)
                        cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                        # to displya name on pi screen
                        lcd.lcd_byte(lcd.LCD_LINE_1, lcd.LCD_CMD)
                        lcd.lcd_string(name, 2)



            cv2.imshow('Webcam', img)
            cv2.waitKey(1)


    # cv2.imshow('Webcam', img)
    # cv2.waitKey(1)
except:
    print("Camera is not connected....")

