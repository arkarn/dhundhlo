

TOKEN = "5071725330:AAGpS1_I0LJKEbIbmnWqpJOTkdhQWiqwiQg"
#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

import pymongo
import re
myclient = pymongo.MongoClient("mongodb+srv://arkiitkgp:admin123@cluster0.a8wtp.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
coll = myclient["dhundhlo"]["jobs"]


import math
def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c
    return d
    


CITY, USERTYPE, JOBROLE, PINCODE = range(4)

# job_keywords = {"salesman": ["sale", "sales", "salesperson", "salesmen"],
#                 "software": ["software"]
#                 }
import pgeocode
nomi = pgeocode.Nominatim('in')

def get_distance_bw_pin_latlon(pin, latlon):
    try:
        details = nomi.query_postal_code(str(pin))
        origin = (details['latitude'], details['longitude'])
        destination = (latlon[0], latlon[1])
        return round(distance(origin, destination))
    except:
        return None
    
    
def get_jobs(role, pincode, city):
    myquery = { "jobrole": {"$regex": re.compile(role, re.IGNORECASE)}, "city": {"$regex": re.compile(city, re.IGNORECASE)} }
    jobs = []
    for x in coll.find(myquery):
        if 'latlon' in x.keys():
            x['distance_from_user'] = get_distance_bw_pin_latlon(pincode, x['latlon'])
        jobs.append(x)
    return jobs
        
    

def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Delhi', 'Lucknow', 'Other']]
    update.message.reply_text(
        'Hi! I am DhundhLo bot. I will help you in getting work. '
        'Send /cancel anytime to stop talking to me.\n\n'
        'Choose city where you want work:',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Choose from below:'
        ),
    )

    return CITY


def city(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("city of %s: %s", user.first_name, update.message.text)
    city = update.message.text
    context.user_data['city'] = city
    if city.lower() in ['delhi', 'lucknow']:
        reply_keyboard = [['Employer', 'Job Seeker', 'Freelancer']]
        update.message.reply_text(
            f'Great! We are available in {city}.\n'
            'Choose the type of user you are:',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder='Choose from below:'
        ),
        )
        return USERTYPE
    else:
        update.message.reply_text(
            'Sorry :( we are not there yet! To restart conversation send /start',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


def usertype(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("usertype of %s: %s", user.first_name, update.message.text)
    usertype = update.message.text.lower()
    context.user_data['usertype'] = usertype
    if usertype == 'job seeker':
        update.message.reply_text(
            'Enter the job role you are looking for'
        )
        return JOBROLE
    elif usertype == 'employer':
        pass
    else:
        update.message.reply_text(
            'Sorry :( we are still adding this functionality! To restart conversation send /start',
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


def jobrole(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("jobrole of %s: %s", user.first_name, update.message.text)
    jobrole = update.message.text.lower()
    context.user_data['jobrole'] = jobrole
    update.message.reply_text(
        'Enter your pincode:'
    )
    return PINCODE


def pincode(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    pincode = update.message.text
    context.user_data['pincode'] = pincode
    logger.info(
        "Location of %s: %s", user.first_name, pincode
    )
    jobs = get_jobs(context.user_data['jobrole'], context.user_data['pincode'], context.user_data['city'])
    if len(jobs)>0:
        reply_string = """Great! we found jobs for you.\n"""
        for i,job in enumerate(jobs):
            reply_string += f"{i+1}: {job['company']}, {job['address']}, {job['phone']}"
            if ('distance_from_user' in job.keys()) and (job['distance_from_user'] is not None):
                reply_string += f", {job['distance_from_user']}km"
            reply_string += '\n'
    else:
        reply_string = "Sorry! We can't find any job posting yet! Will keep you posted."   
    update.message.reply_text(
        reply_string
    )
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CITY: [MessageHandler(Filters.text & ~Filters.command, city)],
            USERTYPE: [MessageHandler(Filters.text & ~Filters.command, usertype)],
            JOBROLE: [MessageHandler(Filters.text & ~Filters.command, jobrole)],
            PINCODE: [MessageHandler(Filters.text & ~Filters.command, pincode)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()
    import time
    while(1):
        time.sleep(3)
        print("sleeping")