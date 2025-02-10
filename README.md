# 🤖 SQL RAG Chatbot

Welcome to this awesome SQL RAG chatbot project! It's a super cool tool that lets you chat with your SQL databases through Telegram using natural language. Whether you're typing, sending voice messages, or even sharing images, this bot's got you covered! 

![SQL RAG Architecture](https://github.com/AtharshKrishnamoorthy/SQL-RAG-Chatbot/blob/main/SQL%20RAG%20Architecture%20Final.png)

## ✨ What's Cool About It?

- 🗣️ **Chat with Your Database**: Just ask questions naturally, and the bot converts them to SQL
- 📱 **Multiple Ways to Ask**:
  - ⌨️ Type your questions
  - 🖼️ Send images with text (it'll read them!)
  - 🎤 Send voice messages
- 🧠 **Smart Memory**: Remembers your conversation for better follow-ups. Maintains  a session history for each user.
- 🎯 **RAG Pipeline**: Utilizes RAG Architecture to retrieve the relevant info from the Vector DB and answer.
- 📱 **Easy Telegram Access**: Chat with your database like you're texting a friend
- 📊 **Performance Tracking**: You can track the Logs and traces of the chatbot through opik. 

## 🛠️ Tech Stack

### Core Stuff
- 🐍 Python 3.11+
- 🗄️ SQLAlchemy
- 🎲 MySQL Database
- ⛓️ LangChain
- 🔍 FAISS Vector Store
- 🧠 Groq API (LLM)

### Important Libraries
- `langchain-groq`: For utilizing Groq API Providers from langchain integrations for utilizing open sourced LLMs.
- `langchain`: For orchestrating the RAG application. 
- `telegram`: To make it all chat-friendly
- `speech_recognition`: For recording audio through our microphone to make use of the voice feature. 
- `FAISS`: Local Vector DB for storing the SQL data Embeddings.
- 'langchain-huggingface`: Making use of the huggingface Embedding models with pangchain integration to convert the doc data to Embeddings. 
- `dotenv`: Helps to load all the env Variables. 

## 🏗️ How It Works

The bot has two main parts:

### 🎯 Pipeline 1 - SQL Magic
1. Gets your message
2. Processes it with LangChain
3. Creates SQL Query
4. Runs the query on your database
5. Gets your data

### 🎨 Pipeline 2 - Smart Responses
1. Turns SQL results into vectors
2. Stores them in FAISS
3. Finds relevant info
4. Creates a natural response
5. Keeps track of your chat

## 🚀 Getting Started

### What You'll Need
- 🐍 Python 3.11+
- 🎲 MySQL Server
- 📱 Telegram Account
- 🔑 API Keys for:
  - Groq
  - Telegram Bot
  - Opik (for watching performance)

### Let's Set It Up!

1. Grab the code:
```bash
git clone https://github.com/AtharshKrishnamoorthy/SQL-RAG-Chatbot.git
cd SQL-RAG-Chatbot
```

2. Create your Python playground:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Install the goodies:
```bash
pip install -r requirements.txt
```

4. Set up your secrets in `.env`:
```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_TOKEN=your_telegram_token
OPIK_API_KEY=your_opik_api_key
```

5. 🔥 Here's the cool part - connect to YOUR database in `conn.py`:
```python
SQLALECHEMY_DB_URL = "mysql://username:password@host:port/database_name"
```

That's it! Just plug in your database details, and you're ready to chat with your data! 🎉

### 🎮 Fire It Up!

1. Start your bot:
```bash
python bot.py
```

2. Find it on Telegram:
   - Search for your bot username
   - Hit `/start`
   - Tell it your name
   - Start asking questions about your data! 🚀

## 💡 Try These Out!

1. **Text Questions**:
   ```
   "Hey, show me last month's orders!"
   ```

2. **Voice Questions**:
   - Just send a voice message asking about your data
   - The bot will understand and respond! 🎤

3. **Image Questions**:
   - Snap a pic of some text
   - The bot will read and process it! 📸

## 📁 What's Where

```
SQL-RAG-Chatbot/
├── bot.py              # Your Telegram buddy
├── conn.py            # Database connection magic
├── pipeline1.py       # SQL query wizardry
├── rag.py             # RAG smarts
├── requirements.txt   # All the dependencies
└── .env              # Your secret stuff
```

## 🤝 Want to Help?

1. Fork it!
2. Create your branch: `git checkout -b feature/CoolNewThing`
3. Commit your changes: `git commit -m 'Add some CoolNewThing'`
4. Push it: `git push origin feature/CoolNewThing`
5. Open a Pull Request! 🎉

---

💡 **Pro Tip**: This bot works with ANY  database be it MYSQL , Postgress! Just update the connection URL in `conn.py`, and you're good to go. Chat with your data through Telegram, no matter what database you're using! 🚀
