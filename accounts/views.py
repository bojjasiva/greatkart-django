
from django.shortcuts import render,redirect
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required

from .forms import RegistrationForm
from .models import Account
from django.http import HttpResponse
from carts.models import Cart, CartItem
from carts.views import _cart_id
import requests

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
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()

                # Getting products and varaiations from cart before login
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    product_variation = []
                    ci_id_cart = []
                    for item in cart_item:
                        variation = item.variation.all()                       
                        product_variation.append(list(variation))
                        ci_id_cart.append(item.id)
                        
                    
                # Getting products and variations from user account in database
                    cart_item = CartItem.objects.filter(user=user)
                    exst_var_list = []
                    ci_id = []
                    for item in cart_item:
                        variation = item.variation.all()
                        exst_var_list.append(list(variation))
                        ci_id.append(item.id)

                # Saving product if variation is already exist in user account from databse
                    for pr in product_variation:
                        index = product_variation.index(pr)
                        item_id_pr = ci_id_cart[index]
                        if pr in exst_var_list:
                            index = exst_var_list.index(pr)
                            item_id = ci_id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                # Saving product if variation not existing in account items from database
                        else:
                            index = product_variation.index(pr)
                            item_id_pr = ci_id_cart[index]
                            cart_item = CartItem.objects.get(id=item_id_pr)
                            cart_item.user = user
                            cart_item.save()
                            # cart_item = CartItem.objects.filter(cart=cart)
                            # for item in cart_item:
                            #     item.user = user
                            #     item.save()
                    
            except:
                pass
            auth.login(request, user)

            # Code to redirect url to /cart/checkout after login with cart items
            url = request.META.get('HTTP_REFERER')
            # url value is 'next=/cart/checkout'
            try:
                query = requests.utils.urlparse(url).query

                # Creating a dictionary from string
                params=dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
                # params valus is "{'next':'/cart/checkout'}"

            except:
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


