from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
import random
from .models import Student, Resume, HR, Job, JobApplication
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.views.decorators.cache import never_cache



def calculate_job_match(resume, job):

    # 🔹 SKILL MATCH
    resume_skills = set((resume.skills or "").lower().split(","))
    job_skills = set((job.skills or "").lower().split(","))

    matched_skills = resume_skills.intersection(job_skills)

    if len(job_skills) > 0:
        skill_score = (len(matched_skills) / len(job_skills)) * 100
    else:
        skill_score = 0


    # 🔹 EXPERIENCE MATCH
    resume_exp = resume.experience or 0
    job_exp = job.experience or 0

    if resume_exp >= job_exp:
        exp_score = 100
    else:
        if job_exp > 0:
            exp_score = (resume_exp / job_exp) * 100
        else:
            exp_score = 0


    # 🔹 FINAL SCORE (50% skill + 50% experience)
    final_score = (skill_score * 0.5) + (exp_score * 0.5)

    return round(final_score, 2)

def check_match(request, job_id):

    email = request.session.get("student_email")

    student = Student.objects.get(email=email)

    resume = Resume.objects.filter(student=student).last()

    if not resume:
        return redirect("create_resume")

    job = Job.objects.get(id=job_id)

    score = calculate_job_match(resume, job)

    return render(request,"job_match.html",{
        "job": job,
        "score": score
    })

# --------------------
# INDEX & ROLE
# --------------------
def index(request):
    return render(request, 'index.html')


def role(request):
    return render(request, 'home.html')


# --------------------
# STUDENT SIGNUP
# --------------------
def student_signup(request):

    if request.method == "POST":

        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if Student.objects.filter(email=email).exists():
            return render(request, 'student_signup.html', {
                'error': 'Email already registered'
            })

        otp = str(random.randint(100000, 999999))

        request.session['signup_name'] = name
        request.session['signup_email'] = email
        request.session['signup_password'] = password
        request.session['otp'] = otp

        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp}",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return redirect('otp_verify')

    return render(request, 'student_signup.html')


# --------------------
# OTP VERIFY
# --------------------
def otp_verify(request):

    if request.method == "POST":

        user_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if user_otp == session_otp:

            Student.objects.create(
                name=request.session.get('signup_name'),
                email=request.session.get('signup_email'),
                password=request.session.get('signup_password')
            )

            request.session['student_email'] = request.session.get('signup_email')

            return redirect("student_dashboard")

        else:
            return render(request, "otp_verify.html", {"error": "Invalid OTP"})

    return render(request, "otp_verify.html")


# --------------------
# RESEND OTP
# --------------------
def resend_otp(request):

    email = request.session.get("signup_email")

    if not email:
        return redirect("student_signup")

    otp = str(random.randint(100000, 999999))
    request.session['otp'] = otp

    send_mail(
        "Your New OTP Code",
        f"Your new OTP is {otp}",
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

    return redirect("otp_verify")


# --------------------
# STUDENT LOGIN
# --------------------
def student_login(request):

    if request.method == 'POST':

        email = request.POST['email']
        password = request.POST['password']

        try:

            student = Student.objects.get(email=email, password=password)

            request.session['student_email'] = email

            return redirect('student_dashboard')

        except Student.DoesNotExist:

            return render(request, 'student_login.html', {
                'error': 'Invalid Email or Password'
            })

    return render(request, 'student_login.html')


# --------------------
# STUDENT DASHBOARD
# --------------------
def student_dashboard(request):

    email = request.session.get('student_email')

    if not email:
        return redirect('student_login')

    student = Student.objects.get(email=email)

    # Resume
    resume = Resume.objects.filter(student=student).last()

    # ✅ Recommended Jobs (simple logic)
    recommended_jobs = []
    if resume and resume.skills:
        skills = [s.strip().lower() for s in resume.skills.split(',')]

        all_jobs = Job.objects.all()

        for job in all_jobs:
            job_skills = job.skills.lower()

            for skill in skills:
                if skill in job_skills:
                    recommended_jobs.append(job)
                    break

    # limit 5 jobs
    recommended_jobs = recommended_jobs[:5]

    # ✅ Apply Count
    applied_count = JobApplication.objects.filter(student=student).count()

    return render(request, 'student_dashboard.html', {
        'student': student,
        'recommended_jobs': recommended_jobs,
        'applied_count': applied_count
    })
# --------------------
# STUDENT LOGOUT
# --------------------
def student_logout(request):
    return redirect("give_rating")

# --------------------
# FORGOT PASSWORD
# --------------------
@never_cache
def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        try:

            student = Student.objects.get(email=email)

            otp = str(random.randint(100000, 999999))

            request.session['reset_email'] = email
            request.session['reset_otp'] = otp

            send_mail(
                "Password Reset OTP",
                f"Your OTP for password reset is {otp}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )

            return redirect("reset_otp")

        except Student.DoesNotExist:

            return render(request, "forgot_password.html", {
                "error": "Email not registered"
            })

    return render(request, "forgot_password.html")


# --------------------
# VERIFY RESET OTP
# --------------------
def reset_otp(request):

    if request.method == "POST":

        user_otp = request.POST.get("otp")
        session_otp = request.session.get("reset_otp")

        if user_otp == session_otp:

            return redirect("reset_password")

        else:

            return render(request, "reset_otp.html", {
                "error": "Invalid OTP"
            })

    return render(request, "reset_otp.html")


# --------------------
# RESET PASSWORD
# --------------------
def reset_password(request):

    if request.method == "POST":

        password = request.POST.get("password")
        email = request.session.get("reset_email")

        student = Student.objects.get(email=email)

        student.password = password
        student.save()

        return redirect("student_login")

    return render(request, "reset_password.html")


# --------------------
# CREATE RESUME
# --------------------
from .models import Resume, Student   # 👈 aa import jaruri chhe

def create_resume(request):

    email = request.session.get('student_email')

    if not email:
        return redirect('student_login')

    student = Student.objects.get(email=email)

    if request.method == 'POST':

        name = request.POST.get('name')
        education = request.POST.get('education')
        skills = request.POST.get('skills')
        experience = request.POST.get('experience')
        photo = request.FILES.get('photo')
        resume_file = request.FILES.get('resume')   # 👈 aa file lai rahya chhe
        soft_skills = request.POST.get('soft_skills')
        projects = request.POST.get('projects')
        Resume.objects.create(
    student=student,
    name=name,
    education=education,
    skills=skills,
    soft_skills=soft_skills,
    projects=projects,
    experience=experience,
    photo=photo,
    resume_file=resume_file   # ✅ aa sachu chhe
        )

        return redirect('view_resume')

    return render(request, 'create_resume.html', {'student': student})
# --------------------
# VIEW RESUME
# --------------------
def view_resume(request):

    email = request.session.get('student_email')

    if not email:
        return redirect('student_login')

    student = Student.objects.get(email=email)

    # ✅ safer way
    resume = Resume.objects.filter(student=student).order_by('-id').first()

    if not resume:
        return redirect('create_resume')

    # ✅ SAFE SPLIT (NO ERROR)
    skills_list = []
    if resume.skills:
        skills_list = [s.strip() for s in resume.skills.split(',') if s.strip()]

    soft_skills_list = []
    if resume.soft_skills:
        soft_skills_list = [s.strip() for s in resume.soft_skills.split(',') if s.strip()]

    return render(request, 'view_resume.html', {
    'resume': resume,
    'skills_list': skills_list,
    'soft_skills_list': soft_skills_list,
    'student': student   # 🔥 ADD THIS
})
# --------------------
# HR SIGNUP
# --------------------
@never_cache
def hr_signup(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        if HR.objects.filter(email=email).exists():

            return render(request, 'hr_signup.html', {
                'error': 'Email already exists'
            })

        HR.objects.create(email=email, password=password)

        return redirect('hr_login')

    return render(request, 'hr_signup.html')


# --------------------
# HR LOGIN
# --------------------
@never_cache
def hr_login(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        hr = HR.objects.filter(email=email, password=password).first()

        if hr:

            request.session['hr_email'] = email

            return redirect('hr_dashboard')

        else:

            return render(request, 'hr_login.html', {
                'error': 'Invalid Login'
            })

    return render(request, 'hr_login.html')


# --------------------
# HR DASHBOARD
# --------------------
def hr_dashboard(request):
    email = request.session.get('hr_email')

    if not email:
        return redirect('hr_login')

    hr = HR.objects.get(email=email)

    total_resumes = Resume.objects.count()
    shortlisted = Resume.objects.filter(shortlisted=True).count()
    jobs_posted = Job.objects.count()

    return render(request, "hr_dashboard.html", {
        "hr": hr,
        "total_resumes": total_resumes,
        "shortlisted": shortlisted,
        "jobs_posted": jobs_posted
    })

# --------------------
# HR RESUMES
# --------------------
def hr_resumes(request):

    email = request.session.get("hr_email")

    # 🔥 Login check
    if not email:
        return redirect("hr_login")

    try:
        hr = HR.objects.get(email=email)
    except HR.DoesNotExist:
        return redirect("hr_login")

    # 🔍 Filter inputs
    skill = request.GET.get('skill')
    exp = request.GET.get('exp')

    resumes = Resume.objects.all()

    # 🔥 Skill filter
    if skill:
        resumes = resumes.filter(skills__icontains=skill)

    # 🔥 Experience filter
    if exp:
        resumes = resumes.filter(experience__gte=exp)

    # 🔥 Score calculate
    for r in resumes:
        r.score = r.experience * 20

    # ✅ Send data to template
    return render(request, 'hr_resumes.html', {
        'resumes': resumes,
        'hr': hr
    })

# --------------------
# SHORTLIST RESUME
# --------------------
def shortlist_resume(request, id):

    resume = Resume.objects.get(id=id)

    resume.shortlisted = True

    resume.save()

    return redirect('view_resumes')
# --------------------
# SHORTLISTED STUDENTS
# --------------------
# --------------------
# SHORTLISTED STUDENTS
# --------------------
def shortlisted_students(request):

    email = request.session.get('hr_email')
    if not email:
        return redirect('hr_login')

    hr = HR.objects.get(email=email)

    # 🔥 ONLY APPROVED APPLICATIONS
    applications = JobApplication.objects.filter(
        job__hr=hr,
        status="approved"
    ).select_related('student', 'job')

    # 🔥 FILTER
    job_filter = request.GET.get('job')

    if job_filter:
        applications = applications.filter(job__title=job_filter)

    data = []

    for app in applications:

        resume = Resume.objects.filter(student=app.student).last()

        data.append({
            "job_title": app.job.title,
            "student_name": app.student.name,
            "skills": resume.skills if resume else "No Skills",
            "experience": resume.experience if resume else 0,
            "match": app.match_percentage
        })

    jobs = Job.objects.filter(hr=hr)

    return render(request, "shortlisted.html", {
        "hr": hr,
        "data": data,
        "jobs": jobs
    })




def view_resumes(request):

    email = request.session.get("hr_email")

    hr = HR.objects.get(email=email)

    resumes = Resume.objects.all()

    return render(request,'hr_resumes.html',{
        'resumes':resumes,
        'hr':hr
    })
# --------------------
# POST JOB
# --------------------
def post_job(request):

    email = request.session.get("hr_email")

    if not email:
        return redirect("hr_login")

    hr = HR.objects.get(email=email)

    if request.method == "POST":

        title = request.POST.get("title")
        company = request.POST.get("company")
        skills = request.POST.get("skills")
        experience = request.POST.get("experience")
        description = request.POST.get("description")

        Job.objects.create(
    hr=hr,  # 🔥 move this TOP
    title=title,
    company=company,
    skills=skills,
    experience=experience,
    description=description
)

    return render(request,"post_job.html",{
        "hr": hr
    })




from django.http import JsonResponse

from .models import Message, Student
from datetime import date, timedelta
def messages(request):

    email = request.session.get("hr_email")

    if not email:
        return redirect("hr_login")

    hr = HR.objects.get(email=email)

    if request.method == "POST":
        text = request.POST.get("message")
        file = request.FILES.get("file")

        student = Student.objects.first()

        Message.objects.create(
            student=student,
            text=text,
            file=file
        )

    all_messages = Message.objects.all().order_by("created_at")

    # 🔥 GROUP BY DATE
    grouped_messages = {}

    today = date.today()
    yesterday = today - timedelta(days=1)

    for msg in all_messages:
        msg_date = msg.created_at.date()

        if msg_date == today:
            key = "Today"
        elif msg_date == yesterday:
            key = "Yesterday"
        else:
            key = msg_date.strftime("%d %b %Y")

        if key not in grouped_messages:
            grouped_messages[key] = []

        grouped_messages[key].append(msg)

    return render(request, "messages.html", {
        "hr": hr,
        "grouped_messages": grouped_messages
    })
from django.http import JsonResponse

def messages_data(request):

    messages = Message.objects.select_related('student').all().order_by("created_at")  
    # 🔥 select_related → fast + safe

    data = []

    for m in messages:
        data.append({
            "student_name": m.student.name if m.student else "Unknown",  # ✅ FIX
            "job_title": m.job.title if m.job else "No Job",
            "text": m.text,
            "file": m.file.url if m.file else None,

            "time": m.created_at.strftime("%H:%M"),
            "full_date": m.created_at.strftime("%Y-%m-%d"),

            "interview_date": str(m.interview_date) if m.interview_date else "",
            "interview_time": str(m.interview_time) if m.interview_time else "",

            "seen": m.is_seen
        })

    return JsonResponse({"messages": data})



def approve_with_interview(request):

    if request.method == "POST":

        app_id = request.POST.get("application_id")
        date = request.POST.get("date")
        time = request.POST.get("time")

        application = JobApplication.objects.get(id=app_id)
        application.status = "approved"
        application.save()

        student = application.student
        job = application.job

        hr_email = request.session.get("hr_email")
        hr = HR.objects.get(email=hr_email)

        # 🔥 message send
        Message.objects.create(
            student=student,
            hr=hr,
            job=job,
            text="You are selected for interview",
            interview_date=date,
            interview_time=time
        )

        return redirect("view_applicants")

from .models import Message


def student_messages(request):

    email = request.session.get("student_email")
    student = Student.objects.get(email=email)

    messages = Message.objects.filter(student=student).order_by('created_at')

    resume = Resume.objects.filter(student=student).first()

    return render(request, "student_messages.html", {
        "messages": messages,
        "shortlisted": resume.shortlisted if resume else False,
    })

from django.shortcuts import redirect, get_object_or_404
from .models import Resume, Message, JobApplication

def approve_student(request, application_id):

    application = get_object_or_404(JobApplication, id=application_id)

    # 🔥 already approved hoy to duplicate na thay
    if application.status != "approved":

        application.status = "approved"
        application.save()

        # 🔥 duplicate message avoid
        if not Message.objects.filter(
            student=application.student,
            job=application.job
        ).exists():

            Message.objects.create(
                student=application.student,
                job=application.job,
                text=f"🎉 Congratulations {application.student.name}! You are approved for {application.job.title} job."
            )

    return redirect('view_applicants')
def reject_student(request, application_id):

    application = get_object_or_404(JobApplication, id=application_id)

    application.status = "rejected"
    application.save()

    return redirect('view_applicants')


# --------------------
# VIEW JOBS
# --------------------
def view_jobs(request):

    jobs = Job.objects.all()

    return render(request, "jobs.html", {"jobs": jobs
                                         })


# --------------------
# STUDENT JOBS
# --------------------

from .models import Job

def student_jobs(request):

    email = request.session.get("student_email")

    if not email:
        return redirect("student_login")

    student = Student.objects.get(email=email)

    # 🔥 applied jobs find karo
    applied_jobs = JobApplication.objects.filter(student=student).values_list('job_id', flat=True)

    # 🔥 applied jobs remove karo
    jobs = Job.objects.exclude(id__in=applied_jobs)

    return render(request, "student_jobs.html", {"jobs": jobs,
                                                 'student': student })
# --------------------
# APPLY JOB
# --------------------
def apply_job(request, job_id):

    email = request.session.get("student_email")

    if not email:
        return redirect("student_login")

    student = Student.objects.get(email=email)
    job = Job.objects.get(id=job_id)

    # 🔥 duplicate prevent
    if JobApplication.objects.filter(student=student, job=job).exists():
        return redirect("student_jobs")

    # 🔥 IMPORTANT FIX (resume check)
    resume = Resume.objects.filter(student=student).last()

    if not resume:
        return redirect("create_resume")   # Resume nathi → create page

    # match calculate
    score = calculate_job_match(resume, job)

    # create application
    JobApplication.objects.create(
        student=student,
        job=job,
        match_percentage=score
    )

    return redirect("student_jobs")

def recommended_jobs(request):

    email = request.session.get("student_email")

    if not email:
        return redirect("student_login")

    student = Student.objects.get(email=email)

    resume = Resume.objects.filter(student=student).last()

    jobs = Job.objects.all()

    job_scores = []

    for job in jobs:

        score = calculate_job_match(resume, job)

        # Only show jobs with 70% or more match
        if score >= 70:

            job_scores.append({
                "job": job,
                "score": score
            })

    job_scores = sorted(job_scores, key=lambda x: x["score"], reverse=True)

    return render(request, "recommended_jobs.html", {
        "job_scores": job_scores,
        "student": student
    })
# --------------------
# VIEW APPLICANTS
# --------------------
def view_applicants(request):

    email = request.session.get('hr_email')
    if not email:
        return redirect('hr_login')

    hr = HR.objects.get(email=email)

    # 🔥 only HR jobs (dropdown mate)
    jobs = Job.objects.filter(hr=hr)

    # 🔥 only this HR applicants
    applications = JobApplication.objects.select_related('student', 'job')\
        .filter(job__hr=hr)

    # 🔥 FILTERS
    skill = request.GET.get('skill')
    job_filter = request.GET.get('job')

    if skill:
        applications = applications.filter(student__resume__skills__icontains=skill)

    if job_filter:
        applications = applications.filter(job__title=job_filter)

    # 🔥 SORT by match %
    applications = applications.order_by('-match_percentage')

    applicant_data = []

    for app in applications:

        resume = Resume.objects.filter(student=app.student).last()

        applicant_data.append({
            "job_title": app.job.title,
            "student_name": app.student.name,
            "skills": resume.skills if resume else "No Skills",
            "experience": f"{resume.experience} Years" if resume else "No Experience",
            "resume_file": resume.resume_file if resume and resume.resume_file else None,
            "match": app.match_percentage,
            "status": app.status,
            "application_id": app.id
        })

    return render(request, "view_applicants.html", {
        "hr": hr,
        "applicant_data": applicant_data,
        "jobs": jobs   # 🔥 IMPORTANT ADD
    })


# --------------------
# HR MESSAGES
# --------------------
def hr_messages(request):

    return render(request, 'messages.html')


# --------------------
# GENERAL LOGOUT
# --------------------
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):

    logout(request)

    return redirect('home')


# --------------------
# LANDING PAGE
# --------------------
def landing(request):

    return render(request, 'landing.html')



def hr_profile(request):
    email = request.session.get('hr_email')

    if not email:
        return redirect('hr_login')

    hr = HR.objects.get(email=email)

    if request.method == "POST":
        name = request.POST.get("name")
        photo = request.FILES.get("photo")

        if name:
            hr.name = name.title()

        if photo:
            hr.photo = photo

        hr.save()
        return redirect("hr_profile")

    return render(request, "hr_profile.html", {"hr": hr})

from .models import Student

def student_profile(request):

    email = request.session.get("student_email")

    student = Student.objects.get(email=email)

    if request.method == "POST":

        student.name = request.POST.get("name")

        if request.FILES.get("photo"):
            student.photo = request.FILES.get("photo")

        student.save()

        return redirect("student_profile")

    return render(request, "student_profile.html", {"student": student})
def edit_resume(request):

    email = request.session.get('student_email')

    if not email:
        return redirect('student_login')

    student = Student.objects.get(email=email)

    resume = Resume.objects.filter(student=student).first()

    # 👉 safety check
    if not resume:
        return redirect('create_resume')

    if request.method == "POST":

        # ===== BASIC DATA =====
        name = request.POST.get("name")
        resume.name = name
        resume.education = request.POST.get("education")
        resume.skills = request.POST.get("skills")

        # ===== NEW FIELDS =====
        resume.soft_skills = request.POST.get("soft_skills")
        resume.projects = request.POST.get("projects")

        resume.experience = request.POST.get("experience")

        # ===== 🔥 NAME SYNC (SIDEBAR FIX) =====
        student.name = name
        student.save()

        # ===== PHOTO UPDATE =====
        if request.FILES.get("photo"):
            photo = request.FILES.get("photo")

            # resume photo
            resume.photo = photo

            # 🔥 sidebar photo
            student.photo = photo
            student.save()

        # ===== RESUME FILE UPDATE =====
        if request.FILES.get("resume"):
            resume.resume_file = request.FILES.get("resume")

        # ===== SAVE =====
        resume.save()

        return redirect("view_resume")

    return render(request, "edit_resume.html", {
        "resume": resume,
        "student": student
})
from .models import Resume, JobApplication
from django.db.models import Avg

def about(request):

    resume_count = Resume.objects.count()

    match_count = JobApplication.objects.count()

    rating_avg = 0
    rating_avg = Rating.objects.aggregate(avg=Avg('value'))['avg'] or 0
    rating_avg = round(rating_avg, 1)

    rating_avg = round(rating_avg, 1)

    return render(request, "about.html", {
        "resume_count": resume_count,
        "match_count": match_count,
        "rating_avg": rating_avg,
    })


# --------------------
# rating
# --------------------

from .models import Rating


from .models import Student, Rating

def give_rating(request):

    email = request.session.get("student_email")

    # 🛑 Jo login nathi hoy to redirect
    if not email:
        return redirect("student_login")

    try:
        student = Student.objects.get(email=email)
    except Student.DoesNotExist:
        return redirect("student_login")

    if request.method == "POST":
        rating_value = request.POST.get("rating")

        Rating.objects.create(
            student=student,
            value=rating_value
        )

        # rating pachi logout karo
        request.session.flush()
        return redirect("student_login")

    return render(request, "rating.html")

def send_message(request, student_id, job_id):

    # 🔥 HR session check
    hr_email = request.session.get("hr_email")

    if not hr_email:
        return redirect("hr_login")

    hr = HR.objects.get(email=hr_email)

    student = Student.objects.get(id=student_id)
    job = Job.objects.get(id=job_id)

    if request.method == "POST":

        text = request.POST.get("message")
        file = request.FILES.get("file")

        # 🔥 CREATE MESSAGE (correct indent)
        Message.objects.create(
            student=student,
            hr=hr,
            job=job,
            text=text,
            file=file,
            interview_date=request.POST.get("date"),
            interview_time=request.POST.get("time")
        )

        return redirect("view_applicants")

    return render(request, "send_message.html", {
        "student": student,
        "job": job
    })

#------------------exel-------------------

import openpyxl
from django.http import HttpResponse
from .models import Resume

def export_excel(request):

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resume Report"

    # HEADER
    ws.append(["Name", "Skills", "Experience"])

    # DATA
    for r in Resume.objects.all():
        ws.append([
            r.name,
            r.skills,
            r.experience
        ])

    # RESPONSE
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = 'attachment; filename=resume_report.xlsx'

    wb.save(response)
    return response


from django.shortcuts import render, redirect
from .models import Resume, Job, Student, JobApplication, HR
from django.utils import timezone
from datetime import timedelta
from collections import Counter
import json

from django.contrib.auth import authenticate, login, logout


# ================= ADMIN LOGIN =================
def admin_login(request):

    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, "admin_login.html", {"error": "Invalid login"})

    return render(request, "admin_login.html")


# ================= ADMIN LOGOUT =================
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ================= ADMIN DASHBOARD =================
from collections import Counter
import json
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect

def admin_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:
        return redirect('admin_login')

    filter_type = request.GET.get("filter", "month")
    now = timezone.now()

    # ✅ FILTER RANGE
    if filter_type == "week":
        start_date = now - timedelta(days=7)
    elif filter_type == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    # ✅ FILTERED DATA
    resumes = Resume.objects.filter(created_at__gte=start_date)
    jobs = Job.objects.filter(posted_date__gte=start_date)

    total_resumes = resumes.count()
    total_jobs = jobs.count()
    total_students = Student.objects.count()
    total_shortlisted = Resume.objects.filter(shortlisted=True).count()

    # =========================
    # 🔥 CHART DATA (IMPORTANT FIX)
    # =========================

    resume_data = []
    job_data = []
    application_data = []

    for i in range(7):
        day = now - timedelta(days=i)

        resume_count = Resume.objects.filter(created_at__date=day.date()).count()
        job_count = Job.objects.filter(posted_date__date=day.date()).count()
        app_count = JobApplication.objects.filter(applied_date__date=day.date()).count()

        resume_data.append({"period": day.strftime("%d %b"), "count": resume_count})
        job_data.append({"period": day.strftime("%d %b"), "count": job_count})
        application_data.append({"period": day.strftime("%d %b"), "count": app_count})

    resume_data.reverse()
    job_data.reverse()
    application_data.reverse()

    # =========================
    # 🔥 SKILLS COUNT (SAFE FIX)
    # =========================

    skills_list = []
    for r in Resume.objects.all():
        if r.skills:
            skills_list.extend([s.strip() for s in r.skills.split(",") if s.strip()])

    skill_counts = Counter(skills_list)

    # =========================
    # 🔥 TOP STUDENTS
    # =========================
    top_students = Resume.objects.order_by("-experience")[:5]

    # =========================
    # 🔥 GROWTH CALCULATION FIX
    # =========================
    prev_start = start_date - timedelta(days=30)
    prev_resumes = Resume.objects.filter(
        created_at__gte=prev_start,
        created_at__lt=start_date
    ).count()

    growth = 0
    if prev_resumes > 0:
        growth = ((total_resumes - prev_resumes) / prev_resumes) * 100

    # =========================
    # 🔥 TOP SKILL
    # =========================
    top_skill = max(skill_counts, key=skill_counts.get) if skill_counts else "N/A"

    # =========================
    # 🔥 FINAL CONTEXT
    # =========================

    context = {
        "total_resumes": total_resumes,
        "total_jobs": total_jobs,
        "total_students": total_students,
        "total_shortlisted": total_shortlisted,

        "growth": round(growth, 2),
        "top_skill": top_skill,
        "top_students": top_students,

        # ✅ JSON FIX (VERY IMPORTANT)
        "resume_data": json.dumps(resume_data),
        "job_data": json.dumps(job_data),
        "application_data": json.dumps(application_data),
        "skills": json.dumps(dict(skill_counts))
    }

    return render(request, "admin_dashboard.html", context)
# ================= STUDENTS =================
def admin_students(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    search = request.GET.get("search")

    students = Student.objects.all().order_by("-id")

    if search:
        students = students.filter(name__icontains=search)

    return render(request, "admin_students.html", {
        "students": students
    })
# ================= HR =================
def admin_hr(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    hrs = HR.objects.all()
    return render(request, "admin_hr.html", {"hrs": hrs})


def delete_hr(request, id):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    HR.objects.get(id=id).delete()
    return redirect('admin_hr')


# ================= JOBS =================
def admin_jobs(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    jobs = Job.objects.all()
    return render(request, "admin_jobs.html", {"jobs": jobs})


def delete_job(request, id):
    from .models import Job

    job = Job.objects.get(id=id)
    job.delete()

    return redirect('admin_jobs')


def delete_student(request, id):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    Student.objects.filter(id=id).delete()
    return redirect('admin_students')


def delete_job(request, id):
    from .models import Job

    job = Job.objects.get(id=id)
    job.delete()

    return redirect('admin_jobs')
    