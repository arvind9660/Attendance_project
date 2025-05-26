import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
import face_recognition
import pyttsx3 as pyt
from .models import *

def add_new_face(face_encoding, name, frame):
    face_dir = os.path.join(settings.BASE_DIR, 'faces')
    os.makedirs(face_dir, exist_ok=True)
    new_face_image_path = os.path.join(face_dir, f'{name}.jpg')

    if frame is not None:
        saved = cv2.imwrite(new_face_image_path, frame)
        if saved:
            return face_encoding, name
    return None, None


def voice(text):
    eng = pyt.init()
    voices = eng.getProperty('voices')
    eng.setProperty('rate', 125)
    eng.setProperty('volume', 1)
    for v in voices:
        if 'Zira' in v.name:
            eng.setProperty('voice', v.id)
            break
    eng.say(text)
    eng.runAndWait()

def send_attendance_email(login_email,name, in_time, out_time, duration):
    subject = f"Attendance Recorded for {name}"
    message = f"""
    Attendance Details:
    Name: {name}
    In Time: {in_time}
    Out Time: {out_time}
    Duration: {duration}
    """
    from_email = settings.EMAIL_HOST_USER

    # Receiver email ko find karne ka logic
    receiver_email = None
    try:
        # Pehle employee check karo
        employee = Employee.objects.get(email=login_email)
        receiver_email = employee.company.smtp_email
    except Employee.DoesNotExist:
        try:
            # Agar employee nahi mila toh company check karo
            company = Company.objects.get(email=login_email)
            receiver_email = company.smtp_email
        except Company.DoesNotExist:
            print("Login email not found in Employee or Company.")
            return 0

    try:
        send_mail(subject, message, from_email, [receiver_email])
        print(f"Attendance email sent to {receiver_email}")
        return 1
    except Exception as e:
        print(f"Failed to send attendance email: {e}")
        return 0



def send_monthly_report(login_email):
    today = datetime.now()
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'report_sent.log')
    current_month_str = today.strftime("%Y-%m")

    # Report sirf 1, 2, 3 tareekh ko bhejna chahiye
    if today.day > 3:
        print("Too late to send this month's report.")
        return 0

    # Check if report already sent this month
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            sent_months = f.read().splitlines()
            if current_month_str in sent_months:
                print("Report already sent this month.")
                return 0

    # Check if report file exists
    report_path = os.path.join(settings.BASE_DIR, "attendance.xlsx")
    if not os.path.exists(report_path):
        print("Report file not found.")
        return 0

    # Determine receiver email
    receiver_email = None
    try:
        employee = Employee.objects.get(email=login_email)
        receiver_email = employee.company.smtp_email
    except Employee.DoesNotExist:
        try:
            company = Company.objects.get(email=login_email)
            receiver_email = company.smtp_email
        except Company.DoesNotExist:
            print("Login email not found.")
            return 0

    # Send email
    try:
        email = EmailMessage(
            subject="Monthly Attendance Report",
            body="Please find attached the monthly attendance report.",
            from_email=settings.EMAIL_HOST_USER,
            to=[receiver_email],
        )
        email.attach_file(report_path)
        email.send()

        os.remove(report_path)

        # Log this month's report
        with open(log_file, 'a') as f:
            f.write(current_month_str + '\n')

        print(f"Monthly report sent to {receiver_email}")
        return 1

    except Exception as e:
        print(f"Failed to send email: {e}")
        return 0



def face_attendance(login_email):
    
    video_capture = cv2.VideoCapture(1)
    if not video_capture.isOpened():
        return

    known_face_encodings = []
    known_face_names = []
    face_dir = os.path.join(settings.BASE_DIR, 'faces')
    for face_file in os.listdir(face_dir):
        img_path = os.path.join(face_dir, face_file)
        if os.path.isfile(img_path) and face_file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                name = os.path.splitext(face_file)[0].capitalize()
                known_face_names.append(name)

    attendance_file = "attendance.xlsx"
    columns = ["Name", "In Time", "Out Time", "Date", "Duration"]

    if os.path.exists(attendance_file):
        attendance_df = pd.read_excel(attendance_file, engine='openpyxl')
    else:
        attendance_df = pd.DataFrame(columns=columns)

    FACE_DISTANCE_THRESHOLD = 0.5
    marked_names = set()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if face_distances[best_match_index] < FACE_DISTANCE_THRESHOLD:
                name = known_face_names[best_match_index]
                if name in marked_names:
                    continue

                marked_names.add(name)
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H:%M:%S")
                current_date_str = current_time.strftime("%d-%m-%Y")

                existing = attendance_df[
                    (attendance_df['Name'] == name) & (attendance_df['Date'] == current_date_str)
                ]

                if existing.empty:
                    new_row = {
                        "Name": name,
                        "In Time": current_time_str,
                        "Out Time": None,
                        "Date": current_date_str,
                        "Duration": None
                    }
                    attendance_df = pd.concat([attendance_df, pd.DataFrame([new_row])], ignore_index=True)
                    voice(name + " In Time marked")
                else:
                    idx = existing.index[-1]
                    if pd.isna(attendance_df.at[idx, 'Out Time']):
                        in_time_str = attendance_df.at[idx, 'In Time']
                        in_datetime = datetime.strptime(current_date_str + " " + in_time_str, "%d-%m-%Y %H:%M:%S")
                        duration = (current_time - in_datetime).seconds
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        duration_str = f"{hours:02}:{minutes:02}"

                        attendance_df.at[idx, 'Out Time'] = current_time_str
                        attendance_df.at[idx, 'Duration'] = duration_str
                        voice(name + " Out Time marked. Duration " + duration_str)
                        send_attendance_email(login_email,name, in_time_str, current_time_str, duration_str)

                top, right, bottom, left = face_location
                center = ((left + right) // 2, (top + bottom) // 2)
                radius = min((right - left), (bottom - top)) // 2
                scaling_factor = 2
                center = (center[0] * scaling_factor, center[1] * scaling_factor)
                radius = radius * scaling_factor
                cv2.circle(frame, center, radius, (0, 255, 0), 2)
                cv2.putText(frame, name, (left * 2, bottom * 2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.imshow("Attendance", frame)
        if cv2.waitKey(2) & 0xFF in [ord("q"), ord("Q")]:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    attendance_df.to_excel(attendance_file, index=False, engine='openpyxl')
