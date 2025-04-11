# 🤖 Aiogram Bot Template

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-2.21-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A comprehensive, feature-rich Telegram bot template built with the Aiogram framework. Perfect for quickly launching production-ready bots with advanced features.

## ✨ Features

### 👥 User Management
- **Automatic Registration**: New users are registered in the database on first interaction
- **User Profiles**: View and manage user information
- **Blocking System**: Administrators can block/unblock users
- **Exception Users**: Set users who can bypass subscription requirements

### 🛠️ Admin Panel
- **Complete Dashboard**: Statistics, user management, and settings in one place
- **Mass Messaging**: Send announcements to all users at once
- **User Search**: Find users by username or browse alphabetically
- **Data Export**: Export user data to Excel files for external analysis

### 📢 Channel Subscription
- **Mandatory Subscriptions**: Require users to subscribe to channels before using the bot
- **Multiple Channels**: Support for multiple subscription channels
- **Subscription Verification**: Automatic checking of subscription status
- **Toggle Channels**: Enable/disable subscription requirements per channel

### 🔗 Referral System
- **Personal Links**: Each user gets a unique referral link
- **Referral Tracking**: See who invited whom and when
- **Referral Statistics**: View top inviters and overall statistics
- **Instant Notifications**: Users get notified when their invite is used

### 🗃️ Database Integration
- **SQLAlchemy ORM**: Clean, object-oriented database access
- **SQLite by Default**: Works out of the box with minimal setup
- **Configurable**: Easily switch to MySQL, PostgreSQL, or other databases
- **Migration-Ready**: Structure supports future schema changes

### 🔄 Middleware Architecture
- **Separation of Concerns**: Clean, maintainable code structure
- **Request Processing**: Automated user registration and subscription checking
- **Error Handling**: Graceful error recovery
- **Extensible**: Easy to add new middleware components

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Admin Telegram ID (can be obtained from [@userinfobot](https://t.me/userinfobot))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/aiogram-bot-template.git
   cd aiogram-bot-template
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment variables**
   Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_bot_token_from_botfather
   ADMIN_IDS=your_telegram_id,another_admin_id
   DATABASE_URL=sqlite:///./database.db
   ```

5. **Run the bot**
   ```bash
   python src/bot.py
   ```

## 📁 Project Structure

```
src/
├── bot.py                 # Main entry point
├── config.py              # Configuration from .env file
├── handlers/              # Message handlers
│   ├── admin.py           # Admin commands and panel
│   └── user.py            # User commands
├── keyboards/             # Telegram keyboard layouts
│   ├── admin_kb.py        # Admin panel keyboards
│   └── user_kb.py         # User keyboards
├── middlewares/           # Request processing middleware
│   ├── logging.py         # Request logging
│   ├── subscription.py    # Channel subscription checks
│   └── user_registration.py # User registration
├── services/              # Business logic and database operations
│   ├── channel_service.py # Channel management
│   ├── database.py        # Database models and connection
│   └── user_service.py    # User management
└── utils/                 # Helper functions
    ├── admin_utils.py     # Admin utility functions
    ├── filters.py         # Custom message filters
    ├── misc.py            # Miscellaneous utilities
    └── subscription_utils.py # Subscription checking
```

## ⚙️ Configuration

### Environment Variables
- `BOT_TOKEN`: Your Telegram Bot API token
- `ADMIN_IDS`: Comma-separated list of admin Telegram IDs
- `DATABASE_URL`: SQLAlchemy database URL (defaults to SQLite)

### Custom Configuration
You can extend the configuration in `src/config.py` to add more settings.

## 🔧 Advanced Usage

### Adding New Commands

1. Open the appropriate handler file (`src/handlers/user.py` for user commands)
2. Add your command handler function:
   ```python
   async def my_command(message: types.Message):
       await message.answer("This is my custom command!")
   ```
3. Register the handler in the `register_user_handlers` function:
   ```python
   dp.register_message_handler(my_command, commands=["mycommand"])
   ```

### Creating Custom Keyboards
```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

my_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
my_keyboard.add(
    KeyboardButton("Button 1"), 
    KeyboardButton("Button 2")
)
```

### Adding Database Models
Extend the models in database.py:
```python
class MyNewModel(Base):
    __tablename__ = 'my_new_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

## 🔍 Troubleshooting

### Common Issues

- **Bot doesn't respond**: Check your `BOT_TOKEN` is correct and the bot is running
- **Admin commands don't work**: Ensure your Telegram ID is correctly added to `ADMIN_IDS`
- **Database errors**: Check your database connection string in .env
- **Bot can't verify subscriptions**: Make sure the bot is an admin in the channels

### Getting Help
If you encounter issues not covered here, please open an issue on GitHub.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ by Kamyshnikov Dmitrii