from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, SeparatorComponent, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction, URIAction
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot import (
    LineBotApi, WebhookHandler
)
from flask import Flask, jsonify, request, abort
from waitress import serve
from PIL import Image, ImageOps
import numpy as np
from io import BytesIO
import base64
from dotenv import load_dotenv
import os
import json

# Load variables from .env file into environment
load_dotenv()


PORT = int(os.getenv('PORT'))
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
MODE = os.getenv('MODE')


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)


with open('flex_message_template.json', 'r') as f:
    flex_message_json = json.load(f)


def load_image_from_base64(base64_string):
    img_data = base64.b64decode(base64_string)
    img = Image.open(BytesIO(img_data))
    return img


@app.route('/webhook', methods=['POST'])
def lineWebhook():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("body: ", event, flush=True)
    profile = line_bot_api.get_profile(event.source.user_id)
    print("profile: ", profile, flush=True)

    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text="@"+profile.display_name))

    # location_message = LocationSendMessage(
    #     title='My Location',
    #     address='Tokyo',
    #     latitude=35.65910807942215,
    #     longitude=139.70372892916203
    # )
    # line_bot_api.reply_message(event.reply_token, location_message)

    # quick_reply_items = [
    #     QuickReplyButton(
    #         action=MessageAction(
    #             label='Yes',
    #             text='Yes'
    #         )
    #     ),
    #     QuickReplyButton(
    #         action=MessageAction(
    #             label='No',
    #             text='No',
    #         )
    #     )
    # ]

    # quick_reply = QuickReply(items=quick_reply_items)

    # message = TextSendMessage(
    #     text='Do you like LINE bot SDK?',
    #     quick_reply=quick_reply
    # )
    # line_bot_api.reply_message(event.reply_token, message)
    print(flex_message_json, flush=True)
    flex_message = FlexSendMessage.new_from_json_dict(flex_message_json)

    line_bot_api.reply_message(event.reply_token, flex_message)


@app.route('/get', methods=['GET'])
def hello_world():
    return jsonify([{"id": 1, "name": "Draft"}, {"id": 2, "name": "Tester"}])


if __name__ == '__main__':
    if MODE == "development":
        app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        serve(app, host='0.0.0.0', port=PORT, threads=2)
