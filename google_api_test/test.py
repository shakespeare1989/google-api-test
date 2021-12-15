import json
import os
import flask
from flask.json import jsonify
import requests
from sheets import sheets
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build
# from get_clean_message_data import extract_data


import datetime

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ["https://www.googleapis.com/auth/admin.directory.group.readonly https://mail.google.com/ https://www.googleapis.com/auth/admin.reports.usage.readonly https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/contacts.readonly https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/script.external_request https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/admin.directory.user https://www.googleapis.com/auth/admin.directory.group https://www.googleapis.com/auth/admin.directory.user.readonly openid https://www.googleapis.com/auth/admin.reports.audit.readonly https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/script.scriptapp https://www.googleapis.com/auth/userinfo.email"]
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = 'REPLACE ME - this value is here as a placeholder.'


@app.route('/')
def index():
  return print_index_table()


@app.route('/test')
def test_api_request():
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  files = drive.files().list().execute()

  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.jsonify(**files)

@app.route('/googleapis.com/drive/v3/changes', methods=['GET'])
def test_changes():

  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  # Load credentials from the session.
  credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

  drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  
  # Save credentials back to session in case access token was refreshed.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  flask.session['credentials'] = credentials_to_dict(credentials)

  files = drive.files().list().execute()

  return flask.jsonify(**files)




@app.route('/admin.googleapis.com/admin/reports/v1/activity/users/all/applications/meet?eventName=abuse_report_submitted&maxResults=10&access_token=<credentials>', methods=['GET'])
def get_reports(credentials):
  if 'credentials' not in flask.session:
    return flask.redirect('authorize')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  meet = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

  return flask.jsonify(get_reports(credentials))

@app.route('/googleapis.com/auth/directory.readonly', methods=['GET'])
def get_people():
    if 'credentials' not in flask.session:
      return flask.redirect('authorize')

  # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

    drive = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

    service = build('people', 'v1', credentials=credentials)

    # Call the People API
    print('List 10 connection names')
    results = service.people().connections().list(
      resourceName='people/me',
      pageSize=10,
      personFields='names,emailAddresses').execute()
    connections = results.get('connections', [])

    for person in connections:
      names = person.get('names', [])
      if names:
          name = names[0].get('displayName')
          return jsonify(connections)
    return jsonify(connections)

@app.route('/calendar')
def test_calendar():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

  # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])

    service = build('calendar', 'v3', credentials=credentials)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    return flask.jsonify(events)

@app.route('/gmail-labels')
def test_labels():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

  # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])
    service2 = build('gmail', 'v1', credentials=credentials)

    # Call the Gmail API
    pageToken = None
    history_id = "some recent history id"

    history = service2.users().history().list(userId="me", historyTypes='messageAdded',
                                             startHistoryId=history_id, pageToken=pageToken).execute()

    if history:
        current_history_id = history_id
        last_history_id = history.get('historyId')
        if last_history_id > current_history_id:
            for change in history:
                email_id = change['messagesAdded'][0]['message']['id']
                thread_id = change['messagesAdded'][0]['message']['threadId']
                import_me = 'INBOX' or 'SENT' in change.get('messagesAdded')[0].get('message').get('labelIds')
                if import_me:
                    message = service.users().messages().get(userId="me", id=email_id, format='metadata').execute()
                    clean_message = extract_data(message)
                    return clean_message

@app.route('/calendar-event')
def test_history():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

  # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
      **flask.session['credentials'])
    service = build('calendar', 'v3', credentials=credentials)

    event = {
    'summary': 'Google I/O 2015',
    'location': '800 Howard St., San Francisco, CA 94103',
    'description': 'A chance to hear more about Google\'s developer products.',
    'start': {
        'dateTime': '2021-11-28T09:00:00-07:00',
        'timeZone': 'America/Los_Angeles',
    },
    'end': {
        'dateTime': '2021-11-28T17:00:00-07:10',
        'timeZone': 'America/Los_Angeles',
    },
    'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=2'
    ],
    'attendees': [
        {'email': 'autumn@devpipeline.com'},
        {'email': 'autumn.e.gehring@gmail.com'},
    ],
    
    'reminders': {
        'useDefault': False,
        'overrides': [
        {'method': 'email', 'minutes': 24 * 60},
        {'method': 'popup', 'minutes': 10},
        ],
    },
    }

    event = service.events().insert(calendarId='primary', sendNotifications=True, body=event).execute()
    return flask.jsonify ('Created Event')




@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  # The URI created here must exactly match one of the authorized redirect URIs
  # for the OAuth 2.0 client, which you configured in the API Console. If this
  # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
  # error.
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  flask.session['state'] = state

  return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = flask.session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = flask.request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  flask.session['credentials'] = credentials_to_dict(credentials)

  return flask.redirect(flask.url_for('index'))


@app.route('/revoke')
def revoke():
  if 'credentials' not in flask.session:
    return ('You need to <a href="/authorize">authorize</a> before ' +
            'testing the code to revoke credentials.')

  credentials = google.oauth2.credentials.Credentials(
    **flask.session['credentials'])

  revoke = requests.post('https://oauth2.googleapis.com/revoke',
      params={'token': credentials.token},
      headers = {'content-type': 'application/x-www-form-urlencoded'})

  status_code = getattr(revoke, 'status_code')
  if status_code == 200:
    return('Credentials successfully revoked.' + print_index_table())
  else:
    return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
  if 'credentials' in flask.session:
    del flask.session['credentials']
  return ('Credentials have been cleared.<br><br>' +
          print_index_table())

# @app.route('/sheets')
# def sheets():
#     if 'credentials' not in flask.session:
#         return flask.redirect('authorize')
#       return



def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

def print_index_table():
  return ('<table>' +
  '<tr><td><a href="/authorize">Create Authorization</a></td>' +
          
        '<tr><td><a href="/test">Get Google Drive Data</a></td>' +
        '<tr><td><a href="/calendar">Get Calendar Data From an API request</a></td>' +
        '<tr><td><a href="/gmail-labels">Get Gmail Label Data From an API request</a></td>' +
        '<tr><td><a href="/googleapis.com//auth/directory.readonly">Get Organization Directory</a></td>' +
        '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
        '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
        '</td></tr></table>')


if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification.
  # ACTION ITEM for developers:
  #     When running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  # Specify a hostname and port that are set as a valid redirect URI
  # for your API project in the Google API Console.
  app.run('localhost', 8080, debug=True)