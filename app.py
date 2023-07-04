from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, LocationSendMessage, QuickReply, QuickReplyButton, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, SeparatorComponent, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction, URIAction
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
from linebot import (
    LineBotApi, WebhookHandler
)


from flask import Flask, jsonify, request, abort, make_response, render_template, send_from_directory
from flask_cors import CORS
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
import copy
import logging
import hashlib

from oepnai_manager import openai_manager


MODE = os.getenv('MODE')
# MODE is empty force it to be 'dev'
if MODE is None:
    MODE = 'dev'


ASSISTANT_NAME = "ดอลฟิน"
# Load variables from .env file into environment
load_dotenv()


def is_empty_string(s):
    return not bool(s and s.strip())


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

# check app.log file is exists or not then delete it


# Configure logging to write to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Output to file
        logging.StreamHandler()  # Output to console
    ]
)


# def context_analysis(msg):
#     embedding_path = "./embeddings/embeddings_context.csv"
#     indexes_sort, similarities = openai_manager.get_similarity_data(
#         msg, embedding_path)
#     df = pandas.read_csv(embedding_path)
#     df = df.drop(columns=["embedding"])
#     return df.iloc[indexes_sort[0]]["context"]

def context_analysis(msg):
    system = """You are an excellent context analyzer who can analyze sentences in various forms, your responses must be in the format of JSON only, Don't explain

The types of context can be as follows:
["none","greeting","search","complaint","information","recommend","technician","location","promotion"]

Q:Recommend a tile for bathroom
A:{"context":"recommend"}
Q:Where is store?
A:{context":"location"}
Q:tile 20*30
A:{context":"search"}
Q:How is the marble tile
A:{"context":"information"}
Q:3s6igiu*&กด(_0
A:{"context":"none"}
Q:Recommend how to install tile
A:{"context":"recommend"}
Q:What is Marine Studio?
A:{"context":"information"}
Q: Marine Studio has how many branches?
A:{"context":"location"}
Q: What is you sell?
A:{"context":"information"}
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
        return None
    # return the first choice
    msg = str(res.choices[0]['message']['content'])
    # Find the JSON string using regular expressions
    match = re.search(r'({.*})', msg)

    json_object = None
    if match:
        json_object = json.loads(match.group(1))
    else:
        return None

    return json_object


# content = context_analysis("แนะนำกระเบื้องห้องนอน")
# print(content)
# exit()


def find_product(msg):
    embedding_path = "./embeddings/embeddings_products.csv"
    indexes_sort, similarities = openai_manager.get_similarity_data(
        msg, embedding_path)
    df = pandas.read_csv(embedding_path)
    df = df.drop(columns=["embedding"])
    # get 3 most similar product
    return df.iloc[indexes_sort[0:3]]


def chat_gpt_reply(msg):
    system = f"""You are helpful assistant of Marine Studio,  You are an expert in tiles and bathroom sanitary.,refer datas below
website:www.marine-studio.co.th
tel:02-234-5555
open:every day 7.00-19.00

Q:Hello
A:My name is {ASSISTANT_NAME}, Infrom about what ครับ
Q:What's มารีน ?
A:Marine Studio - The Central Hub for Decorative Materials, featuring over 2,500 items including floor and wall tiles, paint, chemicals, sanitary ware, gardening tools, along with professional installation services provided by skilled craftsmen. 
Q:Who are you?
A:My name is {ASSISTANT_NAME} I'm an assistant of Marine Studio ครับ
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
        app.logger.error(f"code : {e.status_code}")
        app.logger.error(f"code : {e.error.message}")
        app.logger.error(f"code : {e.error.details}")


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
        app.logger.error(f"code : {e.status_code}")
        app.logger.error(f"code : {e.error.message}")
        app.logger.error(f"code : {e.error.details}")


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

# =================== ROUTE ===================


@app.route('/', methods=['GET'])
def get_status():
    # return app status
    app.logger.info("Test")
    return '<h1>Test</h1>'


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
        app.logger.error(
            "Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def get_binary_data(event) -> str:
    content = line_bot_api.get_message_content(event.message.id)
    file = b""
    for chunk in content.iter_content():
        file += chunk

    return file


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    ext = 'jpg'
    message_content = line_bot_api.get_message_content(event.message.id)
    file = get_binary_data(event)
    # save image
    with open(f"images/{event.source.user_id}.{ext}", 'wb') as fd:
        fd.write(file)
    # reply image to user

    app.logger.info(f"==============================")
    app.logger.info(f"type: {event.message.type}")
    app.logger.info(f"user_name: {profile.display_name}")
    app.logger.info(f"user_id: {event.source.user_id}")
    app.logger.info(f"reply_token: {event.reply_token}")
    app.logger.info(f"==============================")


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # print("body: ", event, flush=True)
    profile = line_bot_api.get_profile(event.source.user_id)
    # print("profile: ", profile, flush=True)

    # url = 'https://api.line.me/v2/bot/message/markAsRead'
    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': 'Bearer {CHANNEL_ACCESS_TOKEN}'
    # }
    # data = {
    #     'chat': {
    #         'userId': event.source.user_id
    #     }
    # }

    # requests.post(url, headers=headers, json=data)

    app.logger.info(f"==============================")
    app.logger.info(f"type: {event.message.type}")
    app.logger.info(f"user_name: {profile.display_name}")
    app.logger.info(f"user_id: {event.source.user_id}")
    app.logger.info(f"reply_token: {event.reply_token}")
    app.logger.info(f"message: {event.message.text}")
    app.logger.info(f"==============================")

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
    reciveMsg = event.message.text

    data = context_analysis(reciveMsg)
    if data is None:
        data = {"context": "none"}

    context = data["context"]
    app.logger.info(f"context: {data}")

    if context == "none":
        replyMsg = f"{ASSISTANT_NAME} รบกวนสอบถามใหม่อีกครั้งนะครับ เนื่องจาก{ASSISTANT_NAME}ไม่สามารเข้าใจได้ครับ"
    elif context == "complaint":
        replyMsg = f"{ASSISTANT_NAME} ขอแสดงความเสียใจกับเหตุการณ์ที่เกิดขึ้นนะครับ รบกวนลูกค้าเลือกเรื่องที่ต้องการทำรายการได้เลยครับ"
    elif context == "location":
        replyMsg = f"{ASSISTANT_NAME} ขอแจ้งให้ทราบว่า {chat_gpt_reply(reciveMsg)}"
    elif context == "technician":
        replyMsg = f"""{ASSISTANT_NAME} ขอแนะนำงานบริการคุณภาพเยี่ยม จาก นายช่างดูโฮม
เรามีหลากหลายบริการ ตั้งแต่บริการปรับปรุงที่พักอาศัย บริการติดตั้งเครื่องใช้ไฟฟ้า
และบริการทำความสะอาดบำรุงรักษา ลูกค้าเลือกบริการที่ต้องการได้เลยครับ"""
    elif context == "greeting":
        replyMsg = f"{ASSISTANT_NAME} {chat_gpt_reply(reciveMsg)}"
    elif context == "information":
        replyMsg = f"{ASSISTANT_NAME} ขอแจ้งให้ทราบว่า {chat_gpt_reply(reciveMsg)}"
    elif context == "recommend":
        replyMsg = f"{ASSISTANT_NAME} ขอแนะนำ {chat_gpt_reply(reciveMsg)}"
    elif context == "promotion":
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url='https://draft-dev.online/images/promotion.jpg',
                preview_image_url='https://draft-dev.online/images/promotion.jpg'
            )
        )
        return
    elif context == "search":
        products = find_product(reciveMsg)
        # products drop first column
        replyMsg = products.to_string()

        with open('product_message.json', 'r') as f:
            message = dict()
            message['type'] = 'carousel'

            itemTemplate = json.load(f)
            contents = []
            for i in range(0, len(products)):
                # clone itemTemplate
                item = copy.deepcopy(itemTemplate)
                item['body']['contents'][0]['text'] = products.iloc[i]["tile_name"]
                # add item to contents
                contents.append(item)

            message['contents'] = contents
            flex_message = FlexSendMessage(
                alt_text="Search", contents=message)

            try:
                line_bot_api.reply_message(event.reply_token, flex_message)
            except LineBotApiError as e:
                app.logger.error(f"code : {e.status_code}")
                app.logger.error(f"code : {e.error.message}")
                app.logger.error(f"code : {e.error.details}")

                # end method
            return

    app.logger.info(f"reply : {replyMsg}")

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


@app.route('/replicate/prediction', methods=['POST'])
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


@app.route('/replicate/prediction', methods=['GET'])
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
# create route for get image


@app.route('/images/<path:filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory('images', filename)


# Log
@app.route('/fetch_logs')
def fetch_logs():
    with open('app.log', 'r') as f:
        logs = f.read()
    logs_hash = hashlib.md5(logs.encode()).hexdigest()

    if request.headers.get('If-None-Match') == logs_hash:
        return '', 304  # Return empty response if logs haven't changed
    else:
        response = app.make_response(logs)
        response.headers['ETag'] = logs_hash
        return response


@app.route('/logs')
def view_logs():
    with open('app.log', 'r') as f:
        logs = f.read()
    return render_template('logs.html', logs=logs, mode=MODE)


@app.route('/clear', methods=['POST'])
def clear_logs():
    app.logger.info('Clearing logs...')
    try:
        with open('app.log', 'w') as f:
            f.write('')
        return jsonify(success=True)
    except Exception as e:
        app.logger.error(e)
        return jsonify(success=False, error=str(e))


# Get the current date and time in the specified time zone
current_time = datetime.datetime.now(timezone)
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")


print(f"Server is running [{MODE}] - {formatted_time}", flush=True)
if __name__ == '__main__':

    if MODE == "dev":
        app.run(debug=True)
    else:
        app.run()
