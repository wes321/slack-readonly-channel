# Slack Readonly Channel
Delete all messages inside a slack channel besides chosen admins.

Created by:
Wesley Lorenzini
http://wltechnology.com

### Setup
1. Create a Slack app here https://api.slack.com/apps?new_app=1
2. Copy over the **client_id** and **client_secret** to the **app.py** file 
3. Determine your **slack_team_id** by clicking 'Test Method' here https://api.slack.com/methods/team.info/test. Copy **id** to **slack_team_id**
4. Choose the URL where you will host the app.py file and update that url in **app_base_url** as well as in the Slack App redirect url on the Slack App Page.
5. Add your *username* to **super_admin_usernames** so you can add/remove people
6. Open a web browser and head over to your **app_base_url**. It should ask you for permissions to your channel. It will display "Link Successful!" if your account with creds worked. 
 7. Add a Slack outgoing webhook https://slack.com/apps/A0F7VRG6Q-outgoing-webhooks
 8. Point the outgoing webhook to the channel you want to monitor
 9. Add the **app_base_url** along with **/message_received** appended to the outgoing webhook URL(s) (example **http://hostedhere.com/message_received**')
10. Open up the channel you added and try `add @username` to allow a user to write a message to this channel
11. To delete the user from being able to write a message try `remove @username`
	
License
----

MIT
