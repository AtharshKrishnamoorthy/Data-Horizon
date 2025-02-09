import os
import base64
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from dotenv import load_dotenv
from groq import Groq
import speech_recognition as sr
from rag import get_final_response
import re



load_dotenv()


TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


groq_client = Groq(api_key=GROQ_API_KEY)


recognizer = sr.Recognizer()

def clean_response(response):

    if isinstance(response, str):
        text_to_clean = response
    elif isinstance(response, dict):
        text_to_clean = response.get('answer', str(response))
    else:
        text_to_clean = str(response)
        

    cleaned_text = re.sub(r'<think>.*?</think>', '', text_to_clean, flags=re.DOTALL)
    cleaned_text = cleaned_text.strip()
    return cleaned_text


USERNAME, CHAT, IMAGE_QUERY = range(3)

user_sessions = {}

class UserSession:
    def __init__(self,username):
        self.username = username
        self.last_query = None
        self.last_image = None
        self.convo_history = []
        
    def add_convo(self,query,response):
        self.last_query = query
        self.convo_history.append(
            {
                "query":query,
                "response":response
            }
        )
        
    def get_convo(self):
        return self.convo_history
        

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def transcribe_audio(file_path):
    """
    Transcribe audio file using Groq's Whisper implementation
    Fallback to speech_recognition if needed
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcription = await asyncio.to_thread(
                groq_client.audio.transcriptions.create,
                file=audio_file,
                model="whisper-large-v3"
            )
            return transcription.text
    except Exception:
        try:
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                return text
        except Exception as e:
            print(f"Transcription error: {e}")
            return "Sorry, I couldn't transcribe the audio."

async def process_image_with_query(image_path, query=None):
    """
    Process image using Groq Vision model
    If no query provided, attempt OCR
    """
    base64_image = encode_image(image_path)
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                }
            ]
        }
    ]
    
    if not query:
        messages[0]["content"].append({
            "type": "text", 
            "text": "Perform OCR and extract all visible text from this image. If there are multiple languages, transcribe them all. Dont provide any addtional information other than the visible text in the image."
        })
    else:
        messages[0]["content"].append({
            "type": "text", 
            "text": query
        })
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.2-11b-vision-preview",
            max_completion_tokens=1024
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error processing image: {str(e)}"

async def start(update: Update, context):
    await update.message.reply_text(
        "Welcome! Enter your name to begin. (Eg : Arun K)"
    )
    return USERNAME

async def store_username(update: Update, context):
    username = update.message.text
    user_id = update.effective_user.id
    
    user_sessions[user_id] = UserSession(username)
    context.user_data['username'] = username
    
    await update.message.reply_text(
        f"Hello, {username}! Send me an image, audio, or text."
    )
    return CHAT


async def handle_input(update: Update, context):
    
    user_id = update.effective_user.id
    username = context.user_data.get('username', 'User')
    session = user_sessions.get(user_id)
    
    if not session:
        session = UserSession(username=username)
        user_sessions[user_id] = session
        
    
    downloads_dir = "downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    
    user_input = None
    
    if update.message.photo or (update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('image/')):

        if update.message.photo:
            photo = update.message.photo[-1]
            file = await photo.get_file()
        else:
            file = await update.message.document.get_file()
        

        original_filename = update.message.document.file_name if update.message.document else f"{file.file_unique_id}.jpg"
        file_path = os.path.join(downloads_dir, original_filename)
        

        await file.download_to_drive(file_path)
        

        user_input = await process_image_with_query(file_path)
        context.user_data['current_image'] = file_path
        
        await update.message.reply_text(user_input)
        
        # return CHAT
    

    elif update.message.voice:
        voice_file = await update.message.voice.get_file()
        voice_path = os.path.join(downloads_dir, f"{voice_file.file_unique_id}.ogg")
        await voice_file.download_to_drive(voice_path)
        
        user_input = await transcribe_audio(voice_path)
        os.remove(voice_path)
        
        await update.message.reply_text(
            f"Transcription Completed , {username} you said this: {user_input}"
        )
    
    elif update.message.text:
        user_input = update.message.text
    
    if user_input:
        response = get_final_response(user_input, username)
        response = clean_response(response)
        
        session.add_convo(user_input,response)
        
        
        await update.message.reply_text(f"{username}, {response}")
    
    return CHAT

async def handle_image_query(update: Update, context):
    user_id = update._effective_user.id
    session = user_sessions.get(user_id)
    username = context.user_data.get('username', 'User')
    
    if not session or not session.last_image:
        await update.message.reply_text("Provide a image first..")
        return CHAT
    
    user_query = update.message.text
    query_result = await process_image_with_query(session.last_image,user_query)
    
    session.add_convo(user_query,query_result)
    
    user_query = update.message.text
    
    await update.message.reply_text(
        f"{username}, here's the result of your query:\n{query_result}"
    )
    
    return CHAT

def main():
    app = Application.builder().token(TOKEN).build()
    
 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_username)],
            CHAT: [
                MessageHandler(
                    filters.PHOTO |  
                    (filters.Document.IMAGE) | 
                    filters.VOICE | 
                    filters.TEXT, 
                    handle_input
                )
            ],
            IMAGE_QUERY: [
                MessageHandler(filters.TEXT, handle_image_query)
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
    
    
    
    
