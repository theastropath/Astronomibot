# Astronomibot
A little Twitch bot I've been working on


Setup:
-------
Create a file called "creds.txt" in the working directory where you're running Astronomibot.  
The first line of this file should be the username of your bot.  
The second line of the file should be the Twitch chat oauth key to log in as that user (NOT the password for the account!)
The third line of the file should be the client ID for the application
The fourth line should be the client secret for the application
Fifth line, access token, retrieved as per below:

Access Token:
---------------
Navigate to:
https://api.twitch.tv/kraken/oauth2/authorize?response_type=token&client_id=<Application Client ID>&redirect_uri=localhost&scope=channel_editor
Log in, and you'll be sent to an localhost address that will look like this, containing your access token:
http://localhost/#access_token=<Access Token>&scope=channel_editor
