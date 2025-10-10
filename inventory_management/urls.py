from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', auth_views.LoginView.as_view(
            template_name='user/login.html',
            redirect_authenticated_user=True 
        ), name='user-login'),

    path('dashboard/', include('dashboard.urls')),

    path('user/', include('user.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)