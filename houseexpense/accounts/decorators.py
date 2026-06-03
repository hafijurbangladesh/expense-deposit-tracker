from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_manager():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def flat_owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_flat_owner():
            messages.error(request, "You don't have permission to access this page.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper
