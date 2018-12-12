from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
import os, json, operator
from datetime import datetime
from .models import UserProfile, Hobby

# Global scope
currentAccount = ""

def index(request):
    return render(request,'matchingapp/home.html')

def loginPage(request):
    return render(request, 'matchingapp/login.html')

def register(request):
    return render(request,'matchingapp/register.html')

def getHobbies(request):
    hobbies = list(Hobby.objects.all().values())
    return JsonResponse(hobbies, safe=False)

@csrf_exempt
def authenticate(request):
    if 'username' in request.session:
        data = [{"success":True, "username":request.session['username']}]
        return JsonResponse(data, safe=False)

    else:
        data = [{"success": False}]
        return JsonResponse(data, safe=False)

@csrf_exempt
def registerUser(request):
    username = request.POST["username"]
    email = request.POST["email"]

    if(validateInput(username, email)):
        firstName = request.POST["firstName"]
        lastName = request.POST["lastName"]
        password = request.POST["password"]

        newUser = User.objects.create_user(username, email, password, first_name=firstName, last_name=lastName)
        newUser.save()

        hobbies = json.loads(request.POST['hobbies'])
        if not hobbies:
            data = [{"success":"false", "message":"no hobbies selected"}]
            return JsonResponse(data, safe=False)

        dob = request.POST["dateOfBirth"]
        userGender = request.POST["gender"]

        if request.FILES:
            image = request.FILES["profileImage"]
        else:
            image = "image/default.png"

        newProfile = UserProfile.objects.create(user=newUser, gender=userGender, dateOfBirth=dob, bio="", profileImage=image)

        for hobby in hobbies:
            userHobby = Hobby.objects.get(name=hobby)
            newProfile.hobby.add(userHobby)

        request.session['username'] = username
        request.session['password'] = password

        data = [{"success":"true"}]
        return JsonResponse(data, safe=False)

    else:
        data = [{"success":"false", "message":"user or email taken"}]
        return JsonResponse(data, safe=False)

def checkUsername(username):
    if(User.objects.filter(username=username).exists()):
        return False
    else:
        return True

def checkEmail(email):
    if(User.objects.filter(email=email).exists()):
        return False
    else:
        return True

def validateInput(username, email):
    if(checkUsername(username) and checkEmail(email)):
        return True
    else:
        return False

@csrf_exempt
def login(request):
    username = request.POST["username"]
    password = request.POST["password"]
    try:
        user = User.objects.get(username=username)

        if(user.check_password(password)):
            request.session['username'] = username
            request.session['password'] = password

            currentAccount = username
            data = [{"success":"true","username": username}]
            return JsonResponse(data, safe=False)

        else:
            data = [{"success":"false",  "message": "incorrect password"}]
            return JsonResponse(data, safe=False)

    except User.DoesNotExist:
        data = [{"success":"false",  "message": "user does not exist"}]
        return JsonResponse(data, safe=False)

@csrf_exempt
def logout(request):
    if 'username' in request.session:
        request.session.flush()
        print("---------USER LOGGED OUT------------------")
        data = [{"success":"true"}]

        return JsonResponse(data, safe=False)

    else:
        data = [{"success":"false"}]
        return JsonResponse(data, safe=False)

def profile(request):
    return render(request,'matchingapp/profile.html')

def settingsPage(request):
    return render(request,'matchingapp/settings.html')

@csrf_exempt
def loadUser(request):
    username = request.POST["username"]
    user = User.objects.get(username=username)
    userProfile = UserProfile.objects.get(user=user)
    hobbies = userProfile.hobby.all()

    userHobbies = []
    for hobby in hobbies:
        userHobbies.append(str(hobby))

    try:
        profileImage = userProfile.profileImage.url
    except:
        profileImage = None

    data = [{
        "success": "true",
        "id": user.id,
        "username": user.username,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "dob": userProfile.dateOfBirth,
        "bio": userProfile.bio,
        "image": profileImage,
        "hobbies": userHobbies,
        "gender": userProfile.gender,
    }]
    return JsonResponse(data, safe=False)

@csrf_exempt
def getProfiles(request):
    username = request.session['username']
    user = User.objects.get(username=username) # get me
    profiles = list(UserProfile.objects.all().values().exclude(user=user)) # get all profiles but mine
    users = list(User.objects.all().values().exclude(username=username)) # get all users but me
    content = {
        'profiles': profiles,
        'users': users,
    }
    return JsonResponse(content, safe=False)

@csrf_exempt
def update(request):
    userID = request.POST['id']
    newUsername = request.POST['username']
    newFirstName = request.POST['firstName']
    newLastName = request.POST['lastName']
    newDOB = request.POST['dateOfBirth']
    newBio = request.POST['bio']
    newGender = request.POST['gender']

    user = User.objects.get(id=userID)
    profile = UserProfile.objects.get(user=user)

    user.username = newUsername
    user.first_name = newFirstName
    user.last_name = newLastName

    profile.dateOfBirth = newDOB
    profile.bio = newBio
    profile.gender = newGender

    if request.FILES:
        profile.profileImage = request.FILES["profileImage"]
    else:
        profile.profileImage = "image/default.png"

    user.save()
    profile.save()

    request.session['username'] = newUsername

    return JsonResponse({"success": True}, safe=False)

@csrf_exempt
def delete(request):
    body = json.loads(request.body.decode('utf-8'))
    item = body['id']
    post = User.objects.get(id=item)
    post.delete()
    return HttpResponse("success")

@csrf_exempt
def lookupMatches(request):
    count = 0;
    matches = {};

    myUsername = request.session['username']
    me = User.objects.get(username=myUsername)
    myProfile = UserProfile.objects.get(user=me)
    myHobbies = myProfile.hobby.all().values('name')

    theirProfiles = UserProfile.objects.all().exclude(user=me)
    for profile in theirProfiles:
        theirHobbies = profile.hobby.all().values('name')
        for theirHobby in theirHobbies:
            for myHobby in myHobbies:
                if(myHobby == theirHobby):
                    count = count + 1

        if(count == 0):
            matches[profile.user.username] = 0

        else:
            matches[profile.user.username] = count
        count = 0

    users = []
    userMatches = []
    userImages = []
    userProfiles = []
    sortedV = sorted(matches.items(), key=operator.itemgetter(1), reverse=True)
    for key in sortedV:
        name, theirMatches = key
        users.append(name)
        userMatches.append(theirMatches)

    for user in users:
        theUser = User.objects.get(username=user)
        theirProfile = UserProfile.objects.all().values().get(user=theUser)
        userProfiles.append(theirProfile)

    content = {
        'users': users,
        'profiles': userProfiles,
        'matches': userMatches
    }

    return JsonResponse(content, safe=False)
