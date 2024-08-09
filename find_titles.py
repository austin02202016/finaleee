from googleapiclient.discovery import build
import isodate

# Replace with your own API key
api_key = "AIzaSyBYIbxcnq3wJqaMBD1qECD0ba3T95mx6Rc"
# Create a YouTube resource object
youtube = build('youtube', 'v3', developerKey=api_key)

# Function to get all video IDs from your channel that are less than 60 seconds and posted after a specific date
def get_short_video_ids(channel_id, published_after):
    video_ids = []
    request = youtube.search().list(
        part="id",
        channelId=channel_id,
        maxResults=50,
        type="video",
        videoDuration="short",  # Only get short videos (less than 4 minutes)
        publishedAfter=published_after
    )
    
    response = request.execute()
    
    for item in response['items']:
        video_ids.append(item['id']['videoId'])
    
    while 'nextPageToken' in response:
        request = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=50,
            type="video",
            pageToken=response['nextPageToken'],
            videoDuration="short",
            publishedAfter=published_after
        )
        response = request.execute()
        
        for item in response['items']:
            video_ids.append(item['id']['videoId'])
    
    return video_ids

# Function to get video titles by IDs
def get_video_titles(video_ids):
    video_titles = []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()
        
        for item in response['items']:
            # Check if video duration is less than 60 seconds
            duration = item['contentDetails']['duration']
            seconds = parse_duration(duration)
            if seconds < 60:
                title = item['snippet']['title']
                # Remove '#' and everything after it
                if '#' in title:
                    title = title.split('#')[0].strip()
                video_titles.append(title)
    
    return video_titles

def parse_duration(duration):
    """
    Parse an ISO 8601 duration string and return the duration in seconds.
    """
    parsed_duration = isodate.parse_duration(duration)
    return parsed_duration.total_seconds()

# Function to find and return titles
def find_titles(channel_id, published_after):
    video_ids = get_short_video_ids(channel_id, published_after)
    video_titles = get_video_titles(video_ids)
    return video_titles

# Your channel ID
channel_id = 'UCINOoCpGapKXHhxZRDBX1uQ'
# Specify the date after which videos should be considered
published_after = '2024-02-28T00:00:00Z'

# Get and store titles
titles = find_titles(channel_id, published_after)
