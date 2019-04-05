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


def handle_media(message, username, user_id, avatar_url):
    local_media = app.download_media(message)
    if message["voice"]:
        file_name = "medias/{}{}".format(
            message.date, message['voice'].file_id
        )
    media = storage.child(file_name).put(local_media)
    return storage.child(file_name).get_url(media['downloadTokens'])


def media_message(message, username, user_id, avatar_url):
    media_url = handle_media(message, username, user_id, avatar_url)
    data = {
        "media_audio": media_url,
        "created_at": str(datetime.now()),
        "user": {
            "id": user_id,
            "username": username,
            "avatar": avatar_url
        }
    }
    return db.child("audios/{}".format(message['message_id'])).set(data)


def reply_message(message, user_id, username, user_avatar):
    message_id = message['reply_to_message']['message_id']
    if message.media:
        media_url = handle_media(message, username, user_id, user_avatar)
        db.child("audios/").update(
            {
                "{}/media_audio"
                .format(message_id): media_url,
            })
    else:
        slug = slugify(message["text"] + '-por-' + username)
        db.child("audios/").update({
            "{}/title".format(message_id): message["text"],
            "{}/slug".format(message_id): slug
        })


def user_photo(photo_id, username, user_id):
    user_photo = app.download_media(photo_id)
    file_name = "medias/{}{}".format(username, photo_id)
    media = storage.child(file_name).put(user_photo)
    media_url = storage.child(file_name).get_url(media['downloadTokens'])
    db.child("users/").update(
        {
            "{}/avatar".format(user_id): media_url,
        })
    return media_url


def handle_message(message, user_id, username, user_avatar):
    if message['reply_to_message']:
        return reply_message(message, user_id, username, user_avatar)
    if message.media:
        return media_message(message, user_id, username, user_avatar)

    slug = slugify(message["text"] + '-por-' + username)
    data = {
        "title": message["text"],
        "slug": slug,
        "created_at": str(datetime.now()),
        "user": {
            "id": user_id,
            "username": username,
            "avatar": user_avatar
        }
    }
    db.child("audios/{}".format(message['message_id'])).set(data)


@app.on_message()
def my_handler(client, message):

    username = message['from_user'].username
    user_id = message['from_user'].id
    photo_id = message['from_user'].photo.big_file_id

    if str(user_id) in allowed_users:
        user = db.child("users/{}".format(user_id)).get().val()
        if user:
            handle_message(message, user_id, username, user['avatar'])
        else:
            data = {
                "username": username,
            }
            db.child("users/{}".format(user_id)).set(data)
            avatar_url = user_photo(photo_id, username, user_id)
            handle_message(message, user_id, username, avatar_url)
    else:
        data = {
            "username": username,
            "first_name": message['from_user'].first_name,
        }
        db.child("wait_list/{}".format(user_id)).set(data)


app.run()
