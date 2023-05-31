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


# Load variables from .env file into environment
load_dotenv()


PORT = int(os.getenv('PORT'))
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
MODE = os.getenv('MODE')
openai.api_key = os.getenv('OPENAI_API_KEY')


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)


def chat_gpt_reply(msg):
    # ผู้ช่วย DoHome
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "คุณคือผู้ช่วยของ DoHome ที่เก่งมากๆ, คุณสามารถแนะนำสินค้า ข้อมูลสินค้า ของดูโฮมได้ทุกอย่าง, คุณจะแนะนำ DoHome เป็นอันดับแรกเสมอ, คำตอบของคุณจะต้องมาจากความเป็นจริง"},
            {"role": "user", "content": "คุณเป็นใคร"},
            {"role": "assistant", "content": "ดูโฮม สวัสดีครับ สามารถถามได้เลยครับ"},
            {"role": "user", "content": "ขอข้อมูลติดต่อ"},
            {"role": "assistant", "content": "สามารถติดต่อ DoHome ผ่านช่องทางต่อไปนี้ได้เลยครับ\n- เว็บไซต์: www.dohome.co.th\n- โทรศัพท์: 02-0278787"},
            {"role": "user", "content": msg},
        ]
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
    # print("profile: ", profile, flush=True)

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
    gptresult = chat_gpt_reply(event.message.text)
    print("gpt result: ", gptresult, flush=True)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=gptresult))

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
        response = make_response(jsonify({"error": "required json"}))
        response.status_code = 400
        return response

    if 'version' not in json_data:
        response = make_response(jsonify({"error": "required version"}))
        response.status_code = 400
        return response

    if 'model' not in json_data:
        response = make_response(jsonify({"error": "required model"}))
        response.status_code = 400
        return response

    model = replicate.models.get(
        json_data['model'])
    version = model.versions.get(
        json_data['version'])

    res = replicate.predictions.create(
        version,
        input=json_data['input']
    )
    return jsonify({
        "id": res.id
    })


@app.route('/api/replicate/prediction', methods=['GET'])
def get_prediction():
    id = request.args.get('id')

    if id is None or id == "":
        response = make_response(jsonify({"error": "required id"}))
        response.status_code = 400
        return response

    res = replicate.predictions.get(id)

    response = make_response(jsonify({
        "id": res.id,
        "status": res.status,
        "input": res.input,
        "output": res.output,
    }))
    response.status_code = 200

    return response


if __name__ == '__main__':
    if MODE == "development":
        app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        serve(app, host='0.0.0.0', port=PORT, threads=2)
