from datetime import datetime
from decouple import config
from pyrogram import Client
from slugify import slugify

import pyrebase

api_id = config('API_ID', cast=int)
api_hash = config('API_HASH')
app = Client(config('BOT_TOKEN'), api_id, api_hash)

firebase_config = {
    "apiKey": config('APIKEY'),
    "authDomain": config('AUTHDOMAIN'),
    "databaseURL": config('DATABASEURL'),
    "projectId": config('PROJECTID'),
    "storageBucket": config('STORAGEBUCKET'),
    "messagingSenderId": config('MESSAGINGSENDERID')
  }

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
storage = firebase.storage()

allowed_users = config('ALLOWED_USERS')

def handle_media(message, username, user_id):
    local_media = app.download_media(message)
    if message["voice"]:
        file_name = "medias/{}{}".format(
            message.date, message['voice'].file_id
        )
    media = storage.child(file_name).put(local_media)
    media_url = storage.child(file_name).get_url(media['downloadTokens'])
    data = {
        "media_audio": media_url,
        "created_at": str(datetime.now()),
        "user": {
            "id": user_id,
            "username": username,
        }
    }
    return db.child("audios/{}".format(message['message_id'])).set(data)


def reply_message(message, username):
    if message.media:
        media_url = handle_media(message)
        db.child("audios/").update(
            {
                "{}/audios".format(message['reply_to_message']['message_id']): media_url,
            })
    else:
        slug = slugify(message["text"] + '-por-' + username)
        db.child("audios/").update({
            "{}/title".format(message['reply_to_message']['message_id']): message["text"],
            "{}/slug".format(message['reply_to_message']['message_id']): slug
        })


@app.on_message()
def my_handler(client, message):

    print(message)
    username = message['from_user'].username
    user_id = message['from_user'].id
    if str(user_id) in allowed_users:
        data = {
            "username": username,
        }
        db.child("users/{}".format(user_id)).set(data)

        if message['reply_to_message']:
            return reply_message(message, username)
        if message.media:
            return handle_media(message, username, user_id)

        slug = slugify(message["text"] + '-por-' + username)
        data = {
        "title": message["text"],
            "slug": slug,
            "created_at": str(datetime.now()),
            "user": {
                "id": user_id,
                "username": username,
            }
        }
        db.child("audios/{}".format(message['message_id'])).set(data)
    else:
        data = {
            "username": username,
        }
        db.child("wait_list/{}".format(user_id)).set(data)


app.run()
