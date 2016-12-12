#!flask/bin/python

"""
    Slack Read-Only Channels

	Delete all messages inside a channel besides chosen admins
    This app.py file contains the endpoint you need from slack outgoing webhooks to automatically delete messages from anyone but the channel admins

    Note: You must be an admin of your Slack team since it requires delete message permissions

	App Setup
	1. Run pip install Flask requests TinyDB
	2. Run python app.py

 	Slack Setup
 	1. Create a Slack App
 	2. Copy over the client_id and client_secret below
 	3. Determine your 'slack_team_id' by clicking 'Test Method' here https://api.slack.com/methods/team.info/test. Copy id to slack_team_id
 	4. Choose the URL where you will host this and update it in app_base_url as well as in the Slack App redirect url on the Slack App Page
 	5. Add your username to super_admin_usernames so you can add/remove people
 	6. Head over to your app_base_url. It should ask you for permissions to your channel. It will display "Link Successful!" if your account with creds worked. 
 	7. Add a Slack outgoing webhook
 	8. Point the outgoing webhook to the channel you want to monitor
 	9. Add the app_base_url along with /message_received appended to the outgoing webhook URL(s) (example http://hostedhere.com/message_received')
	10. Open up the channel you added and try 'add @username' without quotes to allow a user to write a message to this channel
	11. To delete the user from being able to write a message try 'remove @username' without quotes
	
	Created By: 
	Wesley Lorenzini
	http://wltechnology.com
"""

from flask import Flask, request, Response, make_response, current_app, redirect
from datetime import timedelta
from tinydb import TinyDB, where, Query
from tinydb.operations import delete
import requests

app = Flask(__name__)

# TinyDB Setup
db = TinyDB('db.json')
# Make DB tables
configs = db.table('configs')
permissions = db.table('permissions')

# Configs
app_base_url='http://hostedhere.com' #This is where URL where you will host this code
slack_team_id='' #This is to prevent this app from being used for other teams but the one you choose
slack_client_id='' #This if your Slack App Client Id
slack_client_secret='' #This is your Slack App Client Secret
super_admin_usernames=['username'] #This user can add / remove channels and users who can post to read-only channels

# Do not edit
slack_base_url='https://slack.com/api/'
slack_scope='chat:write:bot,chat:write:user,channels:read,users:read'
slack_redirect_uri='/oauth_redirect' # Where the slack app goes after its authorized


# Routes
@app.route('/message_received', methods=['POST'])
def message_received():
	message_timestamp=False
	user_name=False
	user_id=False
	channel_name=False
	channel_id=False
	text=False
	# print request.form.items()
	for key, value in request.form.items():
		if(key == 'token'):
			slack_message_auth_token=value
		if(key == 'user_name'):
			user_name=value
		if(key == 'user_id'):
			user_id=value
		if(key == 'channel_name'):
			channel_name=value
		if(key == 'channel_id'):
			channel_id=value
		if(key == 'timestamp'):
			message_timestamp=value
		if(key == 'text'):
			text=value

	# This is the correct token from Slack Outgoing Webhook
	if admin_for_channel(channel_name, user_id) or user_name in super_admin_usernames:
		print '['+message_timestamp+'] '+user_name+"'s message allowed: "+text
	else:
		remove_slack_message(user_id, message_timestamp, channel_id)
		print '['+message_timestamp+'] '+user_name+"'s message deleted: "+text

	# Do check if super admins are trying to add / remove users
	if user_name in super_admin_usernames:
		if "add <@" in text:
			split_1 = text.split('<@')
			if len(split_1) > 1:
				split_2 = split_1[1].split('>')
				add_user_id = split_2[0]
				send_slack_message(user_id, username_for_user_id(add_user_id)+' added to '+channel_name)
				add_admin_for_channel(channel_name, add_user_id)
				remove_slack_message(user_id, message_timestamp, channel_id)

		if "remove <@" in text:
			split_1 = text.split('<@')
			if len(split_1) > 1:
				split_2 = split_1[1].split('>')
				remove_user_id = split_2[0]
				send_slack_message(user_id, username_for_user_id(remove_user_id)+' removed from '+channel_name)
				remove_admin_for_channel(channel_name, remove_user_id)
				remove_slack_message(user_id, message_timestamp, channel_id)

	return 'success'

@app.route('/', methods=['GET'])
def auth():
	return redirect("https://slack.com/oauth/authorize?client_id="+slack_client_id+'&scope='+slack_scope+'&redirect_uri='+app_base_url+slack_redirect_uri+"&team="+slack_team_id, code=302)

@app.route(slack_redirect_uri, methods=['GET'])
def oauth_redirect():
	slack_code=None
	if request.args.get('code'):
		slack_code=request.args.get('code')

	dictToSend = {'client_id':slack_client_id, 'client_secret':slack_client_secret, 'code':slack_code, 'redirect_uri': app_base_url+slack_redirect_uri}
	res = requests.get(slack_base_url+'oauth.access', params=dictToSend)
	dictFromServer = res.json()
	if dictFromServer['ok']:
		set_access_token(dictFromServer['access_token'])
		for sadmin in super_admin_usernames:
			send_slack_message(user_id_for_username(sadmin), 'Linked by user')
		return 'Link Successful!'
	else:
		print 'ERROR'
		print dictFromServer
		return 'Link Failed! Please check your logs.'	


# Message Removal
def remove_slack_message(user_id, message_timestamp, channel_id):
	dictToSend = {'token':get_access_token(), 'ts':message_timestamp, 'channel':channel_id}
	res = requests.get(slack_base_url+'chat.delete', params=dictToSend)
	dictFromServer = res.json()
	if 'error' in dictFromServer:
		print 'Slack API Error'
		error = dictFromServer['error']
		print error
		if error == 'not_authed':
			print 'Please authenticate this again at '+app_base_url
	return dictFromServer

# Message User 
def send_slack_message(user_id, message):
	dictToSend = {'token':get_access_token(), 'text':message, 'channel':user_id}
	res = requests.get(slack_base_url+'chat.postMessage', params=dictToSend)
	dictFromServer = res.json()
	print dictFromServer
	return dictFromServer

# Get Username from User's ID
def username_for_user_id(user_id):
	members = get_slack_members()
	for member in members:
		if member['id'] == user_id:
			return member['name']
	return None

# Get User Id from username
def user_id_for_username(username):
	members = get_slack_members()
	for member in members:
		if member['name'] == username:
			return member['id']
	return None

# TinyDB Functions
def set_access_token(access_token):
	configs.remove(where('name') == 'access_token')
	configs.insert({'name':'access_token', 'access_token': access_token})

def get_access_token():
	db_query = Query()
	query_response = configs.search(db_query.name == 'access_token')
	access_token = None
	if len(query_response) > 0:
		if 'access_token' in query_response[0]:
			access_token = query_response[0]['access_token']
	return access_token

def add_admin_for_channel(channel, user_id):
	db_query = Query()
	results = permissions.search((db_query.channel == channel) & (db_query.user_id == user_id))
	if len(results) == 0:
		permissions.insert({'channel':channel, 'user_id': user_id, 'username': username_for_user_id(user_id)})

def remove_admin_for_channel(channel, user_id):
	db_query = Query()
	results = permissions.search((db_query.channel == channel) & (db_query.user_id == user_id))
	if len(results) > 0:
		permissions.remove((db_query.channel == channel) & (db_query.user_id == user_id))

def admin_for_channel(channel, user_id):
	db_query = Query()
	results = permissions.search((db_query.channel == channel) & (db_query.user_id == user_id))
	if len(results) == 0:
		return False
	else: 
		return True


# If needed to build out more functionality for your project
def get_slack_channels():
	dictToSend = {'token':get_access_token()}
	res = requests.get(slack_base_url+'channels.list', params=dictToSend)
	dictFromServer = res.json()
	channels = dictFromServer['channels']
	return channels

def get_slack_members():
	dictToSend = {'token':get_access_token()}
	res = requests.get(slack_base_url+'users.list', params=dictToSend)
	dictFromServer = res.json()
	members = dictFromServer['members']
	return members

		
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)