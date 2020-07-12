from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from notifications.signals import notify

from user.utilities import get_my_ports_context, get_followed_ports_context
from user.forms import MyPortsForm


def profile(request):
    return render(request, 'account/profile.html')


@login_required
def my_ports_github(request):
    handles, emails, ports_github, ports_email, ports, builder = get_my_ports_context(request, 'GitHub')

    return render(request, 'account/my_ports.html', {
        'using': 'GitHub',
        'connections': handles,
        'ports_by_email_count': ports_email,
        'ports_by_github_count': ports_github,
        'ports': ports,
        'builder': builder,
        'form': MyPortsForm(request.GET)
    })


@login_required
def my_ports_email(request):
    handles, emails, ports_github, ports_email, ports, builder = get_my_ports_context(request, 'email')

    return render(request, 'account/my_ports.html', {
        'using': 'email',
        'connections': emails,
        'ports_by_email_count': ports_email,
        'ports_by_github_count': ports_github,
        'ports': ports,
        'builder': builder,
        'form': MyPortsForm(request.GET)
    })


@login_required
def followed_ports(request):
    ports, builder = get_followed_ports_context(request)

    return render(request, 'account/followed_ports.html', {
        'ports': ports,
        'builder': builder,
        'form': MyPortsForm(request.GET)
    })


@login_required
def notifications_all(request):
    usr = request.user
    notifications = usr.notifications.all()

    return render(request, 'account/notifications.html', {
        'notifications': notifications,
    })

