from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, SeparatorComponent, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction, URIAction
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot import (
    LineBotApi, WebhookHandler
)

from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS
from waitress import serve
from PIL import Image, ImageOps
import numpy as np
from io import BytesIO
import base64
from dotenv import load_dotenv
import os
import json
import re
import codecs
import openai
import replicate
import pytz
import datetime
import requests
import pandas

from oepnai_manager import openai_manager


# Load variables from .env file into environment
load_dotenv()


def is_empty_string(s):
    return not bool(s and s.strip())


PORT = int(os.getenv('PORT'))
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
MODE = os.getenv('MODE')
openai.api_key = os.getenv('OPENAI_API_KEY')


# check empty string
if is_empty_string(os.getenv('OPENAI_API_KEY')):
    print("OPENAI_API_KEY is empty")
    exit()

# Specify the time zone for Bangkok
timezone = pytz.timezone('Asia/Bangkok')

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config['JSON_AS_ASCII'] = False
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)


def context_analysis(msg):
    embedding_path = "./embeddings/embeddings_context.csv"
    indexes_sort, similarities = openai_manager.get_similarity_data(
        msg, embedding_path)
    df = pandas.read_csv(embedding_path)
    df = df.drop(columns=["embedding"])
    return df.iloc[indexes_sort[0]]["context"]


def find_product(msg):
    embedding_path = "./embeddings/embeddings_products.csv"
    indexes_sort, similarities = openai_manager.get_similarity_data(
        msg, embedding_path)
    df = pandas.read_csv(embedding_path)
    df = df.drop(columns=["embedding"])
    # get 3 most similar product
    return df.iloc[indexes_sort[0:3]]


def chat_gpt_reply(msg):
    system = """You are helpful assistant of Marine Studio, Don't say It's AI. ,refer datas below
website:www.marine-studio.co.th
tel:02-234-5555
Q:What's Marine Studio?
A:Marine Studio is shop that sells tiles and bathroom sanitary. We also provide installation and transportation service. 
Q:Who are you?
A:I'm an assistant of Marine Studio ครับ
            """
    # ผู้ช่วย DoHome
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": msg},
        ],
        temperature=0.8,
    )
    # check if the response is empty
    if len(res.choices) == 0:
        return "ไม่เข้าใจคำถามของคุณ"
    # return the first choice

    return str(res.choices[0].message['content'])


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
    # print("body: ", event, flush=True)
    profile = line_bot_api.get_profile(event.source.user_id)
    print("profile: ", profile, flush=True)

    url = 'https://api.line.me/v2/bot/message/markAsRead'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    data = {
        'chat': {
            'userId': event.source.user_id
        }
    }
    requests.post(url, headers=headers, json=data)

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

    print("input: ", event.message.text, flush=True)
    reciveMsg = event.message.text
    context = context_analysis(reciveMsg)

    if context == "none":
        replyMsg = "กรุณาถามใหม่อีกครั้ง"
    elif context == "promotion":
        replyMsg = "โปรโมชั่นเดือนเรามี ซื้อ 1 แถม 1 นะครับ"
    elif context == "information":
        replyMsg = chat_gpt_reply(reciveMsg)
    elif context == "recommendation":
        replyMsg = chat_gpt_reply(reciveMsg)
    elif context == "search":
        products = find_product(reciveMsg)
        # products drop first column
        replyMsg = products.to_string()

    print("reply", replyMsg, flush=True)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=replyMsg))

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


@app.route('/api/replicate/prediction', methods=['POST'])
def prediction():
    json_data = request.get_json()

    if json_data is None:
        response = make_response(jsonify({
            "status": "failed",
            "error": "required json"
        }))
        response.status_code = 400
        return response

    if 'version' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required version"}))
        response.status_code = 400
        return response

    if 'model' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required model"}))
        response.status_code = 400
        return response
    try:
        model = replicate.models.get(
            json_data['model'])
        version = model.versions.get(
            json_data['version'])

        res = replicate.predictions.create(
            version,
            input=json_data['input']
        )
    except Exception as e:
        response = make_response(jsonify({"status": "failed", "error": e}))
        response.status_code = 404
        return response

    return jsonify({
        "status": res.status,
        "id": res.id
    })


@app.route('/api/replicate/prediction', methods=['GET'])
def get_prediction():
    id = request.args.get('id')

    if id is None or id == "":
        response = make_response(
            jsonify({"status": "failed", "error": "required id"}))
        response.status_code = 400
        return response

    try:
        res = replicate.predictions.get(id)
    except Exception as e:
        response = make_response(jsonify({"status": "failed", "error": e}))
        response.status_code = 404
        return response

    response = make_response(jsonify({
        "id": res.id,
        "status": res.status,
        "input": res.input,
        "output": res.output,
    }))
    response.status_code = 200

    return response


# Get the current date and time in the specified time zone
current_time = datetime.datetime.now(timezone)
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")


print(f"Server is running [{MODE}] - {formatted_time}", flush=True)
if __name__ == '__main__':
    if MODE == "development":
        app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        serve(app, host='0.0.0.0', port=PORT, threads=2)
