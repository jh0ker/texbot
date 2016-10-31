#!/usr/bin/env python3

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode, ChatAction
from telegram.error import NetworkError
from time import time
import os
import logging
import subprocess
import traceback
import glob
import shutil
import python3pickledb as pickledb

# Configuration
TOKEN = 'T'

MAX_CONVERSIONS = 5  # The maximum of concurrent conversations
WORK_LOC = '/tmp/texbot'  # The location where the latex is converted

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Internal
EXE_LOC = os.path.join(os.getcwd(), 'textogif')

global db
db = pickledb.load('bot.db', True)

global tex
tex = r'\documentclass[12pt]{article} \usepackage{amssymb} \usepackage{amsmath} \pagestyle{empty} \begin{document} \begin{displaymath} %s \end{displaymath} \end{document}'

global helptext
helptext  = 'Converts LaTeX into an image \n\n'
helptext += '*Usage:* \n'
helptext += '/tex a^2+b^2=c^2 \n'
helptext += '/photo - Send images as photos \n'
helptext += '/file - Send images as files \n\n'
helptext += 'The packages `amssymb` and `amsmath` are imported, and you can use `\\\\ ` for a new line.\n'


# Converting function
def convert(bot, update, args):
    chat_id = update.message.chat.id
    bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)
    
    # Only allow X concurrent conversions
    if len(glob.glob(os.path.join(WORK_LOC, '*'))) > MAX_CONVERSIONS:
        try:
            bot.sendMessage(chat_id=chat_id, text='Sorry, I\'m too busy right now.')       
        except:
            traceback.print_exc()
        
        return 'ok'
    
    # Split message into words and remove mentions of the bot
    text = ' '.join(args)
        
    # Only continue if there's something to convert
    if len(text) < 1:
        return help(bot, update)
    
    photo = db.get(str(chat_id))
    if photo is None:
        photo = True
    
    # Construct latex code
    latex = tex % text
    latex = latex.replace(r'\\', r'\end{displaymath} \begin{displaymath}')
    
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
        origWD = os.getcwd()
        os.chdir(dname)
        
        if len(text) < 5:
            dpi = 550
        elif len(text) < 10:
            dpi = 450
        else:
            dpi = 350
             
        command = '%s -png -dpi %d -res 0.50 code.tex > /dev/null 2> /dev/null' % (EXE_LOC, dpi)
        subprocess.call(command.split(' '))
        if photo:
            command = 'convert code.png code.jpg'
            subprocess.call(command.split(' '))
        os.chdir(origWD)
        
        if photo:
            bot.sendPhoto(chat_id=chat_id, photo=open(foutname, 'rb'), reply_to_message_id=update.message.message_id)
        else:
            bot.sendDocument(chat_id=chat_id, document=open(foutname, 'rb'), filename='LaTeX.png', reply_to_message_id=update.message.message_id)
        
    # In case anything fails, send error message
    except NetworkError as e:
        if 'Photo_invalid_dimensions' in e.message:
            bot.sendMessage(chat_id=chat_id, text='Invalid photo dimensions. Try to use /file or add a newline with \\\\ somewhere.')
        else:
            raise e
    except Exception as e:
        traceback.print_exc()
        
        try:
            bot.sendMessage(chat_id=chat_id, text='Sorry, that did not work :(')
                
        except:
            traceback.print_exc()
    
        
    finally:
        try:
            fin.close()
        except:
            pass
            
        # Clean up
        shutil.rmtree(dname)


# Print help text
def as_photo(bot, update):
    try:
        chat_id = update.message.chat.id
        
        db.set(str(chat_id), True)
        
        bot.sendMessage(chat_id=chat_id, text='Got it!')
    
    except:
        traceback.print_exc()


# Print help text
def as_file(bot, update):
    try:
        chat_id = update.message.chat.id
        
        db.set(str(chat_id), False)
        
        bot.sendMessage(chat_id=chat_id, text='Got it!')
    
    except:
        traceback.print_exc()


# Print help text
def help(bot, update):
    try:
        chat_id = update.message.chat.id
        
        bot.sendMessage(chat_id=chat_id, text=helptext, parse_mode=ParseMode.MARKDOWN)
    
    except:
        traceback.print_exc()
    

def error(bot, update, error):
    """ Simple error handler """
    logger.exception(error)


u = Updater(token=TOKEN)
dp = u.dispatcher
dp.addHandler(CommandHandler('tex', convert, pass_args=True))
dp.addHandler(CommandHandler('photo', as_photo))
dp.addHandler(CommandHandler('file', as_file))
dp.addHandler(CommandHandler('help', help))
dp.addHandler(CommandHandler('start', help))
u.start_polling(timeout=30)
u.idle()

