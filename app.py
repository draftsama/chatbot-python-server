import urllib3
from image_classification import ImageClassifucation
from oepnai_manager import openai_manager
from aes import AES
import hashlib
import logging
import copy
import pandas as pd
import datetime
import pytz
import replicate
import openai
import re
import json
import tempfile
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
import numpy as np
from PIL import Image, ImageOps
from flask_cors import CORS
from flask import Flask, jsonify, request, abort, make_response, render_template, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from argparse import ArgumentParser
import errno
import ssl

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage,
    FlexMessage,
    LocationMessage,
    MessagingApiBlob,
    ApiException,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
    MessageAction,
    DatetimePickerAction,
    CameraAction,
    CameraRollAction,
    LocationAction,
    
    
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
    
    
)

#TODO FIX ISUSSE LINE SDK V3 : SSL CERTIFICATE_VERIFY_FAILED
#$ sudo update-ca-certificates --fresh
#$ export SSL_CERT_DIR=/etc/ssl/certs

#---------------------------------------------



from database import DatabaseConnect
from psql import PSQLConnect
from word_detect import WordDetect
# from pythainlp.spell import correct


MODE = os.getenv('MODE')
# MODE is empty force it to be 'dev'
if MODE is None:
    MODE = 'dev'


ASSISTANT_NAME = "ดอลฟิน"
# Load variables from .env file into environment
load_dotenv()

ssl._create_default_https_context = ssl._create_unverified_context


def is_empty_string(s):
    return not bool(s and s.strip())


CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
MODE = os.getenv('MODE')
IMAGE_SIZE = int(os.getenv('IMAGE_SIZE'))
# check empty string
OPENAI_API_KEY_ENCRYPTED = os.getenv('OPENAI_API_KEY_ENCRYPTED')
if is_empty_string(OPENAI_API_KEY_ENCRYPTED):
    print("OPENAI_API_KEY is empty")
    exit()
openai.api_key = AES.decrypt(OPENAI_API_KEY_ENCRYPTED)

DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')



static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

    

# Specify the time zone for Bangkok
timezone = pytz.timezone('Asia/Bangkok')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

cors = CORS(app, resources={r"/*": {"origins": "*"}})

app.config['JSON_AS_ASCII'] = False

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
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




# Disable scientific notation for clarity
np.set_printoptions(suppress=True)


ic = ImageClassifucation("./models/model.keras", "./models/labels.txt",IMAGE_SIZE)

psql_connect = PSQLConnect(DATABASE_HOST,DATABASE_NAME,DATABASE_USER,DATABASE_PASSWORD)
word_detect = WordDetect(psql_connect)

if not psql_connect.test_connection():
    app.logger.info("Can't connect to database")
    



# def context_analysis(msg):
#     embedding_path = "./embeddings/embeddings_context.csv"
#     indexes_sort, similarities = openai_manager.get_similarity_data(
#         msg, embedding_path)
#     df = pandas.read_csv(embedding_path)
#     df = df.drop(columns=["embedding"])
#     return df.iloc[indexes_sort[0]]["context"]
def gpt_calculator(msg):
    system = """You are an excellent Tile Calculator, You must think step by step, Keep a short and concise, You are always convert the unit to meter first, Your must using to following datas

Conversion:
- 1 m = 1000cm = 39.3701 inch
- 1 sq.m. = 10000 sq.cm. = 1550 sq.in.

In 1 box:
- tile 15x80 cm = 10 pieces.
- tile 30x60 or 15x90 cm= 8 pieces.
- tile 30x45 or 20x100 cm = 6 pieces.
- tile 50x50 or 60x60 or 20x120 cm = 4 pieces. 
- tile 60x120 cm = 2 pieces.
- tile 80x80 cm = 3 pieces.
- tile 10x16 inch = 10 pieces.
- tile 12x12 inch = 11 pieces.
- tile 16x16 inch  = 6 pieces.

Q: area 3x4 m, How many use  box of tiles size 60x60cm?
A: -Calculate the area: 3 * 4 = 12 sq.m.
-Calculate the tile area: 60 * 60 = 3600 sq.cm.
-Convert unit of tile from sq.cm to sq.m : 3600 / 10000 = 0.36 sq.m.
-Calculate the number of tiles required per area: 12 / 0.36 = 33.33 pieces.
-Each box of 60x60 tiles contains 4 tiles, so we would need a total of 33.33 / 4 = 8.33 boxes.
-Since there is a fractional part, rounding up, we would need a total of 9 boxes."""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": msg},
        ],
        temperature=0.8,
        max_tokens=2048

    )
    # app.logger.info(res)

    # check if the response is empty
    if len(res.choices) == 0:
        return "ไม่เข้าใจคำถามของคุณ"
    # return the first choice
    return str(res.choices[0].message['content'])


def context_analysis(msg):
    system = """You are an excellent context analyzer who can analyze sentences in various forms, your responses must be in the format of JSON only, Don't explain

The types of context can be as follows:
["none","greeting","search","complaint","information","recommend","technician","location","promotion","calculate"]

Q:Recommend a tile for bathroom
A:{"context":"recommend"}
Q:Where is store?
A:{"context":"location"}
Q:tile 20*30
A:{"context":"search","keyword":"tile 20*30"}
Q:please help me find marble tile 60*60
A:{"context":"search","keyword":"marble tile 60*60"}
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
    df = pd.read_csv(embedding_path)
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
    flex_message_options = FlexMessage(
        alt_text="Test", contents=message)


def reply_flex_message_options(reply):
    
    # bubble_string = """{ type:"bubble", ... }"""
    # message = FlexMessage(alt_text="hello", contents=FlexContainer.from_json(bubble_string))
    # line_bot_api.reply_message(
    #     ReplyMessageRequest(
    #         reply_token=event.reply_token,
    #         messages=[message]
    #     )
    # )
    
    pass
   
    # line_bot_api.reply_message(reply, flex_message_options)
   


flex_message_find_products = None
with open('product_message.json', 'r') as f:
    content = dict()
    content['type'] = 'carousel'
    i = json.load(f)
    content['contents'] = [i, i, i]
    flex_message = FlexMessage(alt_text="Test", contents=content)



def reply_flex_message_find_products(reply):
   pass

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
@app.route('/test_post', methods=['POST'])
def test_post():
    #get json data and return it
    json_data = request.get_json()
    return make_response(jsonify(json_data), 200)

@app.route('/webhook', methods=['POST'])
def lineWebhook():

     # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except ApiException as e:
        app.logger.warn("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@app.route('/image_search', methods=['POST'])
def image_search_api():
    json_data = request.get_json()
    max = 5
    #check if image_base64 is in json_data
    if 'image_base64' not in json_data:
        return make_response(jsonify({'error': 'image_base64 not found'}), 400)
    
    if 'max' in json_data:
        max = json_data['max']
        
    
    base64_string = json_data['image_base64']
    result = ic.predict(base64_string, max)
    
    skus = [r['class'] for r in result]    
     # Create the comma-separated string of sku values for the IN clause
    sku_in_clause = ", ".join(skus)

    # Create the CASE statement for ORDER BY
    case_statement = "\n".join([f"WHEN {sku} THEN {index + 1}" for index, sku in enumerate(skus)])
    order_by_clause = f"ORDER BY CASE sku\n{case_statement}\nELSE {len(skus) + 1}\nEND;"

    # Combine the SQL command
    sql_command = f"SELECT *\nFROM tiles\nWHERE sku IN ({sku_in_clause})\n{order_by_clause}"
    df = DatabaseConnect.get_data(sql_command) 
    
    return make_response(jsonify(df.to_dict(orient='records')), 200)


@app.route('/get_products', methods=['POST'])
def get_products():
    json_data = request.get_json()
    if 'skus' not in json_data:
       return make_response(jsonify({'error': 'skus be must empty'}), 400)
   
    skus = json_data['skus']
    sku_in_clause = ", ".join(skus)
    
     # Create the CASE statement for ORDER BY
    case_statement = "\n".join([f"WHEN {sku} THEN {index + 1}" for index, sku in enumerate(skus)])
    order_by_clause = f"ORDER BY CASE sku\n{case_statement}\nELSE {len(skus) + 1}\nEND;"

    # Combine the SQL command
    sql_command = f"SELECT *\nFROM tiles\nWHERE sku IN ({sku_in_clause})\n{order_by_clause}"
    df = DatabaseConnect.get_data(sql_command) 
    
    return make_response(jsonify(df.to_dict(orient='records')), 200)


    

  
# =================== HANDLER ===================

def get_binary_data(content) -> str:
   
    file = b""
    for chunk in content.iter_content():
        file += chunk

    return file


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
     with ApiClient(configuration) as api_client:
        line_bot_blob_api = MessagingApiBlob(api_client)
        line_bot_api = MessagingApi(api_client)
        profile = line_bot_api.get_profile(event.source.user_id)
       
       
        ext = 'jpg'

        #check if static_tmp_path directory is exists or not
        if not os.path.isdir(static_tmp_path):
            os.mkdir(static_tmp_path)
        
        file_binary = line_bot_blob_api.get_message_content(message_id=event.message.id)
        # with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        #         tf.write(file_binary)
        #         tempfile_path = tf.name
       
        # dist_path = tempfile_path + '.' + ext
        # dist_name = os.path.basename(dist_path)
        # os.rename(tempfile_path, dist_path)
        
        # convert to base64
        base64_string = base64.b64encode(file_binary).decode('utf-8')
        # write to base64.txt
        # save image
   
        # reply image to user
        app.logger.info(f"==============================")
        app.logger.info(f"type: {event.message.type}")
        app.logger.info(f"user_name: {profile.display_name}")
        app.logger.info(f"user_id: {event.source.user_id}")
        app.logger.info(f"reply_token: {event.reply_token}")
        app.logger.info(f"==============================")

        result = ic.predict(base64_string, 5)
        
        #clear ram
        del file_binary
        del base64_string
        
        #list to json string
        app.logger.info(f"{json.dumps(result,indent=4)}")
        
      
        # connect to postgresql database
    
        with open('product_message.json', 'r') as f:
                message = dict()
                message['type'] = 'carousel'

                itemTemplate = json.load(f)
                contents = []
                for i in range(0, len(result)):
                    # clone itemTemplate
                    item = copy.deepcopy(itemTemplate)
                    sku = result[i]['class']
                    query = f"SELECT * FROM tiles WHERE sku = {sku}"
                    
                    
                    df = DatabaseConnect.get_data(query) 
                    if len(df) == 0:
                        continue
                    
                    card_image_url =f"https://mkt-app.dohome.co.th/images/cards/{sku}.jpg"
                    
                    text = f"{df.iloc[0]['sku']} - {df.iloc[0]['product_name']}"
                    item['hero']['url'] = card_image_url
                    item['body']['contents'][0]['text'] = text
                    # add item to contents
                    contents.append(item)
            
                if len(contents) == 0:
                    return
                    
                message['contents'] = contents
                flex_message = FlexMessage(
                    alt_text="Search", contents=FlexContainer.from_dict(message))

                
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[flex_message]
                    ))
                

                    # end method
            


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    
    with ApiClient(configuration) as api_client:
        
        line_bot_api = MessagingApi(api_client)
        profile = line_bot_api.get_profile(event.source.user_id)

        app.logger.info(f"==============================")
        app.logger.info(f"type: {event.message.type}")
        app.logger.info(f"user_name: {profile.display_name}")
        app.logger.info(f"user_id: {event.source.user_id}")
        app.logger.info(f"reply_token: {event.reply_token}")
        app.logger.info(f"message: {event.message.text}")
        app.logger.info(f"==============================")

        # receiveMsg = correct(event.message.text)
        receiveMsg = event.message.text
        #Check the message equals to keyword
        replyMsg,options = word_detect.keyword_detect(receiveMsg)
        
        
        if replyMsg is not None:
            app.logger.info(f"reply : {replyMsg}")
            
            quick_reply = None
            if options is not None:
                quickReplayItems = []
                for option in options:
                    quickReplayItems.append(QuickReplyItem(
                        action=MessageAction(label=option, text=option)))
                
                quick_reply = QuickReply(items=quickReplayItems)
            # app.logger.info(f"options : {options}")
            # app.logger.info(f"quick_reply : {quick_reply}")

            # QuickReply(items=[
            #              QuickReplyItem(
            #                         action=PostbackAction(label="label1", data="data1")),
            #                     QuickReplyItem(
            #                         action=MessageAction(label="label2", text="text2")
            #                     ),
            #                     QuickReplyItem(
            #                         action=DatetimePickerAction(label="label3",
            #                                                     data="data3",
            #                                                     mode="date")
            #                     ),
            #                     QuickReplyItem(
            #                         action=CameraAction(label="label4")
            #                     ),
            #                     QuickReplyItem(
            #                         action=CameraRollAction(label="label5")
            #                     ),
            #                     QuickReplyItem(
            #                         action=LocationAction(label="label6")
            #                     ),
            #         ])
            
            line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text=replyMsg,
                    quick_reply=quick_reply)]

            ))
           
            return
            
        
        if len(re.findall("ค้นหาสินค้า", receiveMsg)) != 0:
            reply_flex_message_options(event.reply_token)
            return

  

        if len(re.findall("ค้นหาร้านค้า", receiveMsg)) != 0:
            
            location_message = LocationMessage(
                title='DoHome',
                address='DoHome',
                latitude=13.7667711,
                longitude=100.5488918
            )
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[location_message]
                )
            )
            return

        
        #GPT
        data = context_analysis(receiveMsg)
        if data is None:
            data = {"context": "none"}

        context = data["context"]
    
        
        app.logger.info(f"context: {data}")

        if context == "none":
            replyMsg = f"{ASSISTANT_NAME} รบกวนสอบถามใหม่อีกครั้งนะครับ เนื่องจาก{ASSISTANT_NAME}ไม่สามารเข้าใจได้ครับ"
        elif context == "complaint":
            replyMsg = f"{ASSISTANT_NAME} ขอแสดงความเสียใจกับเหตุการณ์ที่เกิดขึ้นนะครับ รบกวนลูกค้าเลือกเรื่องที่ต้องการทำรายการได้เลยครับ"
        elif context == "location":
            replyMsg = f"{ASSISTANT_NAME} {chat_gpt_reply(receiveMsg)}"
        elif context == "technician":
            replyMsg = f"""{ASSISTANT_NAME} ขอแนะนำงานบริการคุณภาพเยี่ยม จาก นายช่างดูโฮม
    เรามีหลากหลายบริการ ตั้งแต่บริการปรับปรุงที่พักอาศัย บริการติดตั้งเครื่องใช้ไฟฟ้า
    และบริการทำความสะอาดบำรุงรักษา ลูกค้าเลือกบริการที่ต้องการได้เลยครับ"""
        elif context == "greeting":
            replyMsg = f"{ASSISTANT_NAME} {chat_gpt_reply(receiveMsg)}"
        elif context == "information":
            replyMsg = f"{ASSISTANT_NAME} {chat_gpt_reply(receiveMsg)}"
        elif context == "recommend":
            replyMsg = f"{ASSISTANT_NAME} {chat_gpt_reply(receiveMsg)}"
            app.logger.info(f"reply recommend : {replyMsg}")

        elif context == "calculate":
            replyMsg = gpt_calculator(receiveMsg)
        elif context == "promotion":
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[ImageMessage(
                        original_content_url='https://draft-dev.online/images/promotion.jpg',
                        preview_image_url='https://draft-dev.online/images/promotion.jpg'
                    )]
                )
            )
            
            return
        elif context == "search":
            
            keyword = receiveMsg
            #check key in data
            if "keyword" in data:
                keyword = data["keyword"]
            
            products = find_product(keyword)
        

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
                flex_message = FlexMessage(
                    alt_text="Search", contents=message)

               
                line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[flex_message]
                )
                )
                
                    # end method
                return

        app.logger.info(f"reply : {replyMsg}")

        line_bot_api.reply_message_with_http_info
        (
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=replyMsg)]
            )
        )

        


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

# check image


@app.route('/check_image/<path:filename>', methods=['GET'])
def check_image(filename):
    if os.path.isfile('images/' + filename):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed"})

# create route for upload image


@app.route('/test', methods=['POST'])
def post_test():
    # return app status
    response = make_response(jsonify({
        "status": "test"
    }))

    return response


@app.route('/upload_image', methods=['POST'])
def upload_image():

    json_data = request.get_json()
    if json_data is None:
        response = make_response(jsonify({
            "status": "failed",
            "error": "required json"
        }))
        response.status_code = 400
        return response

    if 'image' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required image base64"}))
        response.status_code = 400
        return response

    if 'name' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required name of image"}))
        response.status_code = 400
        return response

    # save image
    image_data = json_data['image']
    image_data = image_data.split(',')[1]
    image_data = bytes(image_data, encoding="ascii")
    image_data = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_data))
    image.save(os.path.join('images', json_data['name']))
    response = make_response(jsonify({
        "status": "success",
        "message": "upload image successfully"
    }))

    return response

# delete image


@app.route('/delete_image', methods=['POST'])
def del_image():
    json_data = request.get_json()
    if json_data is None:
        response = make_response(jsonify({
            "status": "failed",
            "error": "required json"
        }))
        response.status_code = 400
        return response

    if 'name' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required name of image"}))
        response.status_code = 400
        return response

    # check image in folder
    if os.path.exists(os.path.join('images', json_data['name'])):
        os.remove(os.path.join('images', json_data['name']))
        response = make_response(jsonify({
            "status": "success",
            "message": "image deleted successfully"

        }))
        return response
    else:
        response = make_response(
            jsonify({"status": "failed", "error": "image not found"}))
        response.status_code = 400
        return response


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


@app.route('/db/get_data', methods=['POST'])
def get_data_from_database():
    json_data = request.get_json()
    if json_data is None:
        response = make_response(jsonify({
            "status": "failed",
            "error": "required json"
        }))
        response.status_code = 400
        return response

    if 'table' not in json_data:
        response = make_response(
            jsonify({"status": "failed", "error": "required table"}))
        response.status_code = 400
        return response
    table = json_data['table']
    query = ""
    if 'query' in json_data:
        query = json_data['query']
    
    results = psql_connect.get_data(table,query)

    #list to json string
    return make_response(jsonify({"status": "success","datas":results}), 200)
    
@app.route('/db/insert_data', methods=['POST'])
def insert_data_to_database():
    json_data = request.get_json()

    #json format
    # {
    #     "table": "chatbot_dialog",
    #     "datas": 
    #         [{
    #             "name": "test1"
    #         },
    #           {
    #             "name": "test2"
    #         }]
    # }
    
    if json_data is None:
        return make_response(jsonify({"status": "failed", "error": "required json"}), 400)
    

    if 'table' not in json_data:
       return make_response(jsonify({'error': 'table be must empty'}), 400)
   
    if 'datas' not in json_data:
       return make_response(jsonify({'error': 'datas be must empty'}), 400)
   
   
    table = json_data['table']
    datas = json_data['datas']
    results = psql_connect.insert_data(table,datas)
    if len(results) > 0:
        return make_response(jsonify({
            "status": "success",
            "datas": results
            }), 200)
    else:
        return make_response(jsonify({"status": "failed"}), 400)

@app.route('/db/update_data', methods=['POST'])
def update_data_to_database():
    json_data = request.get_json()
    
    #json format
    # {
    #     "table": "chatbot_dialog",
    #     "update_key": "id",
    #     "datas":[
    #         {
    #             "id": 1,
    #             "name": "test1"
    #         },
    #         {
    #             "id": 2,
    #             "name": "test2"
    #         }
    #     ]
    # }
    update_key = "id"
    if json_data is None:
        return make_response(jsonify({"status": "failed", "error": "required json"}), 400)

    if 'table' not in json_data:
         return make_response(jsonify({'error': 'table be must empty'}), 400)
    if 'update_key' in json_data:
        update_key  = json_data['update_key']
    
    if 'datas' not in json_data:
        return make_response(jsonify({'error': 'datas be must empty'}), 400)
    
    table = json_data['table']
    datas = json_data['datas']
    
    is_sucess = psql_connect.update_data(table,datas,update_key)
    
    if is_sucess:
        return make_response(jsonify({"status": "success"}), 200)
    else:
        return make_response(jsonify({"status": "failed"}), 400)
    
    


@app.route('/db/delete_data', methods=['POST'])
def delete_data_from_database():
    json_data = request.get_json()

    #json format
    # {
    #     "table": "chatbot_dialog",
    #     "delete_key": "id",
    #     "key_values": [1,2,3]
    # }
    
    if json_data is None:
        return make_response(jsonify({"status": "failed", "error": "required json"}), 400)
    
    if 'table' not in json_data:
       return make_response(jsonify({'error': 'table be must empty'}), 400)
   
    if 'delete_key' not in json_data:
         return make_response(jsonify({'error': 'delete_key be must empty'}), 400)
     
    if 'key_values' not in json_data:
        return make_response(jsonify({'error': 'key_values be must empty'}), 400)
    
    table = json_data['table']
    delete_key = json_data['delete_key']
    key_values = json_data['key_values']
    is_sucess = psql_connect.delete_data(table,key_values,delete_key)
    if is_sucess:
        return make_response(jsonify({"status": "success"}), 200)
    else:
        return make_response(jsonify({"status": "failed"}), 400)
    
        
    
    
   
  


# Get the current date and time in the specified time zone
current_time = datetime.datetime.now(timezone)
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

print("Server is starting up...", flush=True)
print(f"Server is running [{MODE}] - {formatted_time}", flush=True)
if __name__ == '__main__':

   
        
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()


    app.run(debug=True, port=3000)
