from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Login password
    smtp_email = models.EmailField()             # SMTP sender email
    use_tls = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class Employee(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True) 
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    face_image = models.ImageField(upload_to='', null=True, blank=True)


    def __str__(self):
        return f"{self.employee_id} - {self.name} ({self.company.name})"
    
