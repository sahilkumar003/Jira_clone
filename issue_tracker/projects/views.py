from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from .models import Project, Member
from users.models import User
from django.contrib import messages
from .serializers import ProjectSerializer
from django.http import request
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail


class CreateProjectView(LoginRequiredMixin, TemplateView):
    template_name = "projects/project_create.html"
    login_url = "signin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.exclude(id=self.request.user.id)
        context["users"] = users
        return context

    def post(self, request):
        print(request.POST)
        print(request.user)
        data = {
            "title": request.POST.get("title"),
            "description": request.POST.get("description"),
            "members": [],
            "owner": request.user.id,
        }
        serializer = ProjectSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            project = serializer.save()
            members = request.POST.getlist("members")
            for member_id in members:
                user = User.objects.get(id=member_id)
                role = request.POST.get(f"member_role_{member_id}")
                Member.objects.create(user=user, project=project, role=role)

                subject = "You have been added to a project"
                message = f"You have been added to the project '{project.title}'."
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [user.email]
                send_mail(subject, message, email_from, recipient_list)

            messages.success(request, "Project has been successfully created")
            return redirect("projects:dashboard")
        else:
            print(serializer.errors)
            context = self.get_context_data(serializer_errors=serializer.errors)
            return self.render_to_response(context)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "projects/dashboard.html"
    login_url = "signin"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        filter_param = self.kwargs.get("filter_param")

        if filter_param == "owned":
            projects = Project.objects.filter(owner=user)
        elif filter_param == "member":
            projects = Project.objects.filter(members=user)
        else:
            projects = Project.objects.all()

        context["projects"] = projects
        return context
