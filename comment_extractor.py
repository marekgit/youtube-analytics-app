import os
import re
import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import csv
import io
from datetime import datetime

# No Airtable integration

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # Regular expression to match YouTube video IDs in different URL formats
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_video_details(youtube, video_id):
    """Get video details from YouTube API."""
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if not response["items"]:
            return None
        
        return response["items"][0]
    except HttpError as e:
        st.error(f"An error occurred: {e}")
        return None

def get_comments(youtube, video_id, max_comments=None, progress_bar=None):
    """Get all comments and replies for a YouTube video."""
    comments = []
    next_page_token = None
    comment_count = 0
    
    try:
        # Create a progress bar if not provided
        if progress_bar is None:
            progress_bar = st.progress(0, "Fetching comments...")
        
        # Continue fetching comments until there are no more or we reach max_comments
        while True:
            # Get top-level comments
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,  # Maximum allowed by the API
                pageToken=next_page_token
            )
            response = request.execute()
            
            # Process each comment thread (top-level comment and its replies)
            for item in response["items"]:
                # Extract top-level comment
                comment = item["snippet"]["topLevelComment"]["snippet"]
                
                comments.append({
                    "commentId": item["id"],
                    "authorDisplayName": comment["authorDisplayName"],
                    "authorProfileImageUrl": comment["authorProfileImageUrl"],
                    "authorChannelUrl": comment.get("authorChannelUrl", ""),
                    "textOriginal": comment["textOriginal"],
                    "likeCount": comment["likeCount"],
                    "publishedAt": comment["publishedAt"],
                    "updatedAt": comment["updatedAt"],
                    "parentId": "",  # Top-level comments don't have a parent
                    "isReply": False
                })
                
                comment_count += 1
                
                # Extract replies if any
                if "replies" in item:
                    for reply in item["replies"]["comments"]:
                        reply_snippet = reply["snippet"]
                        
                        comments.append({
                            "commentId": reply["id"],
                            "authorDisplayName": reply_snippet["authorDisplayName"],
                            "authorProfileImageUrl": reply_snippet["authorProfileImageUrl"],
                            "authorChannelUrl": reply_snippet.get("authorChannelUrl", ""),
                            "textOriginal": reply_snippet["textOriginal"],
                            "likeCount": reply_snippet["likeCount"],
                            "publishedAt": reply_snippet["publishedAt"],
                            "updatedAt": reply_snippet["updatedAt"],
                            "parentId": reply_snippet["parentId"],
                            "isReply": True
                        })
                        
                        comment_count += 1
                
                # Update progress
                if max_comments:
                    progress = min(comment_count / max_comments, 1.0)
                    progress_bar.progress(progress, f"Fetched {comment_count} comments...")
                    
                    # Check if we've reached the maximum number of comments
                    if max_comments and comment_count >= max_comments:
                        return comments
            
            # Check if there are more pages
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
            
            # Add a small delay to avoid hitting API rate limits
            time.sleep(0.1)
        
        return comments
    
    except HttpError as e:
        st.error(f"An error occurred while fetching comments: {e}")
        return comments

def generate_csv_download_link(comments, video_title):
    """Generate a CSV file from comments and create a download link."""
    # Create a DataFrame from the comments
    df = pd.DataFrame(comments)
    
    # Clean the video title to use as filename (remove special characters)
    clean_title = re.sub(r'[^\w\s-]', '', video_title).strip().replace(' ', '_')
    filename = f"{clean_title}_comments_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Convert DataFrame to CSV
    csv = df.to_csv(index=False)
    
    # Create a download link
    b64 = io.StringIO()
    b64.write(csv)
    
    return filename, b64.getvalue()

def get_api_key():
    """Get YouTube API key from environment variable.
    
    Works with both local .env files and deployed environment variables.
    """
    import os
    from dotenv import load_dotenv
    
    # Try to load from .env file first (local development)
    try:
        load_dotenv()
    except Exception:
        pass
        
    # Get API key from environment variable
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        st.error("YouTube API key not found. Please set the YOUTUBE_API_KEY environment variable in Streamlit Cloud.")
        st.markdown('''
        ### How to set up your API key in Streamlit Cloud:
        1. Go to your app settings in Streamlit Cloud
        2. Click on 'Secrets'
        3. Add a new secret with the key `YOUTUBE_API_KEY` and your API key as the value
        ''')
        st.stop()
    return api_key

def comments_extractor_ui():
    """Main function for the comments extractor UI."""
    st.markdown('<h2 class="sub-header">YouTube Comments Extractor</h2>', unsafe_allow_html=True)
    
    # Input for YouTube video URL
    video_url = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        max_comments = st.number_input("Maximum comments to fetch (leave at 0 for all)", 
                                       min_value=0, 
                                       value=0, 
                                       help="Set to 0 to fetch all comments")
    
    with col2:
        include_replies = st.checkbox("Include replies", value=True, 
                                     help="Include replies to comments")
    
    if video_url:
        # Extract video ID
        video_id = extract_video_id(video_url)
        
        if not video_id:
            st.error("Invalid YouTube video URL. Please enter a valid URL.")
            st.stop()
        
        # Create extract button
        extract_button = st.button("Extract Comments")
        
        if extract_button:
            with st.spinner("Initializing..."):
                # Get API key
                api_key = get_api_key()
                
                # Initialize YouTube API client
                youtube = build('youtube', 'v3', developerKey=api_key)
                
                # Get video details
                video_details = get_video_details(youtube, video_id)
                
                if not video_details:
                    st.error("Could not retrieve video details. The video might be private or unavailable.")
                    st.stop()
                
                # Display video information
                snippet = video_details["snippet"]
                statistics = video_details["statistics"]
                
                st.markdown("### Video Information")
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.image(snippet["thumbnails"]["high"]["url"], width=200)
                
                with col2:
                    st.markdown(f"**Title:** {snippet['title']}")
                    st.markdown(f"**Channel:** {snippet['channelTitle']}")
                    st.markdown(f"**Published:** {snippet['publishedAt'][:10]}")
                    st.markdown(f"**Views:** {int(statistics['viewCount']):,}")
                    
                    # Check if comments are disabled
                    if "commentCount" not in statistics:
                        st.error("Comments are disabled for this video.")
                        st.stop()
                    
                    st.markdown(f"**Comment Count:** {int(statistics['commentCount']):,}")
                
                # Determine how many comments to fetch
                comment_count = int(statistics.get("commentCount", 0))
                if max_comments == 0 or max_comments > comment_count:
                    max_comments = comment_count
                
                # Create a progress bar
                progress_bar = st.progress(0, "Preparing to fetch comments...")
                
                # Fetch comments
                with st.spinner(f"Fetching up to {max_comments:,} comments..."):
                    comments = get_comments(youtube, video_id, max_comments, progress_bar)
                
                # Filter out replies if not requested
                if not include_replies:
                    comments = [comment for comment in comments if not comment["isReply"]]
                
                # Display comment count
                st.success(f"Successfully fetched {len(comments):,} comments!")
                
                # Create download button
                if comments:
                    filename, csv_data = generate_csv_download_link(comments, snippet['title'])
                    
                    st.download_button(
                        label="Download Comments as CSV",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
                    # Display sample of comments
                    st.markdown("### Sample Comments")
                
                    # Convert to DataFrame for display
                    df = pd.DataFrame(comments)
                
                    # Select columns to display
                    display_columns = ["authorDisplayName", "textOriginal", "likeCount", "publishedAt", "isReply"]
                
                    # Rename columns for display
                    display_df = df[display_columns].copy()
                    display_df.columns = ["Author", "Comment", "Likes", "Published At", "Is Reply"]
                
                    # Show a sample of the comments
                    st.dataframe(display_df.head(10), use_container_width=True)
                
                    # Airtable integration removed
