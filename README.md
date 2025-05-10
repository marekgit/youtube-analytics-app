# YouTube Analytics App

A Streamlit application that allows users to analyze YouTube channel statistics by simply entering a channel URL.

## Features

### Channel Analytics
- Input a YouTube channel URL
- View channel statistics (subscriber count, view count, video count)
- Display channel information (title, description, country, etc.)

### Comment Extractor
- Extract comments from any YouTube video
- Download comments as CSV file
- Upload comments to Airtable for further analysis
- View comment statistics and samples

- Simple and intuitive user interface with sidebar navigation

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your API keys:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   
   # Optional: For Airtable integration
   AIRTABLE_API_KEY=your_airtable_api_key_here
   AIRTABLE_BASE_ID=your_airtable_base_id_here
   AIRTABLE_TABLE_NAME=your_airtable_table_name_here
   ```
4. Run the application:
   ```
   streamlit run app.py
   ```

## Getting a YouTube API Key

1. Go to the [Google Developers Console](https://console.developers.google.com/)
2. Create a new project
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Copy the API key to your `.env` file

## Requirements

- Python 3.7+
- Streamlit
- Google API Python Client
- Python-dotenv
- Validators

## Deployment

### Deploying to Streamlit Cloud

Streamlit Cloud is the recommended platform for deploying Streamlit applications:

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Sign in with your GitHub account
4. Click "New app"
5. Select your repository, branch, and the main file (app.py)
6. Add your YouTube API key as a secret in the "Advanced settings" section:
   - Key: YOUTUBE_API_KEY
   - Value: your_api_key_here
7. Click "Deploy"

### Alternative Deployment Options

You can also deploy this application to other platforms that support Python applications:

- **Heroku**: Use a Procfile with `web: streamlit run app.py --server.port=$PORT`
- **Render**: Create a new Web Service with the build command `pip install -r requirements.txt` and start command `streamlit run app.py`
- **AWS/GCP/Azure**: Deploy using containerization (Docker) for the best experience
