from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from api.models import VerificationJob
from api.mongo import media_docs


# ------------------------------
# HOME (Landing Page)
# ------------------------------
def home(request):
    return render(request, "landing.html")


# ------------------------------
# SIGNUP
# ------------------------------
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login_view")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserCreationForm()

    return render(request, "signup.html", {"form": form})


# ------------------------------
# LOGIN
# ------------------------------
def login_view(request):
    error_message = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            error_message = "Invalid username or password."

    return render(request, "login.html", {"error": error_message})


# ------------------------------
# LOGOUT
# ------------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login_view")


# ------------------------------
# DASHBOARD (Dynamic)
# ------------------------------
@login_required
def dashboard(request):
    sql_jobs = VerificationJob.objects.filter(user=request.user).order_by('-uploaded_at')

    jobs = []

    for job in sql_jobs:
        media_doc = media_docs.find_one({"media_id": job.media_id}) or {}

        jobs.append({
            "job_id": job.job_id,
            "media_id": job.media_id,
            "status": media_doc.get("status", "processing"),
            "truthscore": media_doc.get("truthscore", None)
        })

    return render(request, "dashboard.html", {"jobs": jobs})


# ------------------------------
# UPLOAD FORM PAGE (Static UI)
# ------------------------------
@login_required
def upload_form(request):
    return render(request, "upload_form.html")


# ------------------------------
# LOADING PAGE (Dynamic job polling)
# ------------------------------
@login_required
def loading(request, job_id):
    return render(request, "loading.html", {"job_id": job_id})


# ------------------------------
# REPORT PAGE (Loads API results)
# ------------------------------
@login_required
def report(request, job_id):
    return render(request, "report.html", {"job_id": job_id})
