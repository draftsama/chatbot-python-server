from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, SeparatorComponent, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction, URIAction
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
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
import re

import openai


# Load variables from .env file into environment
load_dotenv()


PORT = int(os.getenv('PORT'))
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
MODE = os.getenv('MODE')
openai.api_key = os.getenv('OPENAI_API_KEY')


with open('trainingdata.txt', 'r') as f:
    trainingdata = f.read()


def chat_gpt(text_input):
    prompt = f"[{text_input}] {trainingdata}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=1000,
        n=1,
        stop=None,
        frequency_penalty=0,
        presence_penalty=0
    )
    message = response.choices[0].text.strip()
    data = json.loads(message)

    return data


print(chat_gpt('ค้นหากระเบื้องลายเสือ'))
exit()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)


flex_message_options = None
with open('flex_message_options.json', 'r') as f:
    message = dict()
    message['type'] = 'carousel'
    message['contents'] = [json.load(f)]
    flex_message_options = FlexSendMessage(
        alt_text="Test", contents=message)


def reply_flex_message_options(reply):
    try:
        line_bot_api.reply_message(reply, flex_message_options)
    except LineBotApiError as e:
        print('e.status_code:', e.status_code)
        print('e.error.message:', e.error.message)
        print('e.error.details:', e.error.details)


flex_message_find_products = None
with open('product_message.json', 'r') as f:
    message = dict()
    message['type'] = 'carousel'
    i = json.load(f)
    message['contents'] = [i, i, i]
    flex_message_find_products = FlexSendMessage(
        alt_text="Test", contents=message)


def reply_flex_message_find_products(reply):
    try:
        line_bot_api.reply_message(reply, flex_message_find_products)
    except LineBotApiError as e:
        print('e.status_code:', e.status_code)
        print('e.error.message:', e.error.message)
        print('e.error.details:', e.error.details)


# message = dict()
# message['type'] = 'carousel'
# message['contents'] = [flex_message_json, flex_message_json]

# flex_messages = FlexSendMessage(
#     alt_text="Test", contents=message)

# try:
#     line_bot_api.broadcast(flex_messages)
# except LineBotApiError as e:
#     print('e.status_code:', e.status_code)
#     print('e.error.message:', e.error.message)
#     print('e.error.details:', e.error.details)


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

    if len(re.findall("ค้นหาสินค้า", event.message.text)) != 0:
        reply_flex_message_options(event.reply_token)
        return

    if len(re.findall("ค้นหาจากแคตตาล็อก", event.message.text)) != 0:
        reply_flex_message_find_products(event.reply_token)
        return

    if len(re.findall("ค้นหาร้านค้า", event.message.text)) != 0:
        location_message = LocationSendMessage(
            title='DoHome',
            address='DoHome',
            latitude=13.7667711,
            longitude=100.5488918
        )
        line_bot_api.reply_message(event.reply_token, location_message)
        return

    gptresult = chat_gpt(event.message.text)
    action = gptresult['action']
    product = gptresult['product']
    target = gptresult['target']

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str(gptresult)))

    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text="@"+profile.display_name))

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

    # line_bot_api.reply_message(event.reply_token, flex_message)


@app.route('/get', methods=['GET'])
def hello_world():
    return jsonify([{"id": 1, "name": "Draft"}, {"id": 2, "name": "Tester"}])


if __name__ == '__main__':
    if MODE == "development":
        app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        serve(app, host='0.0.0.0', port=PORT, threads=2)
