from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms import LoginForm, SignUpForm
from apps.documents.models import Document
from apps.study.models import ChatSession, GeneratedMaterial
from services.progress_service import get_progress_summary


def landing_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "landing.html")


@login_required
def dashboard_view(request):
    documents = Document.objects.filter(user=request.user)[:6]
    sessions = ChatSession.objects.filter(user=request.user).select_related("document")[:5]
    materials = GeneratedMaterial.objects.filter(user=request.user)[:5]
    progress = get_progress_summary(request.user)
    return render(
        request,
        "dashboard.html",
        {
            "documents": documents,
            "sessions": sessions,
            "materials": materials,
            "progress": progress,
        },
    )


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your study companion is ready.")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("landing")
