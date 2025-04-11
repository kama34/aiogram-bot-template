# aiogram-bot-template

This is a Telegram bot template built using the Aiogram framework. It features an admin panel for user management, a database for storing user data, and a clean, structured codebase that adheres to best practices.

## Features

- **Admin Panel**: Manage users, view statistics, and perform administrative tasks.
- **User Management**: Handle user registration, referral links, and subscription checks.
- **Database Integration**: Uses SQLite with SQLAlchemy for data storage.
- **Logging Middleware**: Logs user actions and bot events for better insights.
- **Custom Keyboards**: Provides inline and reply keyboards for enhanced user interaction.

## Project Structure

```
aiogram-bot-template
├── src
│   ├── bot.py                # Entry point of the bot
│   ├── config.py             # Configuration settings
│   ├── handlers               # Contains admin and user handlers
│   │   ├── admin.py          # Admin functionalities
│   │   └── user.py           # User functionalities
│   ├── middlewares            # Middleware for logging
│   │   └── logging.py        # Logging middleware
│   ├── services               # Services for database and user management
│   │   ├── database.py       # Database connection and models
│   │   └── user_service.py    # User management logic
│   ├── keyboards              # Keyboards for user interaction
│   │   ├── admin_kb.py       # Admin panel keyboards
│   │   └── user_kb.py        # User interaction keyboards
│   └── utils                 # Utility functions and filters
│       ├── misc.py           # Miscellaneous utility functions
│       └── filters.py        # Custom filters for message handling
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd aiogram-bot-template
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your bot token and database URL:
   ```
   BOT_TOKEN=<your_bot_token>
   DATABASE_URL=sqlite:///./database.db
   ```

## Usage

To run the bot, execute the following command:
```
python src/bot.py
```

## Contributing

Feel free to submit issues or pull requests to improve the bot. Contributions are welcome!

## License

This project is licensed under the MIT License. See the LICENSE file for details.