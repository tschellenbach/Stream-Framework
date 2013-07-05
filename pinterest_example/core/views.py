from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.contrib.auth import get_user_model
from core.models import Item
from core import forms
from django.http import HttpResponse
import json
from django.contrib.auth.decorators import login_required
from pinterest_example.core.models import Board, Pin
from pinterest_example.core.pin_feed import PinFeed


def homepage(request):
    '''
    Homepage where you can register
    '''
    if request.user.is_authenticated():
        response = trending(request)
    else:
        response = render_to_response('core/homepage.html')
    return response


@login_required
def feed(request):
    '''
    Items pinned by the people you follow
    '''
    context = RequestContext(request)
    feed = PinFeed(request.user.id, {}, {})
    activities = list(feed[:25])
    context['feed'] = activities
    context['feed_pins'] = feed_to_pins(activities)
    response = render_to_response('core/feed.html', context)
    return response


def feed_to_pins(activities):
    pin_ids = [a.object_id for a in activities]
    pin_dict = Pin.objects.in_bulk(pin_ids)
    for a in activities:
        a.pin = pin_dict.get(a.object_id)
    return activities


def trending(request):
    '''
    The most popular items
    '''
    context = RequestContext(request)
    popular = Item.objects.all()[:10]
    context['popular'] = popular
    response = render_to_response('core/trending.html', context)
    return response


def profile(request, username):
    '''
    Shows the users profile
    '''
    profile_user = get_user_model().objects.get(username=username)
    context = RequestContext(request)
    context['profile_user'] = profile_user
    context['profile_pins'] = Pin.objects.filter(user=profile_user)
    response = render_to_response('core/profile.html', context)
    return response


@login_required
def pin(request):
    '''
    Simple view to handle (re) pinning an item
    '''
    output = {}
    if request.method == "POST":
        data = request.POST.copy()
        data['user'] = request.user.id
        form = forms.PinForm(data=data)

        if form.is_valid():
            pin = form.save()
            output['pin'] = dict(id=pin.id)
        else:
            output['errors'] = dict(form.errors.items())
    else:
        form = forms.PinForm()
    return HttpResponse(json.dumps(output), content_type='application/json')


@login_required
def follow(request):
    '''
    A view to follow other users
    '''
    output = {}
    if request.method == "POST":
        data = request.POST.copy()
        data['user'] = request.user.id
        form = forms.FollowForm(data=data)

        if form.is_valid():
            follow = form.save()
            output['follow'] = dict(id=follow.id)
        else:
            output['errors'] = dict(form.errors.items())
    else:
        form = forms.FollowForm()
    return HttpResponse(json.dumps(output), content_type='application/json')
