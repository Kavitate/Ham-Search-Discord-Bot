<h1 align="center">🐷 📻 Ham Search Discord Bot 📻 🐷</h1>
This Discord bot utilizes the API from https://callook.info/ to pull callsign information.

The bot also logs all command searches, but can be removed if logging is not needed.

<p float="left">
  <img align="center" src="https://i.imgur.com/8lfM2jb.png" width="350" height="400"/>
  <img align="right" src="https://i.imgur.com/kmnkAhW.png" width="350" height="400"/>
</p>

## Variables
Prior to using the bot, the following variables must be updated in the `confog.json` file:
- Replace `YOUR_DISCORD_BOT_TOKEN_HERE` with your Discord bot token.
- Replace `YOUR_DISCORD_SERVER_ID` with the Discord server ID you want the bot to be in.

## Commands
Once the above variables have been updated, run the bot using the following command:
- `/ham` followed by a callsign to get information about the callsign.
- `/logbook` followed by a callsign to view QSOs and confirmations from QRZ.
- `/distance` followed by two callsigns to calculate the distance between both.
- `/conditions` to view the latest band conditions.

Note: The `/ham` and `/distance` commands will only function if the callsigns are located within the U.S

This is because there is no "global callsign database" to pull callsign data from.
