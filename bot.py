#!/usr/bin/env python3

import telegram
from flask import Flask, request
from time import time
import os
import traceback
import glob
import shutil
import pickledb

# Configuration
BOTNAME = 'examplebot'  # The name of the bot, without @
TOKEN = ''  # Security Token given from the @BotFather
BASE_URL = 'sub.example.com'  # Domain name of your server, without protocol. You may include a port, if you dont want to use 443.
HOST = '0.0.0.0'  # IP Address on which Flask should listen on
PORT = 5000  # Port on which Flask should listen on

# If Flask won't handle your SSL stuff, ignore this
CERT     = '/etc/pki/tls/certs/examplebot.pem'
CERT_KEY = '/etc/pki/tls/certs/examplebot.key'

MAX_CONVERSIONS = 5  # The maximum of concurrent conversations
WORK_LOC = '/tmp/texbot'  # The location where the latex is converted

# Internal
EXE_LOC = os.path.join(os.getcwd(), 'textogif')

ABOTNAME = '@' + BOTNAME
CONTEXT = (CERT, CERT_KEY)

app = Flask(__name__)

global bot
bot = telegram.Bot(token=TOKEN)

global db
db = pickledb.load('bot.db', True)

global tex
tex = '\\documentclass[12pt]{article} \\pagestyle{empty} \\begin{document} \\begin{displaymath} %s \\end{displaymath} \\end{document}'

global helptext
helptext  = 'Converts LaTeX into an image \n\n'
helptext += '*Usage:* \n'
helptext += '*/tex a^2+b^2=c^2* \n\n'
helptext += 'Questions? Message my creator @jh0ker'

# Converting function
def convert(update):
    chat_id = update.message.chat.id
    bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)
    
    # Only allow X concurrent conversions
    if len(glob.glob(os.path.join(WORK_LOC, '*'))) > MAX_CONVERSIONS:
        bot.sendMessage(chat_id=chat_id, text='Sorry, I\'m too busy right now.')
        return 'ok'
    
    # Split message into words and remove mentions of the bot
    text = list([word.replace(ABOTNAME, '') for word in filter(lambda word2: word2 != ABOTNAME, update.message.text.split())])
        
    # Only continue if there's something to convert
    if len(text) < 2:
        return help(update)
    
    # Check if this chat gets files or photos
    ftype = db.get(chat_id)
    if ftype is None:
        ftype = 'P'
    
    photo = (ftype == 'P')
    
    # Construct latex code
    latex = tex % ' '.join(text[1:])
    
    # Create a directory for each request, so we can work undisturbed
    dname = hex(int(time() * 10000000))[2:] 
    dname = os.path.join(WORK_LOC, dname)
    finname = os.path.join(dname, 'code.tex')
    foutname = os.path.join(dname, ('code.jpg' if photo else 'code.png'))
    
    os.makedirs(dname)
    
    try:
        fin = open(finname, 'w')
        fin.write(latex)
        fin.close()
        
        # Run perl script
        command = 'cd %s; %s -png -dpi 400 -res 0.50 code.tex > /dev/null 2> /dev/null%s' % (dname, EXE_LOC, ('; convert code.png code.jpg' if photo else ''))
        os.system(command)
        
        if photo:
            bot.sendPhoto(chat_id=chat_id, photo=open(foutname, 'rb'), reply_to_message_id=update.message.message_id)
        else:
            bot.sendDocument(chat_id=chat_id, document=open(foutname, 'rb'), filename='LaTeX.png', reply_to_message_id=update.message.message_id)
        
    # In case anything fails, send error message
    except Exception as e:
        bot.sendMessage(chat_id=chat_id, text='Sorry, that did not work :(')
        
    finally:
        try:
            fin.close()
        except:
            pass
            
        # Clean up
        shutil.rmtree(dname)
        return 'ok'

# This chat gets photos!
def as_photo(update):
    chat_id = update.message.chat.id
    
    db.set(chat_id, 'P')
    
    bot.sendMessage(chat_id=chat_id, text='Got it!')
    
    return 'ok'
    
# This chat gets files!
def as_file(update):
    chat_id = update.message.chat.id
    
    db.set(chat_id, 'F')
    
    bot.sendMessage(chat_id=chat_id, text='Got it!')
    
    return 'ok'
            

# Print help text
def help(update):
    chat_id = update.message.chat.id
    
    bot.sendMessage(chat_id=chat_id, text=helptext, parse_mode=telegram.ParseMode.MARKDOWN)
    
    return 'ok'
    
# The webhook for Telegram messages
@app.route('/webhook_tg', methods=['POST'])
def tg_webhook_handler():
    if request.method == "POST":
        
        # Retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))
        
        text = update.message.text
        
        # split command into list of words and remove mentions of botname
        text = list([word.replace(ABOTNAME, '') for word in filter(lambda word2: word2 != ABOTNAME, text.split())])
        
        # Bot was invited to a group chat or received an empty message
        if update.message.new_chat_participant is not None and update.message.new_chat_participant.username == BOTNAME or len(text) is 0:
            return help(update)
            
        # Text is empty
        elif len(text) is 0:
            return 'ok'
            
        # Run commands
        elif text[0] == '/tex':
            return convert(update)
        elif text[0] == '/photo':
            return as_photo(update)
        elif text[0] == '/file':
            return as_file(update)
        elif text[0] == '/help' or text[0] == '/start':
            return help(update)
            
    return 'ok'

# Go to https://BASE_URL/set_webhook with your browser to register the telegram webhook of your bot
# You may want to comment out this route after triggering it once
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://%s/webhook_tg' % BASE_URL)
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

# Confirm that the bot is running and accessible by going to https://BASE_URL/ with your browser
@app.route('/')
def index():
    return 'Texbot is running!'
        
# Start Flask with SSL handling
#app.run(host=HOST,port=PORT, ssl_context=CONTEXT, threaded=True, debug=False)

# Start Flask without SSL handling
app.run(host=HOST,port=PORT, threaded=True, debug=False)

