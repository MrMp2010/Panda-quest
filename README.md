# Panda-quest

## Project Overview

PandaHub is a comprehensive project that combines a versatile Telegram bot with a dynamic web-based interface. This platform offers a wide range of functionalities, from content downloading across various platforms to AI services and an engaging coin-based economic system with interactive games. The project aims to deliver practical tools and entertainment within a user-friendly and scalable environment.

## Key Features

### Telegram Bot

* **Multi-Platform Downloader:**
    * Download videos from **YouTube**
    * Download posts and reels from **Instagram**
    * Retrieve information and music previews from **Spotify**
    * Retrieve information and music previews from **SoundCloud**
* **Artificial Intelligence (AI) Services:**
    * **GPT-3:** Question and answer with the GPT-3 language model (via OpenAI API)
    * **Image Generation:** Create images based on text descriptions
    * **Optical Character Recognition (OCR):** Extract text from uploaded images
* **Coin System & Games:**
    * Number Guessing Game with coin rewards
    * User coin management and accumulation system
* **User Management & Admin Panel:**
    * User statistics and management
    * Broadcast messaging capability
    * Database backup functionality
* **Channel Subscription Check:** Ensures users are subscribed to specified channels to access bot features.
* **Rate Limiting:** Prevents abuse by limiting the number of requests per unit of time.
* **Support:** Option for 24/7 user support.

### Web Mini-App

* **Engaging User Interface:** A web interface with modern design (HTML and inline CSS).
* **Coin Display & Transfer:** View coin balance and transfer coins to other users.
* **Games & Challenges:** Access to the number guessing game and a "challenges" section (under development).
* **Coin Rate & Marketplace:** Displays coin exchange rates and provides access to a marketplace.
* **Invite System:** Ability to invite friends and earn free coins.

## Technologies Used

**Backend (Python):**
* **Flask:** Web framework for managing Telegram webhooks and bot communication.
* **PyTelegramBotAPI (telebot):** Library for Telegram bot development.
* **OpenAI:** For interacting with AI services (GPT-3, image generation).
* **pytube:** For downloading videos from YouTube.
* **Instaloader:** For downloading content from Instagram.
* **Spotipy:** Python client for the Spotify Web API.
* **Soundcloud:** Library for interacting with the SoundCloud API.
* **SQLite3:** Lightweight database for storing user and coin information.
* **python-dotenv:** For managing environment variables.
* **Pillow (PIL):** For image processing (used in the OCR section).
* **logging, functools, json, os, time, random, string:** Standard Python modules.

**Frontend (Web Mini-App):**
* **HTML5:** Main structure of the web user interface.
* **CSS3:** Styling and appearance of the application.
* **JavaScript (Vanilla JS):** Interactive logic, modal management, and the number guessing game.

## Installation, Setup, and Running the Project

To set up and run this project, follow these steps:

### 1. Prerequisites

* Python 3.x
* Git

### 2. Clone the Repository

```bash
git clone [https://github.com/MrMp2010/Panda-quest.git](https://github.com/MrMp2010/Panda-quest.git)
cd Panda-quest
