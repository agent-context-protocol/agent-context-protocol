import shutil
import sqlite3
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from geopy.geocoders import Nominatim

# Function to fetch search history
def fetch_search_history(original_path, limit=5):
    copy_path = original_path + "_copy.db"
    
    # Copy the database file
    shutil.copyfile(original_path, copy_path)

    # Connect to the copied database file
    conn = sqlite3.connect(copy_path)
    c = conn.cursor()

    # Query to fetch search history
    query = '''
    SELECT url, title, visit_count, last_visit_time
    FROM urls
    WHERE url LIKE '%google.com/search?q=%'
    ORDER BY last_visit_time DESC
    LIMIT ?
    '''
    c.execute(query, (limit,))
    rows = c.fetchall()

    # Extract search queries from the results
    search_history = []
    for row in rows:
        url = row[0]
        
        # Parse the URL to extract the search query
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        search_query = query_params.get('q', [''])[0]  # Default to empty string if 'q' not found
        
        search_history.append(search_query)
    
    # Close the connection and remove the copied database file
    conn.close()
    os.remove(copy_path)

    return search_history

# Function to extract bookmarks
def extract_bookmarks(bookmarks_path):
    # Read the Bookmarks file
    with open(bookmarks_path, 'r') as file:
        data = json.load(file)

    # Function to recursively extract bookmarks
    def extract_bookmarks_recursive(bookmark_node, results):
        if 'children' in bookmark_node:
            for child in bookmark_node['children']:
                extract_bookmarks_recursive(child, results)
        elif 'url' in bookmark_node:
            results.append({
                'name': bookmark_node['name'],
                'url': bookmark_node['url']
            })

    # Extract bookmarks
    bookmarks = []
    extract_bookmarks_recursive(data['roots']['bookmark_bar'], bookmarks)
    extract_bookmarks_recursive(data['roots']['other'], bookmarks)
    extract_bookmarks_recursive(data['roots']['synced'], bookmarks)

    return bookmarks

# Function to retrieve calendar events
def get_calendar_events(credentials_path, token_path, max_results=10):
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=max_results, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    calendar_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        calendar_events.append({
            "start": start,
            "summary": event['summary']
        })

    return calendar_events

# Function to get the current location
def get_current_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        
        location = {
            'city': data.get('city'),
            'region': data.get('region'),
            'country': data.get('country'),
            'latitude': data.get('loc', ',').split(',')[0],
            'longitude': data.get('loc', ',').split(',')[1]
        }
        return location
    except Exception as e:
        print(f"Error getting location: {str(e)}")
        return None

def get_location_name(latitude, longitude, city):
    try:
        geolocator = Nominatim(user_agent="myapp")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        
        # Split the address into parts
        address_parts = location.address.split(', ')
        
        # Find the index of the city in the address parts
        city_index = next((i for i, part in enumerate(address_parts) if city.lower() in part.lower()), None)
        
        if city_index is not None:
            # Join all parts before the city
            return ', '.join(address_parts[:city_index])
        else:
            return location.address
    except Exception as e:
        print(f"Error getting location name: {str(e)}")
        return None