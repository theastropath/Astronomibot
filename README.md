# Astronomibot
A little Twitch bot I've been working on


Setup:
-------
Run astronomibot.py one time, providing your channel name as an argument, eg:

    astronomibot.py theastropath

Which will generate a new blank config file at ./config/<channel name>/config.ini

Open that file and start filling in the fields as follows...

[Chat] Section:
----------------

"chatnick" is the username that your bot will use

You can get your chat OAuth key for "chatpassword by going here:
https://twitchapps.com/tmi/

Note: Log in as the account that your bot will speak through!

"channel" is the chat channel your bot will run in (It should start with a # and be lowercase).  Eg: #theastropath


[TwitchAPI] Section:
-------------------------------------------
Go here and click "Register your application" at the bottom of the page:
https://www.twitch.tv/settings/connections

Enter an application name that seems reasonable (Eg. "Astronomibot")
Enter "http://localhost" for the Redirect URI
Select "Chat bot" for the Application Category

Accept the terms and conditions, then hit Register.

You'll be brought to a page to manage your new application.  Near the bottom, you'll see a box that is labelled "Client ID".
This is the client ID that will go into the "clientid" field.

Below that, you'll see a button that says "New Secret" underneath a label saying Client Secret.  Click that and you'll be given
a client secret that you can enter into the "clientsecret" field.

Navigate to:

    https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=<Application Client ID>&redirect_uri=http://localhost&scope=channel_editor channel_read user:edit:broadcast bits:read channel:read:redemption channel_subscriptions

Log in as the channel owner, and you'll be sent to an localhost address that will look like this, containing your access token:

    http://localhost/#access_token=<Access Token>&scope=channel_editor channel_read user:edit:broadcast bits:read channel:read:redemption channel_subscriptions

Grab the access token from the URL and enter it as the "accesstoken" field.


Alternately, use the token generator available at https://twitchapps.com/tokengen making sure to request the following scopes: 

    channel_editor channel_read user:edit:broadcast bits:read channel:read:redemption channel_subscriptions


# Credentials for other Modules:

## [FTP] Section (For website uploading)
   * "ftpurl" is the URL to connect to with FTP
   * "ftpuser" is the username to log in with
   * "ftppassword" is the password to log in
   * "ftpdir" is the folder to upload into (relative to the base FTP directory)

## [Twitter] Section (Twitter tweets when Live)
   * "consumerkey" is your Twitter consumer key
   * "consumersecret" is your consumer secret
   * "accesstoken" is your access token
   * "accesstokensecret" is your access token secret

For information on obtaining those, read https://developer.twitter.com/en/docs/labs/filtered-stream/quick-start

## [Discord] Section (Discord message when Live)
   * "clientid" is your Discord Client ID
   * "clientsecret" is your Discord Client Secret
   * "username" is the Discord User Name for your bot (Including the distinguisher)
   * "userid" is the Discord User ID of your bot
   * "accesstoken" is your Discord Access Token
   * "channelid" is the channel ID where you want the notifications posted

## Game Voting Support
Create a Google Sheets document with a list of games.  It must have at least a column containing game names, and another column for the game status.

## [GameVote] Section
   * "googledocapikey" is your Google Sheets API Key
   * "googlesheetid" is the sheet ID of the document you created

To add tables that you can vote for games in, you can create as many of the following sections (with unique keywords) as you want

## [GameVoteTable&lt;keyword>] Section (Voting for games)
   * "sheetname" is the name of the sheet containing regular games
   * "gamenamecolumn" is the column letter containing the list of game names
   * "gamestatuscolumn" is the column letter containing the status of those games
   * "firstgamerow" is the row number of the first game in the list
    
The &lt;keyword> can be anything, and the new command will be !&lt;keyword>vote




# Dependencies:
-------------
 * milight (for MiLight module)
 * webcolors (for MiLight module)
 * tweepy (for LiveNotifications module)
 * markovify (for Speak module)
 * requests
 * urlextract
 * websocket-client
