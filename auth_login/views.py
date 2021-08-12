import json
import logging
from pprint import pprint
from urllib import parse

import django
import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from oauth2_provider.models import AccessToken, Application

from home.models import Tokens, CartModel

logger = logging.getLogger('v2')


def give_points(personal_token, option):
    """
     Throws Error if the invite code is invalid
    @param personal_token: str
    @type option: str
    """

    if personal_token and personal_token != 'null':
        invited = Tokens.objects.get(private_token=personal_token)
        if option == 'invite':
            invited.invited += 1
            invited.points += 10
        elif option == 'review':
            invited.reviews += 1
            invited.points += 5
        elif option == 'report':
            invited.reports += 1
            invited.points += 1
        elif option == 'image':
            invited.images += 1
            invited.points += 5
        invited.save()


def parse_url_next(next_loc):
    parsed = parse.parse_qs(next_loc)
    try:
        next_loc = dict(parsed)
        return next_loc
    except Exception as e:
        logger.exception("Parser")
        return False


def get_item_from_list_dict(parsed_loc, key):
    try:
        invite = parsed_loc[key][0]
    except (IndexError, KeyError) as e:
        logger.error('item not in list ' + str(e))
        invite = ''
    return invite


def get_item_from_url(url_params, key, default=''):
    parsed_loc = parse_url_next(url_params)
    if parsed_loc:
        return get_item_from_list_dict(parsed_loc, key)
    else:
        return default


def get_client_id(next_string):
    client_id = settings.DEFAULT_CLIENT
    if next_string:
        try:
            search_query = next_string.split('?')[1]
            logger.info('search string is ' + search_query)
            client_id = get_item_from_url(search_query, 'client_id')
        except IndexError:
            logger.debug('client id was not provided')
    return client_id


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    print(x_forwarded_for)
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip



@ensure_csrf_cookie
def signin(request):
    context1 = {}
    pprint(request.META['QUERY_STRING'])
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        print(email, password)
        if not email or not password:
            context1['pswderr'] = "Text fields cannot be empty"
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            redirect_location = request.GET.get('next', '/') + '?' + request.META['QUERY_STRING']
            return HttpResponseRedirect(redirect_location)
        else:
            # Return an 'invalid login' error message.
            context1['pswderr'] = "Invalid Credentials"
    context1['sign_text'] = 'Sign In'
    context1['GOOGLE_CLIENT_ID'] = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
    context1['google_redirect_uri'] = settings.DEPLOYMENT_URL + '/google-login'
    context1['FACEBOOK_CLIENT_ID'] = settings.SOCIAL_AUTH_FACEBOOK_KEY
    context1['facebook_redirect_uri'] = settings.DEPLOYMENT_URL + '/facebook-login'
    return render(request, template_name='login.html', context=context1)


@ensure_csrf_cookie
def signup(request):
    context1 = {}
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        passwrd2 = request.POST.get("password retype")
        username = request.POST.get("username", '')
        firstname = request.POST.get("firstname", "")
        lastname = request.POST.get("lastname", "")
        if not email:
            context1['pswderr'] = 'Email cannot be empty'
            logger.info('Email was empty')
        elif not password or not passwrd2:
            context1['pswderr'] = 'Password cannot be empty'
            logger.info('Password was empty')
        elif not username:
            context1['pswderr'] = 'Username cannot be empty'
            logger.info('Username was empty')
        else:
            if passwrd2 == password:
                try:
                    inv = request.POST.get('invite', '')
                    give_points(inv, 'invite')
                    user = User.objects.create_user(email=email, password=password, username=username,
                                                    first_name=firstname, last_name=lastname)
                    token,_ = Tokens.objects.get_or_create(user=user)
                    token.invite_token=inv
                    token.save()
                    CartModel.objects.get_or_create(user=user)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    redirect_location = request.GET.get('next', '/') + '?' + request.META['QUERY_STRING']
                    return HttpResponseRedirect(redirect_location)

                except IntegrityError as e:
                    print(e)
                    logger.info('User already exist')
                    context1['pswderr'] = 'User already exists'
                except Tokens.DoesNotExist as e:
                    print(e)
                    logger.info('Token was invalid')
                    context1['pswderr'] = 'Invalid Token'

            else:
                logger.info('Password Does not match')
                context1['pswderr'] = 'Password Does not match'

    next_loc = request.GET.get('next', '')
    context1['sign_text'] = "Register"
    context1['invite'] = get_item_from_url(next_loc, 'invite')
    context1['redirect_uri'] = settings.DEPLOYMENT_URL + '/google-login'
    context1['GOOGLE_CLIENT_ID'] = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
    context1['FACEBOOK_CLIENT_ID'] = settings.SOCIAL_AUTH_FACEBOOK_KEY
    context1['facebook_redirect_uri'] = settings.DEPLOYMENT_URL + '/facebook-login'
    return render(request, template_name="signup.html", context=context1)


@login_required
def log_out(request):
    logout(request)
    url = '/?' + request.META['QUERY_STRING']
    return HttpResponseRedirect(url)



def request_google(auth_code, redirect_uri):
    data = {'code': auth_code,
            'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            'client_secret': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'}
    r = requests.post('https://oauth2.googleapis.com/token', data=data)
    try:
        logger.info('google auth_login ')
        content = json.loads(r.content.decode())
        token = content["access_token"]
        return token
    except Exception as e:
        logger.exception('google auth_login fail')
        logger.debug(r.content.decode())
        return False


def convert_google_token(token, client_id):
    application = Application.objects.get(client_id=client_id)
    data = {
        'grant_type': 'convert_token',
        'client_id': client_id,
        'client_secret': application.client_secret,
        'backend': 'google-oauth2',
        'token': token
    }
    url = settings.DEPLOYMENT_URL + '/auth/social/convert-token'
    r = requests.post(url, data=data)
    try:
        logger.info('google auth_login convert')
        cont = json.loads(r.content.decode())
        access_token = cont['access_token']
        return access_token
    except Exception as e:
        logger.exception('google convert failed')
        logger.debug(r.content.decode())
        return False


def Google_login(request):
    state = request.GET.get('state', '/')
    auth_code = request.GET.get('code')
    redirect_uri = settings.DEPLOYMENT_URL + '/google-login'

    next_loc = get_item_from_url(state, 'next', '/')
    logger.info('next ' + next_loc)
    invite_token = get_item_from_url(next_loc, 'invite')
    client_id = get_client_id(next_loc)
    logger.info('Recived client id ' + client_id)
    token = request_google(auth_code, redirect_uri)
    if token:
        logger.info(' Token Success')
        access_token = convert_google_token(token, client_id)
        if access_token:
            user = AccessToken.objects.get(token=access_token).user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            try:

                token_of_user, _ = Tokens.objects.get_or_create(user=user)
                if not token_of_user.invite_token:
                    token_of_user.invite_token = invite_token
                token_of_user.save()
            except:
                logger.exception('failed to create token')
            try:
                give_points(invite_token, 'invite')
            except Exception:
                logger.exception('tokens point giving failure')

        return HttpResponseRedirect(next_loc)
    return HttpResponseRedirect('/login/')


def request_facebook(auth_code, redirect_uri):
    data = {'code': auth_code,
            'client_id': settings.SOCIAL_AUTH_FACEBOOK_KEY,
            'client_secret': settings.SOCIAL_AUTH_FACEBOOK_SECRET,
            'redirect_uri': 'https://127.0.0.1:8000/facebook-login',
            'grant_type': 'authorization_code'}
    print(data)
    r = requests.get('https://graph.facebook.com/v11.0/oauth/access_token?', params=data)
    try:
        logger.info('facebook auth_login ')
        content = json.loads(r.content.decode())
        print(content)
        token = content["access_token"]
        logger.info('token is ' + token)
        return token
    except Exception as e:
        logger.exception('facebook auth_login fail')
        logger.debug(r.content.decode())
        return False


def convert_facebook_token(token, client_id):
    try:
        application = Application.objects.get(client_id=client_id)
    except:
        logger.exception('failed to get application')
        return False
    data = {
        'grant_type': 'convert_token',
        'client_id': application.client_id,
        'client_secret': application.client_secret,
        'backend': 'facebook',
        'token': token
    }
    logger.info('trying to trying url')
    url = 'http://127.0.0.1:8000/auth/social/convert-token'
    r = requests.post(url, data=data)
    logger.info('recived the request')
    try:
        logger.info('facebook auth_login convert')
        cont = json.loads(r.content.decode())
        print(cont)
        access_token = cont['access_token']
        return access_token
    except Exception as e:
        logger.exception('facebook convert failed')
        print(e)
        logger.debug(r.content.decode())
        return False


def Facebook_login(request):
    state = request.GET.get('state', '/')
    auth_code = request.GET.get('code')
    logger.info('url is ', settings.DEPLOYMENT_URL)
    redirect_uri = settings.DEPLOYMENT_URL + '/facebook-login/'
    print(redirect_uri)
    next_loc = get_item_from_url(state, 'next', '/')
    logger.info('next ' + next_loc)
    invite_token = get_item_from_url(next_loc, 'invite')
    client_id = get_client_id(next_loc)
    logger.info('Recived client id ' + client_id)
    logger.info('Trying access token')
    token = request_facebook(auth_code, redirect_uri)
    logger.info('Trying access token')
    if token:
        logger.info('Trying access token')
        access_token = convert_facebook_token(token, client_id)
        logger.info('received access token')
        if access_token:
            user = AccessToken.objects.get(token=access_token).user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            try:

                token, _ = Tokens.objects.get_or_create(user=user)
                if not token.invite_token:
                    token.invite_token = invite_token
                token.save()
            except:
                logger.exception('failed to create token')
            try:
                give_points(invite_token, 'invite')
            except Exception:
                logger.exception('tokens')

        return HttpResponseRedirect(next_loc)
    return HttpResponseRedirect('/login/')