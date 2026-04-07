from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render   # 👈 IMPORTANT
from django.conf import settings
from django.conf.urls.static import static

# 👇 Home function define karo
def home(request):
    return render(request, 'home.html')

urlpatterns = [
      path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', home, name='home'),   # 👈 Now it will work
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    
    
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



