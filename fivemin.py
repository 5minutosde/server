import json
from datetime import datetime
from decouple import config
from pyrogram import Client, Filters
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


def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__,
        sort_keys=True, indent=4)


def handle_media(message):
    local_media = app.download_media(message)
    if message["voice"]:
        file_name = "medias/{}{}".format(
            message.date, message['voice'].file_id
        )
    media = storage.child(file_name).put(local_media)
    return storage.child(file_name).get_url(media['downloadTokens'])


@app.on_message()
def my_handler(client, message):
    print(message)
    data = {
            "username": message['from_user'].username,
        }
    db.child("users/{}".format(message['from_user'].id)).set(data)
    if message['reply_to_message']:
        if message.media:
            media_url = handle_media(message)
            db.child("audios/").update(
                {
                    "{}/audios".format(message['reply_to_message']['message_id']): media_url,
                })
        else:
            db.child("audios/").update({"{}/title".format(message['reply_to_message']['message_id']): message["text"]})
        return
    if message.media:
        media_url = handle_media(message)
        data = {
            "media_audio": media_url,
            "created_at": str(datetime.now()),
            "user": {
                "id": message['from_user'].id,
                "username": message['from_user'].username,
            }
        }
        return db.child("audios/{}".format(message['message_id'])).set(data)
    data = {
        "title": message["text"],
        "created_at": str(datetime.now()),
        "user": {
            "id": message['from_user'].id,
            "username": message['from_user'].username,
        }
    }
    db.child("audios/{}".format(message['message_id'])).set(data)


app.run()
