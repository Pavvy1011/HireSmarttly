from django.db import models
from django.utils import timezone

class Student(models.Model):

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    otp = models.CharField(max_length=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    def __str__(self):
        return self.email
class HR(models.Model):

    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    photo = models.ImageField(upload_to='hr_photos/', null=True, blank=True)

    def __str__(self):
        return self.email
        return self.email
class Resume(models.Model):

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    education = models.TextField()
    skills = models.TextField()
    experience = models.IntegerField(default=0)
    projects = models.TextField(blank=True)   # ADD THIS
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
    photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    certifications = models.TextField(blank=True)   # ADD THIS
    shortlisted = models.BooleanField(default=False)
    soft_skills = models.TextField(blank=True, null=True)
    projects = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):

    hr = models.ForeignKey(HR, on_delete=models.CASCADE, null=True, blank=True)  # 🔥 ADD THIS

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    skills = models.CharField(max_length=200)
    experience = models.IntegerField()
    description = models.TextField()
    posted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Message(models.Model):

    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    # 🔥 NEW: HR add karo (IMPORTANT)
    hr = models.ForeignKey(HR, on_delete=models.CASCADE, null=True, blank=True)

    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)

    text = models.TextField(blank=True, null=True)

    file = models.FileField(upload_to='messages/', null=True, blank=True)

    # 🔥 NEW: Interview fields (optional but BEST)
    interview_date = models.DateField(null=True, blank=True)
    interview_time = models.TimeField(null=True, blank=True)

    is_seen = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.text:
            return f"{self.student.name} - {self.text[:50]}"
        return f"{self.student.name} - File Message"

class JobApplication(models.Model):

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)

    match_percentage = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, default="pending")  # 🔥 NEW

    applied_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.job.title}"  

class Rating(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    value = models.IntegerField()   # 1 to 5




class LoginHistory(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('hr', 'HR'),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    login_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.role}"

