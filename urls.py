from django.urls import path
from . import views

urlpatterns = [

 path('', views.landing, name='landing'),

    # Role Selection Page
    path('home/', views.role, name='home'),

    # ---------------- STUDENT ----------------
    path('student-signup/', views.student_signup, name='student_signup'),
    path('student-login/', views.student_login, name='student_login'),

    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),

    path("otp-verify/", views.otp_verify, name="otp_verify"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),

    path("student-logout-main/", views.student_logout, name="student_logout_main"),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-otp/', views.reset_otp, name='reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

    # ---------------- HR ----------------

    path('hr-login/', views.hr_login, name='hr_login'),

    path('hr-dashboard/', views.hr_dashboard, name="hr_dashboard"),
    path('hr-profile/', views.hr_profile, name='hr_profile'),

    path('resumes/', views.hr_resumes, name="view_resumes"),

    path('shortlist/<int:id>/', views.shortlist_resume, name='shortlist_student'),

    path('shortlisted/', views.shortlisted_students, name="shortlisted_students"),

    path('post-job/', views.post_job, name="post_job"),

    path('jobs/', views.view_jobs, name='view_jobs'),
    path('student-jobs/', views.student_jobs, name='student_jobs'),

    path('apply-job/<int:job_id>/', views.apply_job, name='apply_job'),
    path('view-applicants/', views.view_applicants, name='view_applicants'),

    path("messages/", views.messages, name="messages"),

    path('logout/', views.logout_view, name='logout'),

    path('student-logout/', views.student_logout, name='student_logout'),

    # ---------------- Resume ----------------
    path('create-resume/', views.create_resume, name='create_resume'),
    path('view-resume/', views.view_resume, name='view_resume'),
    path('student-profile/', views.student_profile, name='student_profile'),
    path('edit-resume/', views.edit_resume, name='edit_resume'),

    path('check-match/<int:job_id>/', views.check_match, name='check_match'),
    path("recommended-jobs/", views.recommended_jobs, name="recommended_jobs"),






    # About page
    path('about/', views.about, name="about"),
    path('give-rating/', views.give_rating, name='give_rating'),



    #-----------------messece ---------------

    
    path("messages-data/", views.messages_data, name="messages_data"),
    path("messages-data/", views.messages_data, name="messages_data"),

    path('approve-interview/', views.approve_with_interview, name='approve_interview'),
    path("send-message/<int:student_id>/<int:job_id>/", views.send_message, name="send_message"),
    path("student-messages/", views.student_messages, name="student_messages"),

    # urls.py
    path('approve/<int:application_id>/', views.approve_student, name='approve_student'),
    path('reject/<int:application_id>/', views.reject_student, name='reject_student'),

    #-------------admindashbord-----------------
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('admin-students/', views.admin_students, name='admin_students'),
    path('admin-hr/', views.admin_hr, name='admin_hr'),
    path('delete-hr/<int:id>/', views.delete_hr, name='delete_hr'),
    path('admin-jobs/', views.admin_jobs, name='admin_jobs'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('delete-job/<int:id>/', views.delete_job, name='delete_job'),
    path("delete-student/<int:id>/", views.delete_student, name="delete_student"),

]