from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django import forms

# Import các View và Model
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView as BasePasswordResetView
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# Import các Form 
from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm, UserLoginForm


# =======================================================
#               VIEWS & CLASSES CHO USER
# =======================================================

# -------------------------------------------------------
#       CUSTOM LOGIN VIEW
# -------------------------------------------------------
class CustomLoginView(LoginView):
    authentication_form = UserLoginForm


# -------------------------------------------------------
#       REGISTER
# -------------------------------------------------------
def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. Please log in.')
            return redirect('user:login')
    else:    
        form = CreateUserForm()
    return render(request, 'user/register.html', {'form': form})


# -------------------------------------------------------
#   VIEW: PROFILE
# -------------------------------------------------------
def profile(request):
    return render(request, 'user/profile.html')


# -------------------------------------------------------
#           PROFILE UPDATE
# -------------------------------------------------------
def profile_update(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('user:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'user/profile_update.html', context)


# -------------------------------------------------------
#       CUSTOM LOGOUT VIEW
# -------------------------------------------------------
class CustomLogoutView(LogoutView):
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# =======================================================
#           CÁC VIEW/CLASS XỬ LÝ MẬT KHẨU 
# =======================================================

# -------------------------------------------------------
#               NHẬP USERNAME (RESET B1)
# -------------------------------------------------------
class UsernameResetForm(forms.Form):
    username = forms.CharField(max_length=150, label="Enter your username")


# -------------------------------------------------------
#           USERNAME RESET
# -------------------------------------------------------
class UsernameResetView(View):
    template_name = 'user/username_reset.html'

    def get(self, request):
        return render(request, self.template_name, {'form': UsernameResetForm()})

    def post(self, request):
        form = UsernameResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                User.objects.get(username=username)
                request.session['reset_username'] = username
                return redirect('user:password_reset')
            except User.DoesNotExist:
                messages.error(request, "Username does not exist.")
        return render(request, self.template_name, {'form': form})


# -------------------------------------------------------
#           CUSTOM PASSWORD RESET VIEW
# -------------------------------------------------------
class CustomPasswordResetView(BasePasswordResetView):
    template_name = 'user/password_reset_form.html'
    
    def post(self, request, *args, **kwargs):
        username = request.session.get('reset_username')
        
        if not username:
            messages.error(request, "Please enter username first.")
            return redirect('user:username_reset') 
        
        try:
            user = User.objects.get(username=username)
            request.POST = request.POST.copy()
            request.POST['email'] = user.email
            return super().post(request, *args, **kwargs)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('user:username_reset')