# Astronomibot
A little Twitch bot I've been working on


Setup:
-------
Create a file called "creds.txt" in the working directory where you're running Astronomibot.  
   * The first line of this file should be the username of your bot.  
   * The second line of the file should be the Twitch chat oauth key to log in as that user (NOT the password for the account!)
   * The third line of the file should be the client ID for the application
   * The fourth line should be the client secret for the application
   * Fifth line, access token, retrieved as per below:

Chat OAuth Key:
----------------
You can get your chat OAuth key for the second line of the creds file by going here:
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

    https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=<Application Client ID>&redirect_uri=http://localhost&scope=channel_editor channel_read user:edit:broadcast

Log in as the channel owner, and you'll be sent to an localhost address that will look like this, containing your access token:

    http://localhost/#access_token=<Access Token>&scope=channel_editor channel_read user:edit:broadcast

Grab the access token from the URL and enter it as the fifth line in your creds file.


Alternately, use the token generator available at https://twitchapps.com/tokengen making sure to request the following scopes: 

    channel_editor channel_read user:edit:broadcast

# Credentials for other Modules:

## FTP Website Uploading
Create a file called 'ftpcreds.txt' with four lines
   * The first line is the URL to connect to with FTP
   * The second line is the username to log in with
   * The third line is the password to log in
   * The fourth line is the folder to upload into

## Twitter tweets when Live
Create a file called 'twittercreds.txt' with four lines
   * The first line is your Twitter consumer key
   * The second line is your consumer secret
   * The third line is your access token
   * The fourth line is your access token secret

For information on obtaining those, read https://developer.twitter.com/en/docs/labs/filtered-stream/quick-start

## Discord message when Live
Create a file called 'discordcreds.txt' with 6 lines
   * The first line is your Discord Client ID
   * The second line is your Discord Client Secret
   * The third line is your Discord User Name (Including the distinguisher)
   * The fourth line is your Discord User ID
   * The fifth line is your Discord Access Token
   * The sixth line is the channel ID where you want the notifications posted

## Game Voting Support
Create a Google Sheets document with a list of games.  It must have at least a column containing game names, and another column for the game status.
Next, create a file called 'gamevotecreds.txt' with 10 lines
   * The first line is your Google Sheets API Key
   * The second line is the sheet ID of the document you created
   * The third line is the name of the sheet containing regular games
   * The fourth line is the column letter containing the list of game names
   * The fifth line is the column letter containing the status of those games
   * The sixth line is the row number of the first game in the list
   * The seventh line is the name of the sheet containing the list of randomizer games
   * The eight line is the column letter containing the list of randomizer game names
   * The ninth line is the column letter containing the status of those randomizer games
   * The tenth line is the row number of the first randomizer name in the list


# Dependencies:
-------------
 * milight
 * webcolors
 * tweepy
 * requests
