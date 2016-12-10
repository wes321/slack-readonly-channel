#!flask/bin/python

"""
    Slack Read-Only Channels

	Delete all messages inside a channel besides chosen admins
    This app.py file contains the endpoint you need from slack outgoing webhooks to automatically delete messages from anyone but the channel admins (configured by the Slack Read-Only Channel owner)
	
	Created By: Wesley Lorenzini
"""

from flask import Flask, request, Response, make_response, current_app
from datetime import timedelta
import requests

app = Flask(__name__)

# Configs
slack_base_url='https://slack.com/api/'

# Examples for required configs
#slack_token='xoxp-23423423'
#slack_message_token='H2343Ddgjd3g3frtr'
#readonly_channels_data={'channel-name':['allowed-to-post-user-name','another-user-name']}

slack_token=''
slack_message_token=''
readonly_channels_data={'':['']}

@app.route('/app/message_received', methods=['POST'])
def message_received():
	# This is what will come back from the slack outgoing webhook
	# token=XXXXXXXXXXXXXXXXXX
	# team_id=T0001
	# team_domain=example
	# channel_id=C2147483705
	# channel_name=test
	# timestamp=1355517523.000005
	# user_id=U2147483697
	# user_name=Steve
	# text=googlebot: What is the air-speed velocity of an unladen swallow?
	# trigger_word=googlebot:

	slack_message_auth_token=False
	message_timestamp=False
	user_name=False
	channel_name=False
	channel_id=False
	text=False
	# print request.form.items()
	for key, value in request.form.items():
		if(key == 'token'):
			slack_message_auth_token=value
		if(key == 'user_name'):
			user_name=value
		if(key == 'channel_name'):
			channel_name=value
		if(key == 'channel_id'):
			channel_id=value
		if(key == 'timestamp'):
			message_timestamp=value
		if(key == 'text'):
			text=value

	if slack_message_token == slack_message_auth_token:
		# This is the correct token from Slack Outgoing Webhook
		if channel_name in readonly_channels_data:
			# Is one of the defined read-only channels
			if user_name not in readonly_channels_data[channel_name]:
				# This user is not allowed to post so delete the message
				remove_slack_message(message_timestamp, channel_id)
				print '['+message_timestamp+'] '+user_name+"'s message deleted: "+text
			else:
				print '['+message_timestamp+'] '+user_name+"'s message allowed: "+text
	return 'success'

def remove_slack_message(message_timestamp, channel_id):
	dictToSend = {'token':slack_token, 'ts':message_timestamp, 'channel':channel_id}
	res = requests.get(slack_base_url+'chat.delete', params=dictToSend)
	dictFromServer = res.json()
	return dictFromServer

# If needed to build out more functionality for your project
def get_slack_channels():
	dictToSend = {'token':slack_token}
	res = requests.get(slack_base_url+'channels.list', params=dictToSend)
	dictFromServer = res.json()
	channels = dictFromServer['channels']
	return channels

def get_slack_members():
	dictToSend = {'token':slack_token}
	res = requests.get(slack_base_url+'users.list', params=dictToSend)
	dictFromServer = res.json()
	members = dictFromServer['members']
	return members
			
if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)