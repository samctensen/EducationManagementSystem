from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from datetime import *
from django.utils import timezone
from . import models
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.db.models import Count
from django.views.decorators.http import require_GET, require_POST
from django.template.defaulttags import register
from django.utils.safestring import mark_safe
from django.core.exceptions import PermissionDenied

# Create your views here.

def get_user_type(user):
    if user.is_authenticated:
        if user.groups.filter(name="Students").exists():
            return 1
        if user.groups.filter(name="Teaching Assistants").exists():
            return 2
        if user.is_superuser:
            return 4
    else:
        return 3

def is_ta(user):
    if user.is_authenticated:
        if user.groups.filter(name="Teaching Assistants").exists():
            return True
        if user.is_superuser:
            return True
        return False
    return False

def is_student(user):
    if user.is_authenticated:
        if user.groups.filter(name="Students").exists():
            return True
        else:
            return False
    return False

@login_required
def assignments(request):
    try:
        assignments = models.Assignment.objects.all()
    except models.Assignment.DoesNotExist:
        raise Http404("No existing assignments")
    return render(request, "assignments.html",  {'assignments':assignments})

@login_required
def index(request, assignment_id): 
        try:
            assignment = models.Assignment.objects.get(id=assignment_id)
        except models.Assignment.DoesNotExist:
             raise Http404("No Assignment with id " + str(assignment_id))
        userType = get_user_type(request.user)
        if userType == 3:
            taID = None
        else:
            taID = models.User.objects.get(username=request.user.username)
        yourSubmissions = models.Submission.objects.filter(grader=taID).filter(assignment=assignment_id).count()
        totalSubmissions = models.Submission.objects.filter(assignment=assignment_id).count()
        totalStudents = models.Group.objects.get(name="Students").user_set.count()
        isNotDue = assignment.deadline > timezone.now()
        return render(request, "index.html", {'assignment':assignment, 'totalSubmissions':totalSubmissions, 'totalStudents':totalStudents, 'yourSubmissions':yourSubmissions, 'userType':userType, 'user': request.user, 'isNotDue': isNotDue})

@register.filter(is_safe=True)
def studentSubmission(assignment_id, user):
    if (get_user_type(user) == 1):
        assignment = models.Assignment.objects.get(id=assignment_id)
        try:
            submission = models.Submission.objects.filter(assignment=assignment_id).get(author=user)
            if submission.score != None:
                return mark_safe("<p>Your submission, " + "<a href=/uploads/" + submission.file.name + "/>" + submission.file.name + "</a>, received " + str(submission.score) + "/" + str(format(assignment.points, '.1f')) + " points (" + str(round((submission.score / assignment.points * 100), 1)) + "%)</p>")
            else:
                if assignment.deadline < timezone.now():
                    return mark_safe("<p>Your submission, <a href=/uploads/" + submission.file.name + "/>" + submission.file.name + "</a>, is being graded</p>")
                else:
                    return mark_safe("<p id='submissionComment'>Your current submission is <a href=/uploads/" + submission.file.name + "/>" + submission.file.name + "</a>")
        except models.Submission.DoesNotExist:
            if assignment.deadline > timezone.now():
                return mark_safe("<p id='submissionComment'>No current submission</p>")
            else:
                return mark_safe("<p>You did not submit this assignment and received 0 points</p>")
            

@user_passes_test(is_ta)
@login_required
def submissions(request, assignment_id):
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404("No Assignment with id " + str(assignment_id))
    userType = get_user_type(request.user)
    if userType == 2:
        taID = models.User.objects.get(username=request.user.username)
        submissions = models.Submission.objects.filter(grader=taID).filter(assignment__id=assignment_id).order_by('author__username')
    if userType == 4:
         submissions = models.Submission.objects.filter(assignment__id=assignment_id).order_by('author__username')
    return render(request, "submissions.html", {'assignment':assignment, 'submissions':submissions})

@login_required
def profile(request):
    try:
        assignments = models.Assignment.objects.all()
    except models.Assignment.DoesNotExist:
        raise Http404("No existing assignments")
    return render(request, "profile.html", {'assignments':assignments, 'user':request.user, 'userType':get_user_type(request.user)})

@register.filter
def gradedSubmissions(assignment_id, user):
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404("No existing assignments")
    deadline = assignment.deadline
    if deadline >= timezone.now():
        return "Not due"
    if get_user_type(user) == 2:
        taID = models.User.objects.get(username='ta1')
        graded = models.Submission.objects.filter(grader=taID).filter(assignment=assignment_id).exclude(score__isnull=True).count()
        yourSubmissions = models.Submission.objects.filter(grader=taID).filter(assignment=assignment_id).count()
        return str(graded) + "/" + str(yourSubmissions)
    if get_user_type(user) == 4:
        graded = models.Submission.objects.filter(assignment=assignment_id).exclude(score__isnull=True).count()
        totalSubmissions = models.Submission.objects.filter(assignment=assignment_id).count()
        return str(graded) + "/" + str(totalSubmissions)
    
@register.filter
def gradeAssignment(assignment_id, user):
    if get_user_type(user) == 1:
        assignment = models.Assignment.objects.get(id=assignment_id)
        try:
            submission = models.Submission.objects.filter(assignment=assignment_id).get(author=user)
            if submission.score == None:
                return "Ungraded"
            else:
                return str(round((submission.score / assignment.points * 100), 1)) + "%"
        except models.Submission.DoesNotExist:
            if assignment.deadline > timezone.now():
                return "Not Due"
            else:
                return "Missing"
            
@register.filter
def calculateGrade(assignments, user):
    if get_user_type(user) == 1:
        availableGradePoints = 0
        earnedGradePoints = 0
        for assignment in assignments:
            if assignment.deadline < timezone.now():
                try:
                    submission = models.Submission.objects.filter(assignment=assignment.id).get(author=user)
                    if submission.score != None:
                        availableGradePoints = availableGradePoints + assignment.weight
                        gradePercentage = submission.score / assignment.points
                        earnedGradePoints = earnedGradePoints + (gradePercentage * assignment.weight)
                except models.Submission.DoesNotExist:
                    availableGradePoints = availableGradePoints + assignment.weight
        return str(round((earnedGradePoints / availableGradePoints * 100), 1)) + "%"

def login_form(request):
    if (request.method == 'POST'):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        next = request.POST.get("next", "/profile/")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next, user=user)
        else:
            error = "Username and password do not match"
            return render(request, "login.html", {'error': error, 'next': next})
    else:
        next = request.GET.get("next", "/profile/")
        return render(request, "login.html", {'next': next})
    
def logout_form(request):
    logout(request)
    return redirect(f"/profile/login/")
        
@user_passes_test(is_ta)
@login_required
@require_POST
def grade(request, assignment_id):
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404("No Assignment with id " + str(assignment_id))
    for key in request.POST:
        if (key[:6] == 'grade-'):
            submissionID = int(key[6:])
            print(submissionID)
            grade = float(request.POST[key])
            if grade < 0:
                grade = 0
            try:
                submission = models.Submission.objects.get(id=submissionID)
            except models.Submission.DoesNotExist:
                raise Http404("No Submission with id " + str(assignment_id))
            try:
                submission.score = grade
            except ValueError as e:
                submission.score = None
            submission.save()
    return redirect(f"/{assignment_id}/submissions")

@user_passes_test(is_student)
@login_required
@require_POST
def submit(request, assignment_id):
    try:
        assignment = models.Assignment.objects.get(id=assignment_id)
        submissionFile = request.FILES['submission']
        try:
            submission = models.Submission.objects.filter(assignment=assignment.id).get(author=request.user)
            submission.file = submissionFile
        except models.Submission.DoesNotExist:
            submission = models.Submission.objects.create(
                assignment=assignment,
                author=request.user,
                grader=pick_grader(assignment),
                file=submissionFile,
                score = None,
            )
        submission.save()
        return redirect(f"/{assignment_id}/")
    except models.Assignment.DoesNotExist:
        raise Http404("No Assignment with id " + str(assignment_id))
    
def pick_grader(assignment):
    tas = models.Group.objects.get(name='Teaching Assistants').user_set
    count = tas.annotate(total_assigned = Count('graded_set')).order_by('total_assigned').reverse()
    return count[0]

@login_required
def show_upload(request, filename):
    try:
        submission = models.Submission.objects.get(file=filename)
        if request.user == submission.author or request.user == submission.grader or request.user.is_superuser:
            with submission.file.open() as fd:
                response = HttpResponse(fd)
                response["Content-Disposition"] = \
                    f'attachment; filename="{submission.file.name}"'
                return response
        else:
            raise PermissionDenied("Incorrect user")
    except models.Submission.DoesNotExist:
        raise Http404("No submission with name " + filename)
    