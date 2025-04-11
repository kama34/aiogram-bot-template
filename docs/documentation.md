# Aiogram Bot Template Documentation

## Table of Contents

1. README
2. Installation Guide
3. User Guide
4. Admin Guide
5. Architecture Documentation
6. API Documentation
7. Development Guide

## README

# Aiogram Bot Template

A comprehensive, feature-rich Telegram bot template built with aiogram, featuring user management, admin panel, subscription verification, and referral system.

## Features

- **User Management**: Registration, profiles, and blocking capability
- **Admin Panel**: Complete control over users, statistics, and messaging
- **Channel Subscription**: Force users to subscribe to channels before using the bot
- **Referral System**: Track user invitations with personalized referral links
- **Database Integration**: SQLAlchemy ORM with SQLite (configurable)
- **Middleware Architecture**: Clean separation of concerns

## Quick Start

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a .env file with your bot token and admin IDs
4. Run the bot: `python src/bot.py`

## Project Structure

```
src/
├── bot.py                 # Main entry point
├── config.py              # Configuration
├── handlers/              # Message handlers
│   ├── admin.py           # Admin commands
│   └── user.py            # User commands
├── keyboards/             # Telegram keyboard layouts
├── middlewares/           # Request processing middleware
├── services/              # Database and business logic
└── utils/                 # Helper functions
```

## License

MIT License

---

## Installation Guide

# Installation and Setup Guide

## Prerequisites

- Python 3.7+
- Telegram Bot Token (obtain from [@BotFather](https://t.me/BotFather))

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/aiogram-bot-template.git
cd aiogram-bot-template
```

## Step 2: Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create a .env file in the project root:

```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite:///./database.db
```

Replace:
- `your_bot_token_here` with your actual Telegram bot token
- `123456789,987654321` with comma-separated admin user IDs

## Step 5: Initialize Database

The database will be automatically created on first run.

## Step 6: Run the Bot

```bash
cd src
python bot.py
```

## Deployment Options

### Systemd Service (Linux)

Create `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=username
WorkingDirectory=/path/to/aiogram-bot-template
ExecStart=/path/to/aiogram-bot-template/venv/bin/python src/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

### Docker

A Dockerfile is provided for containerized deployment:

```bash
docker build -t telegram-bot .
docker run -d --name telegram-bot telegram-bot
```

---

## User Guide

# User Guide

This document explains how to use the Telegram bot as a regular user.

## Getting Started

1. **Start the bot**: Send `/start` to initiate conversation
2. **Navigate using keyboard buttons**: Use the custom keyboard to access features

## Available Commands

- `/start` - Start the bot and register your account
- `/help` - Get information about bot usage
- `/profile` - View your profile information
- `/referral` or `/ref` - Get your referral link
- `/myreferrals` or `/myref` - View users you've invited

## Main Menu

After starting the bot, you'll see these main menu buttons:

- **🔍 Profile**: View your account information
- **ℹ️ Help**: Get assistance and information
- **🔗 Referral Link**: Get a link to invite friends
- **👥 My Referrals**: See who you've invited

## Profile Section

The profile section shows:

- Your user ID
- Username and full name
- Registration date
- Number of invited users
- Who invited you (if applicable)

## Referral System

### Getting Your Referral Link
1. Press "🔗 Referral Link" button or use `/referral`
2. You'll receive a unique invitation link
3. Share this link with friends

### Tracking Referrals
1. Press "👥 My Referrals" button or use `/myreferrals`
2. View a list of users who joined via your link

## Channel Subscription

If the bot requires subscription to certain channels:

1. You'll see a message listing required channels
2. Use the provided buttons to open these channels
3. Subscribe to each channel
4. Click "🔄 Check Subscription" to verify
5. Once verified, you'll gain access to bot features

## Help and Support

For assistance, press the "ℹ️ Help" button or send `/help` to get information about commands and functionality.

---

## Admin Guide

# Administrator Guide

This guide details the administrative features available to users with admin privileges.

## Accessing Admin Panel

- Send `/admin` command
- Or press "🔧 Admin Panel" button (available only to admins)

## Admin Panel Features

### User Management

- **📊 Statistics**: View total users, blocked users, and new registrations
- **📁 Export**: Download Excel file with all user data
- **🔍 Users**: Find users by username or browse alphabetically
- **📨 Mass Message**: Send announcements to all users

### User Search

Two search methods are available:
1. **Text Search**: Find by username or user ID
2. **Alphabetical Search**: Browse users by first letter

#### User Actions
For any user, you can:
- Block/unblock users
- Set exceptions (users who bypass subscription checks)
- View their referral information

### Channel Management

Access via "📢 Channels" button to:
- View all subscription channels
- Add new channels (bot must be admin in channel)
- Enable/disable channels
- Delete channels

### Referral System Management

- **👥 Referral Stats**: View overall referral statistics
- **🔗 Admin Referral Link**: Generate your admin referral link
- **Top Referrers**: See which users have invited the most others

### Mass Messaging

Send announcements to all users:
1. Click "📨 Mass Message" from admin panel
2. Type your message
3. Confirm to send to all users
4. View delivery statistics

## Adding Channels for Subscription

1. Click "📢 Channels" in admin panel
2. Select "➕ Add Channel"
3. Enter the channel ID or username
   - Format: `-100123456789` or `@channelname`
4. Ensure the bot is an admin in this channel
5. Confirm to add the channel

## Exporting User Data

1. Click "📁 Export" in admin panel
2. An Excel file will be generated with user information
3. Download the file for offline analysis

## Blocking Users

Two methods:
1. Via user search: Find user and click "Block"
2. Direct command: `/block username`

Blocked users:
- Cannot access bot features
- See a block message when attempting to use the bot
- Can still access help button for support

---

## Architecture Documentation

# Architecture Documentation

## Overview

This bot uses the aiogram framework with a layered architecture that separates concerns between handlers, services, middlewares, and utilities.

## System Components

![Architecture Diagram](https://i.imgur.com/ZPSW1q0.png)

### Core Components

1. **Bot Initialization** (`bot.py`)
   - Entry point for the application
   - Sets up the bot, dispatcher, and middlewares
   - Registers all handlers

2. **Configuration** (`config.py`)
   - Loads environment variables
   - Provides global configuration to all components

3. **Database Layer** (`services/database.py`)
   - SQLAlchemy models for Users, Channels, and Referrals
   - Connection management

### Execution Flow

1. Telegram sends update to bot
2. Middlewares process the update:
   - `UserRegistrationMiddleware`: Registers new users
   - `UserMiddleware`: Checks if users are blocked
   - `SubscriptionMiddleware`: Verifies channel subscriptions
3. Appropriate handler processes the command/message
4. Services interact with database as needed
5. Response is sent back to user

## Database Schema

### Users Table
- `id` (PK): Telegram user ID
- `username`: Telegram username
- `full_name`: User's full name
- `is_blocked`: Whether user is blocked
- `is_exception`: Whether user bypasses subscription checks
- `created_at`: Registration timestamp

### Referrals Table
- `id` (PK): Unique record ID
- `user_id`: User who joined
- `referred_by`: User who invited them
- `created_at`: Creation timestamp

### Channels Table
- `id` (PK): Unique record ID
- `channel_name`: Display name of the channel
- `channel_id`: Telegram channel ID
- `is_enabled`: Whether subscription is required
- `added_at`: When channel was added

## Middleware Architecture

### UserRegistrationMiddleware
Automatically registers new users on any interaction

### UserMiddleware
Checks if users are blocked before processing messages

### SubscriptionMiddleware
Verifies users are subscribed to required channels

## Service Layer

### UserService
Handles user-related database operations

### ChannelService
Manages subscription channels

## Key Interactions

1. **User Registration Flow**:
   ```
   Telegram -> Middleware -> Database -> Response
   ```

2. **Subscription Check Flow**:
   ```
   User Request -> SubscriptionMiddleware -> check_user_subscriptions() -> 
   ChannelService -> Bot API -> User Response
   ```

3. **Admin Panel Flow**:
   ```
   Admin Request -> AdminFilter -> Admin Handlers -> 
   Database Operations -> Admin Response
   ```

## Security Model

- Admin access controlled by `ADMIN_IDS` environment variable
- Custom filters (`AdminFilter` and `AdminAccessFilter`) secure admin endpoints
- Blocked users can only access help functionality

---

## API Documentation

# API Documentation

## Bot API

### User-Facing Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `/start` | `ref_[user_id]` (optional) | Initializes bot and registers user. Optional referral parameter. |
| `/help` | None | Displays help information. |
| `/profile` | None | Shows user profile information. |
| `/referral` | None | Generates and displays referral link. |
| `/myreferrals` | None | Shows list of users invited by current user. |
| `/check_subscription` | None | Manually checks channel subscription status. |

### Admin Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `/admin` | None | Opens admin panel. |
| `/block` | `username` | Blocks specified user. |
| `/unblock` | `username` | Unblocks specified user. |

## Service Layer API

### UserService

| Method | Parameters | Return | Description |
|--------|------------|--------|-------------|
| `register_user()` | `username, full_name, user_id=None` | `User` | Registers new user or returns existing one. |
| `get_user_by_id()` | `user_id` | `User` | Retrieves user by ID. |
| `get_user_by_username()` | `username` | `User` | Retrieves user by username. |
| `update_user()` | `user_id, username=None, full_name=None` | `User` | Updates user information. |
| `delete_user()` | `user_id` | `bool` | Deletes user from database. |
| `check_subscription()` | `user_id` | `bool` | Checks if user exists. |
| `create_referral()` | `user_id, referred_by=None` | `Referral` | Creates referral record. |
| `get_referral_by_user_id()` | `user_id` | `Referral` | Gets referral info by user ID. |
| `get_user_referrals()` | `user_id` | `list` | Gets all users referred by given user. |
| `count_user_referrals()` | `user_id` | `int` | Counts how many users were referred by given user. |

### ChannelService

| Method | Parameters | Return | Description |
|--------|------------|--------|-------------|
| `add_channel()` | `channel_name, channel_id` | `Channel` | Adds new channel or returns existing one. |
| `get_channel_by_id()` | `channel_id` | `Channel` | Gets channel by Telegram ID. |
| `get_channel_by_id_db()` | `db_id` | `Channel` | Gets channel by database ID. |
| `get_all_channels()` | None | `List[Channel]` | Gets all channels. |
| `get_enabled_channels()` | None | `List[Channel]` | Gets only enabled channels. |
| `toggle_channel()` | `channel_id` | `Channel` | Toggles channel enabled status. |
| `toggle_channel_by_id()` | `db_id` | `Channel` | Toggles channel using database ID. |
| `delete_channel()` | `channel_id` | `bool` | Deletes channel by Telegram ID. |
| `delete_channel_by_id()` | `db_id` | `bool` | Deletes channel by database ID. |

## Utility Functions

### Subscription Utils

| Function | Parameters | Return | Description |
|----------|------------|--------|-------------|
| `check_user_subscriptions()` | `user_id` | `tuple(bool, list)` | Checks if user is subscribed to all required channels. Returns status and list of channels not subscribed to. |

### Admin Utils

| Function | Parameters | Return | Description |
|----------|------------|--------|-------------|
| `is_admin()` | `user_id` | `bool` | Checks if user is an admin. |

## Callback Query Handlers

| Callback Data | Description |
|---------------|-------------|
| `check_subscription` | Verifies user's channel subscriptions. |
| `get_ref_link` | Generates referral link. |
| `copy_ref_{user_id}` | Copies referral link for easy sharing. |
| `toggle_channel_{id}` | Toggles channel subscription requirement. |
| `delete_channel_{id}` | Initiates channel deletion. |
| `confirm_delete_channel_{id}` | Confirms channel deletion. |

---

## Development Guide

# Development Guide

This guide explains how to extend and modify the bot for developers.

## Getting Started with Development

1. Clone the repository
2. Set up your environment as described in the Installation Guide
3. Review the code structure to understand the architecture

## Project Structure

```
src/
├── bot.py                 # Main entry point
├── config.py              # Configuration
├── handlers/              # Message handlers
│   ├── admin.py           # Admin commands
│   └── user.py            # User commands
├── keyboards/             # Telegram keyboard layouts
│   ├── admin_kb.py        # Admin keyboards
│   └── user_kb.py         # User keyboards
├── middlewares/           # Request processing middleware
│   ├── logging.py         # Logging middleware
│   ├── subscription.py    # Channel subscription check
│   └── user_registration.py # User registration and blocking
├── services/              # Database and business logic
│   ├── channel_service.py # Channel management
│   ├── database.py        # DB models and connection
│   └── user_service.py    # User management
└── utils/                 # Helper functions
    ├── admin_utils.py     # Admin utilities
    ├── filters.py         # Custom filters
    ├── misc.py            # Miscellaneous utilities
    └── subscription_utils.py # Subscription checking
```

## Adding a New Command

1. Choose the appropriate handler file (`user.py` or admin.py)
2. Create your handler function:

```python
async def my_command(message: types.Message):
    """Handle the /mycommand command"""
    await message.answer("This is my new command!")
```

3. Register the handler in the register_handlers function:

```python
def register_user_handlers(dp: Dispatcher):
    # Existing handlers...
    dp.register_message_handler(my_command, commands=["mycommand"])
```

## Working with the Database

### Creating a New Model

Add to database.py:

```python
class MyNewModel(Base):
    __tablename__ = 'my_new_table'
    id = Column(Integer, Sequence('my_model_id_seq'), primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
```

### Creating a New Service

Create a new file `services/my_service.py`:

```python
from sqlalchemy.orm import Session
from .database import MyNewModel, get_database_session

class MyService:
    def __init__(self):
        self.session: Session = get_database_session()
    
    def add_item(self, name: str) -> MyNewModel:
        new_item = MyNewModel(name=name)
        self.session.add(new_item)
        self.session.commit()
        return new_item
    
    def close_session(self):
        self.session.close()
```

## Creating Custom Keyboards

Add to an existing keyboard file or create a new one:

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

my_keyboard = InlineKeyboardMarkup(row_width=2)
my_keyboard.add(
    InlineKeyboardButton("Button 1", callback_data="button1"),
    InlineKeyboardButton("Button 2", callback_data="button2")
)
```

## Adding a New Middleware

Create a new file in the `middlewares` directory:

```python
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

class MyMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Your preprocessing logic here
        print(f"Received message from {message.from_user.id}")
```

Register in bot.py:

```python
from middlewares.my_middleware import MyMiddleware

# ...

dp.middleware.setup(MyMiddleware())
```

## Code Examples

### Handling Callback Queries

```python
async def my_callback_handler(callback: types.CallbackQuery):
    # Answer callback to avoid the "loading" state
    await callback.answer()
    
    # Extract data from callback
    data = callback.data.replace("my_prefix_", "")
    
    # Edit the message
    await callback.message.edit_text(f"You selected: {data}")

# Register handler
dp.register_callback_query_handler(
    my_callback_handler, 
    lambda c: c.data and c.data.startswith("my_prefix_")
)
```

### Using States for Multi-step Interactions

```python
from aiogram.dispatcher.filters.state import State, StatesGroup

# Define states
class MyStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()

# First handler
async def start_process(message: types.Message):
    await message.answer("Please enter your name:")
    await MyStates.waiting_for_name.set()

# Handler for the name state
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    
    await message.answer("Now enter your age:")
    await MyStates.waiting_for_age.set()

# Handler for the age state
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
        
    await message.answer(f"Thank you! Your name is {data['name']} and your age is {data['age']}")
    await state.finish()

# Register handlers
dp.register_message_handler(start_process, commands=["myprocess"])
dp.register_message_handler(process_name, state=MyStates.waiting_for_name)
dp.register_message_handler(process_age, state=MyStates.waiting_for_age)
```

### Adding a New Admin Feature

```python
async def admin_feature(message: types.Message):
    """Handle the /adminfeature command"""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only for admins")
        return
        
    # Admin logic here
    await message.answer("Admin feature activated")

# Register handler
dp.register_message_handler(admin_feature, commands=["adminfeature"])
```

## Best Practices

1. **Always close database sessions** using `try/finally` or the `close_session()` method
2. **Use middleware** for cross-cutting concerns rather than repeating code
3. **Handle exceptions** properly to prevent bot crashes
4. **Keep handlers small** and move business logic to services
5. **Use state management** for multi-step interactions
6. **Answer callback queries** to prevent the "loading" state in Telegram