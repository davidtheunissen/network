from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
import json

from .models import User, Post, Follow, Like


def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    # Pagination
    paginator = Paginator(allPosts, 10)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    allLikes = Like.objects.all()
    youLiked = []

    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                youLiked.append(like.post.id)
    except:
        pass

    return render(request, "network/index.html", {
        "allPosts": allPosts,
        "page_posts": page_posts,
        "youLiked": youLiked,
    })


def new_post(request):
    if request.method == "POST":
        content = request.POST['content']
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        
        return HttpResponseRedirect(reverse(index)) 


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        
        return JsonResponse({"message": "Edit successful!", "data": data["content"]})


def add_like(request,post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newLike = Like(user=user, post=post)
    newLike.save()
    
    return JsonResponse({"message": "Like added!"})


def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    
    return JsonResponse({"message": "Like removed!"})


def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    userPosts = Post.objects.filter(user=user).order_by("id").reverse()

    following = Follow.objects.filter(follower=user)
    followers = Follow.objects.filter(followed=user)

    try:
        checkFollow = followers.filter(user=user.objects.get(pk=request.user.id))
        if len(checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False

    # Pagination
    paginator = Paginator(userPosts, 10)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        "username": user.username,
        "page_posts": page_posts,
        "following": following,
        "followers": followers,
        "user_profile": user,
    })    


def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followedUsers = Follow.objects.filter(follower=currentUser)
    allPosts = Post.objects.all().order_by('id').reverse()
    
    followingPosts = []

    for post in allPosts:
        for person in followedUsers:
            if person.followed == post.user:
                followingPosts.append(post)

    # Pagination
    paginator = Paginator(followingPosts, 10)
    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_posts": page_posts,
    })


def follow(request):
    userFollow = request.POST['user_follow']

    # Create user object
    currentUser = User.objects.get(pk=request.user.id)
    userFollowData = User.objects.get(username=userFollow)
    f = Follow(follower=currentUser, followed=userFollowData)
    f.save()
    user_id = userFollowData.id
    
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def unfollow(request):
    userFollow = request.POST['user_follow']

    # Create user object
    currentUser = User.objects.get(pk=request.user.id)
    userFollowData = User.objects.get(username=userFollow)
    f = Follow(follower=currentUser, followed=userFollowData)
    f.delete()
    user_id = userFollowData.id
    
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id})) 


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
