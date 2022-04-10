
from django.shortcuts import render,redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from .forms import RegistrationForm
from .models import Account
from django.http import HttpResponse

# Email Verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            mobile = form.cleaned_data['mobile']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email,  password=password, mobile=mobile)
            #user.mobile = mobile
            user.save()

            # User Account Activation Email:
            current_site = get_current_site(request)
            mail_subject = 'Please Activate MyKart Account'
            message = render_to_string('accounts/account_verification_email.html',{
                'user'   : user,
                'domain' : current_site,
                'uid'    : urlsafe_base64_encode(force_bytes(user.pk)),
                'token'  : default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            #messages.success(request, 'Registration Successful.')

            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        'form' : form,
    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method=='POST':
        email = request.POST['email']
        password = request.POST['password']
        user_status = Account.objects.get(email=email)
        if user_status.is_active:
            user = auth.authenticate(email=email, password=password)
        else:
            messages.error(request, 'Email Verification pending.! Please verify email by clicking the link sent to your registered email.. ')
            return redirect('login')
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Credentials.! Try Again.. ')
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid Activation Link')
        return redirect('register')

@login_required(login_url = 'login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            current_site = get_current_site(request)
            mail_subject = 'Please Reset Your MyKart Account Password'
            message = render_to_string('accounts/password_reset_email.html',{
                'user'   : user,
                'domain' : current_site,
                'uid'    : urlsafe_base64_encode(force_bytes(user.pk)),
                'token'  : default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Password Reset Link Has Been Sent To Your Email Address. Please Follow The Link To Reset Your Password')
            return redirect('login')

        else:
            messages.error(request, "Account Doesn't Exist.! Plrease Check The Email Address That Is Eeing Entered.")
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetPasswordValidate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Saving uid in the session
        request.session['uid'] = uid
        messages.success(request, 'Please Reset Your Account Paaaword')
        return redirect('resetPassword')
    else:
        messages.error(request, 'Password Reset Link Has Expired.')
        return redirect('forgotPassword')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirmPassword = request.POST['confirmPassword']
        if password == confirmPassword:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password Reset Successful. Please Try Login..')
            return redirect('login')
        else:
            messages.error(request, "Password Doesn't Match.! Try Again")
            return render(request, 'accounts/reset_password.html')
    else:
        return render(request, 'accounts/reset_password.html')


