# Spotify Telegram Bot

This is a Telegram bot that helps users interact with Spotify. The bot can authorize users, retrieve Spotify data, and store user information in a DynamoDB table.

## Features

- Authorize users with Spotify
- Retrieve Spotify data
- Store user information in DynamoDB

## Prerequisites

- Python 3.7+
- A Telegram bot token
- Spotify API credentials (Client ID and Client Secret)
- AWS credentials for DynamoDB

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/spotify-telegram-bot.git
    cd spotify-telegram-bot
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    ```bash
    export TELEGRAM_TOKEN=your_telegram_bot_token
    export SPOTIFY_CLIENT_ID=your_spotify_client_id
    export SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
    export AWS_ACCESS_KEY_ID=your_aws_access_key_id
    export AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
    ```

## Usage

1. Run the bot:
    ```bash
    python telegram_bot.py
    ```

2. Interact with the bot on Telegram:
    - `/help`: Get help information
    - `/id init <spotify_id>`: Initialize your Spotify ID

## Example

To initialize your Spotify ID, send the following command to the bot:
/id init your_spotify_id

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
