from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Video
from django.http import HttpResponseRedirect
import requests
from django.shortcuts import render
from django.conf import settings

def home(request):
    return render(request, 'videos/home.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'videos/signup.html', {'form': form})

@login_required
def save_video(request):
    if request.method == "POST":
        video_id = request.POST.get('youtube_video_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        thumbnail = request.POST.get('thumbnail_url')
        views = request.POST.get('views')

        # Save only if not already saved
        if not Video.objects.filter(user=request.user, youtube_video_id=video_id).exists():
            Video.objects.create(
                user=request.user,
                youtube_video_id=video_id,
                title=title,
                description=description,
                thumbnail_url=thumbnail,
                views=views
            )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def admin_only_view(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only.")
    

@login_required
def saved_videos(request):
    videos = Video.objects.filter(user=request.user)
    return render(request, 'videos/saved_videos.html', {'videos': videos})



def search_videos(request):
    videos = []
    if request.method == 'GET' and 'query' in request.GET:
        query = request.GET.get('query')
        api_key = settings.YOUTUBE_API_KEY

        search_url = 'https://www.googleapis.com/youtube/v3/search'
        video_url = 'https://www.googleapis.com/youtube/v3/videos'

        # Step 1: Get video IDs based on search
        search_params = {
            'part': 'snippet',
            'q': query,
            'key': api_key,
            'maxResults': 10,
            'type': 'video'
        }
        search_response = requests.get(search_url, params=search_params).json()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if video_ids:
            # Step 2: Get detailed info (views, thumbnails, etc.)
            video_params = {
                'part': 'snippet,statistics',
                'id': ','.join(video_ids),
                'key': api_key
            }
            video_response = requests.get(video_url, params=video_params).json()

            for item in video_response.get('items', []):
                video_data = {
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                    'views': item['statistics'].get('viewCount', 0),
                    'youtube_video_id': item['id']
                }
                videos.append(video_data)

    return render(request, 'videos/search.html', {'videos': videos})