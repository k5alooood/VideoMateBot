
# VideoMateBot

This is a Telegram bot designed to download videos from platforms such as YouTube, TikTok, Instagram, and more, and convert them into MP3 format.

## Features
- Download videos from multiple platforms.
- Convert videos to MP3 format.
- Download videos larger than 50MB by uploading them to GoFile.

## Setup Instructions
1. Clone or download the repository.
2. Install the required libraries:
   ```bash
   pip install aiogram yt-dlp aiohttp
   ```
3. Replace the `API_TOKEN` in `VideoMateBot.py` with your own bot token obtained from [BotFather](https://core.telegram.org/bots#botfather).
4. Run the script:
   ```bash
   python VideoMateBot.py
   ```

## Usage
- Use `/start` to start the bot.
- Use `/history` to check your download history.
