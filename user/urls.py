from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'user'

urlpatterns = [
    # URLs REGISTER & PROFILE
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),

    # URLs LOGOUT, LOGIN
    path('login/', views.CustomLoginView.as_view(template_name='user/login.html'), name='login'),
    path('logout/', views.CustomLogoutView.as_view(template_name='user/logout.html'), name='logout'),

    # URLs RESET PASSWORD (bắt đầu bằng username)
    path('username-reset/', views.UsernameResetView.as_view(), name='username_reset'),

    # URLs RESET PASSWORD mặc định của Django
    path('password-reset/', views.CustomPasswordResetView.as_view(
        template_name='user/password_reset_form.html',
        email_template_name='user/password_reset_email.html',
        success_url=reverse_lazy('user:password_reset_done') 
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user/password_reset_confirm.html',
        success_url=reverse_lazy('user:password_reset_complete') 
    ), name='password_reset_confirm'),
    
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user/password_reset_complete.html'
    ), name='password_reset_complete'),
]