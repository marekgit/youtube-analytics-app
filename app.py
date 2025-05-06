import os
import re
import streamlit as st
import validators
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Environment variables are loaded in get_api_key()

# Set page configuration
st.set_page_config(
    page_title="YouTube Analytics App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF0000;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #606060;
        margin-bottom: 1rem;
    }
    .stat-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 10px;
    }
    .stat-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FF0000;
    }
    .channel-info {
        margin-top: 20px;
        padding: 20px;
        background-color: #f9f9f9;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

def get_api_key():
    """Get YouTube API key from environment variable.
    
    Works with both local .env files and deployed environment variables.
    """
    # Try to load from .env file first (local development)
    try:
        load_dotenv()
    except Exception:
        pass
        
    # Get API key from environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        st.error("YouTube API key not found. Please set the YOUTUBE_API_KEY environment variable.")
        st.stop()
    return api_key

def extract_channel_id(youtube, url):
    """Extract channel ID from various YouTube URL formats."""
    # Check if it's already a channel ID format
    if url.startswith("UC") and len(url) == 24:
        return url
    
    # Handle different URL formats
    channel_id = None
    
    # Pattern for channel URLs
    channel_pattern = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:channel\/|c\/|@)([a-zA-Z0-9_-]+)'
    channel_match = re.match(channel_pattern, url)
    
    if channel_match:
        channel_username = channel_match.group(1)
        
        # If it's a direct channel ID
        if channel_username.startswith("UC"):
            return channel_username
        
        # If it's a custom URL or handle (@username)
        try:
            if url.find("@") > -1:
                # Handle @username format
                request = youtube.search().list(
                    part="snippet",
                    q=channel_username,
                    type="channel",
                    maxResults=1
                )
                response = request.execute()
                if response["items"]:
                    return response["items"][0]["snippet"]["channelId"]
            else:
                # Handle /c/customname format
                request = youtube.channels().list(
                    part="id",
                    forUsername=channel_username
                )
                response = request.execute()
                if response["items"]:
                    return response["items"][0]["id"]
        except HttpError as e:
            st.error(f"An error occurred: {e}")
            return None
    
    # Try to find channel from video URL
    video_pattern = r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)'
    video_match = re.match(video_pattern, url)
    
    if video_match:
        video_id = video_match.group(1)
        try:
            request = youtube.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()
            if response["items"]:
                return response["items"][0]["snippet"]["channelId"]
        except HttpError as e:
            st.error(f"An error occurred: {e}")
            return None
    
    return channel_id

def get_channel_stats(youtube, channel_id):
    """Get channel statistics from YouTube API."""
    try:
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        )
        response = request.execute()
        
        if not response["items"]:
            return None
        
        return response["items"][0]
    except HttpError as e:
        st.error(f"An error occurred: {e}")
        return None

def format_number(number, use_exact=False, precision=1):
    """Format large numbers for better readability.
    
    Args:
        number: The number to format
        use_exact: If True, format with commas (e.g., 2,268,347), otherwise abbreviate
        precision: Number of decimal places to show when abbreviating (default: 1)
    """
    if use_exact:
        return f"{number:,}"
    else:
        if number >= 1000000:
            return f"{number/1000000:.{precision}f}M"
        elif number >= 1000:
            return f"{number/1000:.{precision}f}K"
        else:
            return str(number)

def main():
    """Main function to run the Streamlit app."""
    st.markdown('<h1 class="main-header">YouTube Analytics App</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Analyze any YouTube channel by entering its URL</p>', unsafe_allow_html=True)
    
    # Input for YouTube channel URL
    channel_url = st.text_input("Enter YouTube Channel URL", placeholder="https://www.youtube.com/@username or https://www.youtube.com/channel/UC...")
    
    if channel_url:
        # Validate URL
        if not validators.url(channel_url) and not (channel_url.startswith("UC") and len(channel_url) == 24):
            st.error("Please enter a valid YouTube URL or channel ID")
            st.stop()
        
        # Initialize YouTube API client
        api_key = get_api_key()
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        with st.spinner("Fetching channel data..."):
            # Extract channel ID
            channel_id = extract_channel_id(youtube, channel_url)
            
            if not channel_id:
                st.error("Could not find a valid channel ID from the provided URL")
                st.stop()
            
            # Get channel statistics
            channel_data = get_channel_stats(youtube, channel_id)
            
            if not channel_data:
                st.error("Could not retrieve channel data")
                st.stop()
            
            # Display channel information
            snippet = channel_data["snippet"]
            statistics = channel_data["statistics"]
            
            # Channel header with thumbnail
            col1, col2 = st.columns([1, 3])
            with col1:
                st.image(snippet["thumbnails"]["high"]["url"], width=200)
            with col2:
                st.markdown(f"## {snippet['title']}")
                st.markdown(f"**Channel ID:** `{channel_id}`")
                if "customUrl" in snippet:
                    # Remove @ if it's already in the customUrl
                    custom_url = snippet['customUrl']
                    if custom_url.startswith('@'):
                        st.markdown(f"**Custom URL:** {custom_url}")
                    else:
                        st.markdown(f"**Custom URL:** @{custom_url}")
                if "country" in snippet:
                    st.markdown(f"**Country:** {snippet['country']}")
                st.markdown(f"**Created:** {snippet['publishedAt'][:10]}")
            
            # Channel description
            with st.expander("Channel Description"):
                st.markdown(snippet["description"])
            
            # Channel statistics
            st.markdown("## Channel Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div class="stat-container">', unsafe_allow_html=True)
                st.markdown('<p class="stat-header">Subscribers</p>', unsafe_allow_html=True)
                if "hiddenSubscriberCount" in statistics and statistics["hiddenSubscriberCount"]:
                    subscriber_count = "Hidden"
                else:
                    subscriber_count = format_number(int(statistics["subscriberCount"]), precision=2)
                st.markdown(f'<p class="stat-value">{subscriber_count}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="stat-container">', unsafe_allow_html=True)
                st.markdown('<p class="stat-header">Total Views</p>', unsafe_allow_html=True)
                view_count = format_number(int(statistics["viewCount"]), use_exact=True)
                st.markdown(f'<p class="stat-value">{view_count}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="stat-container">', unsafe_allow_html=True)
                st.markdown('<p class="stat-header">Videos</p>', unsafe_allow_html=True)
                video_count = format_number(int(statistics["videoCount"]), use_exact=True)
                st.markdown(f'<p class="stat-value">{video_count}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
