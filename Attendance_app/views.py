import os
import cv2
import face_recognition
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from .forms import EmployeeRegistrationForm
from django.contrib.auth.hashers import make_password,check_password
from .models import *
from .face_reco import *
from .record import get_record
from .st_record import st_record

# --------------------
# Original Web Views
# --------------------

def home(request):
    return render(request, 'home.html')  

def std_record(request):
    folder_path = ''
    files = st_record(folder_path)
    return render(request, 'show_folder.html', {'files': files, 'MEDIA_URL': settings.MEDIA_URL})

def index(request):
    if not request.session.get('company_id') and not request.session.get('employee_id'):
        return redirect('home')

    login_email = request.session.get('company_email') or request.session.get('employee_email')
   


    if login_email:
        send_monthly_report(login_email)

    return render(request, 'index.html')



def record(request):
    records = get_record()
    if records:
        return render(request, 'record.html', {'records': records})
    else:
        messages.error(request, 'No Data Found!')
        return render(request, 'record.html') 

def my_face_recognition(request):
    login_email = request.session.get('employee_email') or request.session.get('company_email')
    face_attendance(login_email)
    return redirect('index')
    

def add_face(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        uploading_file = request.FILES.get("image")

        if not name or not uploading_file:
            return HttpResponse("Error: Name or image not provided.", status=400)

        temp_img_path = os.path.join(settings.MEDIA_ROOT, "temp_image.jpg")
        with open(temp_img_path, "wb") as f:
            for chunk in uploading_file.chunks():
                f.write(chunk)

        try:
            image = face_recognition.load_image_file(temp_img_path)
            face_locations = face_recognition.face_locations(image)

            if face_locations:
                top, right, bottom, left = face_locations[0]
                face_frame = image[top:bottom, left:right]
                face_frame_bgr = cv2.cvtColor(face_frame, cv2.COLOR_RGB2BGR)
                face_encodings = face_recognition.face_encodings(image, [face_locations[0]])

                if face_encodings:
                    face_encoding = face_encodings[0]
                    add_new_face(face_encoding, name, face_frame_bgr)
                    os.remove(temp_img_path)
                    return render(request, 'add_face.html', {'x': f"Face Added Successfully: {name}"})
                else:
                    os.remove(temp_img_path)
                    return HttpResponse("Error: Unable to encode the face.", status=400)
            else:
                os.remove(temp_img_path)
                return HttpResponse("Error: No face detected in the image.", status=400)

        except Exception as e:
            return HttpResponse(f"Unexpected error: {str(e)}", status=500)

    return render(request, "add_face.html")


def delete_image(request, file_name):
    image_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(image_path):
        os.remove(image_path)
        return render(request, 'show_folder.html', {'x': f"Image {file_name} Deleted Successfully"})
    else:
        return JsonResponse({"error": f"Image {file_name} not found"}, status=404)


def company_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

       
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

          
            request.session.flush()

        
            try:
                company = Company.objects.get(email=email)
                request.session['company_id'] = company.id
                request.session['company_email'] =company.email
            except Company.DoesNotExist:
                pass

            return redirect('index')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'company_login.html')


def employee_login(request):
    companies = Company.objects.all()

    if request.method == 'POST':
        company_id = request.POST.get('company')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            employee = Employee.objects.get(email=email, company_id=company_id)

            if check_password(password, employee.password):
               
                request.session.flush()


                request.session['employee_id'] = employee.id
                request.session['employee_email'] = employee.email
                return redirect('index')
            else:
                messages.error(request, 'Invalid password.')
        except Employee.DoesNotExist:
            messages.error(request, 'Invalid company or email.')

    return render(request, 'employee_login.html', {'companies': companies})

def employee_register(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST, request.FILES)  
        if form.is_valid():
            employee = form.save(commit=False)
            employee.password = make_password(form.cleaned_data['password'])
            employee.save()
            messages.success(request, 'Employee registered successfully!')
            return redirect('employee_login')
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'employee_register.html', {'form': form})

# views.py

from .forms import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

def company_register(request):
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            plain_password = form.cleaned_data['password']
            company.password = make_password(plain_password)
            company.save()

            
            User.objects.create_user(
                username=company.email,
                email=company.email,
                password=plain_password
            )

            messages.success(request, 'Company registered successfully!')
            return redirect('company_login')
    else:
        form = CompanyRegistrationForm()
    return render(request, 'company_register.html', {'form': form})


def company_logout(request):
    logout(request)
    request.session.flush()
    return redirect('home')


