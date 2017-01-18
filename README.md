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

Chat OAuth Key:
----------------
You can get your chat OAuth key fro the second line of the creds file by going here:
https://twitchapps.com/tmi/

Note: Log in as the account that your bot will speak through!

Getting your client ID and client secret:
-------------------------------------------
Go here and click "Register your application" at the bottom of the page:
https://www.twitch.tv/settings/connections

Enter an application name that seems reasonable (Eg. "Astronomibot")
Enter "http://localhost" for the Redirect URI
Select "Chat bot" for the Application Category

Accept the terms and conditions, then hit Register.

You'll be brought to a page to manage your new application.  Near the bottom, you'll see a box that is labelled "Client ID".
This is the client ID that will go into the third line of the creds file.

Below that, you'll see a button that says "New Secret" underneath a label saying Client Secret.  Click that and you'll be given
a client secret that you can enter into the fourth line of the creds file.


Access Token:
---------------
Navigate to:

https://api.twitch.tv/kraken/oauth2/authorize?response_type=token&client_id=<Application Client ID>&redirect_uri=http://localhost&scope=channel_editor channel_read

Log in as the channel owner, and you'll be sent to an localhost address that will look like this, containing your access token:

http://localhost/#access_token=<Access Token>&scope=channel_editor

Grab the access token from the URL and enter it as the fifth line in your creds file.

Dependencies:
-------------
 * milight
 * webcolors
