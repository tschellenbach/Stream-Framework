from django.shortcuts import render_to_response
from pinterest_example.models import Item
from django.template.context import RequestContext
from django.contrib.auth import get_user_model


def homepage(request):
    if request.user.is_authenticated():
        response = trending(request)
    else:
        response = render_to_response('pinterest_example/homepage.html')
    return response


def feed(request):
    response = render_to_response('pinterest_example/people_i_follow.html')
    return response


def trending(request):
    context = RequestContext(request)
    popular = Item.objects.all()[:10]
    context['popular'] = popular
    response = render_to_response('pinterest_example/trending.html', context)
    return response


def profile(request, username):
    profile_user = get_user_model().objects.get(username=username)
    context = RequestContext(request)
    context['profile_user'] = profile_user
    response = render_to_response('pinterest_example/profile.html', context)
    return response


def pin(request):
    pass


def follow(request):
    pass
