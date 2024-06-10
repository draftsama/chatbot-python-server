import shutil
import time
import zipfile
import urllib3
from aes import AES
import hashlib
import logging
import copy
import pandas as pd
import datetime
import pytz
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
from argparse import ArgumentParser
from werkzeug.utils import secure_filename
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
    PushMessageRequest
    
)
from linebot.v3.models import (
    UnknownEvent
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
from werkzeug.middleware.proxy_fix import ProxyFix
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


DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')



static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

    

timezone = pytz.timezone('Asia/Bangkok')

app = Flask(__name__)
# app.wsgi_app = middleware(app.wsgi_app)

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



psql_connect = PSQLConnect(DATABASE_HOST,DATABASE_NAME,DATABASE_USER,DATABASE_PASSWORD)
word_detect = WordDetect(psql_connect)

if not psql_connect.test_connection():
    app.logger.info("Can't connect to database")
    



def load_image_from_base64(base64_string):
    img_data = base64.b64decode(base64_string)
    img = Image.open(BytesIO(img_data))
    return img

# =================== ROUTE ===================

ignore_paths = ['/logs', '/clear','/fetch_logs','/images','/check_image']

@app.before_request
def before_request_func():
    
    
    #NOTICE: i don't know why i can't response 401
    api_key = request.headers.get('Api-Key')
    print(request.path)
    
    
    # return make_response(jsonify({'message': 'Hello World'}), 200)
    for path in ignore_paths:
        
        #get prefix path
        if request.path.startswith(path):
            return None
            
            
    if api_key is None:
        return make_response(jsonify({
            "error": "Unauthorized",
            "message": "API Key is required"
        }), 200)
    
    if api_key != os.getenv('MARINE_API_KEY'):
        return make_response(jsonify({
            "error": "Unauthorized",
            "message": "Invalid API Key"
        }), 200)
    
    
    
   
# @app.after_request
# def after_request_func(response):
#     print("after_request executing!")
#     return response
        

@app.route('/test_get', methods=['GET'])
def test_get():
    
    api_key = request.headers.get('Api-Key')

    return make_response(jsonify({'api_key': api_key}), 200)


@app.route('/test_post', methods=['POST'])
def test_post():
    #get json data and return it
    print(request.get_json())
    json_data = request.get_json()
    return make_response(jsonify(json_data), 200)

@app.route('/webhook', methods=['POST'])
def lineWebhook():

     # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except ApiException as e:
        app.logger.warn("Got exception from LINE Messaging API: %s\n" % e.body)
    except InvalidSignatureError:
        abort(400)

    return 'OK'




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

@handler.add(UnknownEvent)
def handle_unknown_left(event):
    app.logger.info(f"unknown event {event}")



def reply_message(token,msgs):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            res = line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=token,
                    messages=msgs
                ))
            app.logger.info(f"line response status_code: {res.status_code}")
            app.logger.info(f"line response data: {res.data}")
        except Exception as e:
            app.logger.info(f"error reply")
            app.logger.info(e)

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
  

        app.logger.info(f"==============================")
        app.logger.info(f"type: {event.message.type}")
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
            app.logger.info(f"options : {options}")
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
            
            reply_message(event.reply_token,
                        [TextMessage(
                        text=replyMsg,
                        quick_reply=quick_reply)])
            return
            

 



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
    folder_image = 'images'
    image_name = json_data['name']

    file_extension = os.path.splitext(image_name)[1].lower()
    
    if file_extension in ['.jpg', '.jpeg']:
            image = image.convert("RGB")

    image.save(os.path.join(folder_image , json_data['name']))
    
    #get base url
    base_url = request.base_url
    image_url = base_url + 'api/images/' + image_name
   
    response = make_response(jsonify({
        "status": "success",
        "message": "upload image successfully",
        "image_url": image_url
    }))
    
    reduct_images('images', 40)

    return response

def reduct_images(path, limit_image = 20):
    images = []
    
    for f in os.listdir(path):
        #get only image file and ignore file name start with "save_"
        if f.endswith(('.png', '.jpg')) and not f.startswith('save_'):
            images.append(f)
            
    #sort by date
    images.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
    
    #if image count > limit_image then remove another images
    if len(images) > limit_image:
        for i in range(len(images) - limit_image):
            os.remove(os.path.join(path, images[i]))
            images.pop(i)
            

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
            "message": "image deleted successfully",

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

    columns = ""
    if 'columns' in json_data:
        columns = json_data['columns']
    
    query = ""
    if 'query' in json_data:
        query =json_data['query']
    
    
    
    
    results = psql_connect.get_data(table,columns,query)

    return make_response(jsonify(results), 200)

#-------- new get_data2 ----------
@app.route('/db/get_data2', methods=['POST'])
def get_data_from_database2():
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

 
    columns = ""
    if 'columns' in json_data:
        columns = json_data['columns']
        
    query = ""
    where = ""
    if 'where' in json_data:
        where =json_data['where']
        if where is not None and where != "":
            query = f" WHERE {where}"
    
    order_by = ""
    if 'order_by' in json_data:
        order_by =json_data['order_by']
        if order_by is not None and order_by != "":
            query += f" ORDER BY {order_by}"
   

    if 'offset' in json_data: 
        offset = None
        try:
            offset = int(json_data['offset'])
        except:
            offset = None
        finally:
            if offset is not None:
                query += f" OFFSET {offset}"
        
  
    if 'limit' in json_data:
        limit = None
        try:
            limit = int(json_data['limit'])
        except:
            limit = None
        finally:
            if limit is not None:
                query += f" LIMIT {limit}"
    
    

    
    
    results = psql_connect.get_data(table,columns,query)

    return make_response(jsonify(results), 200)
    
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
    
    if len(datas) == 0:
        return make_response(jsonify({'error': 'datas be must empty'}), 400)
    
    if len(datas) > 100:
        return make_response(jsonify({'error': 'datas must be less than 100'}), 400)
   
    target_key = None
    if 'target_key' in json_data:
        target_key = json_data['target_key']
    
    
    try:
        df = pd.DataFrame(datas)
        results = DatabaseConnect.insert_data(table,df,target_key)
        
        if len(results) > 0:
            return make_response(jsonify({
                "status": "success",
                "datas": results.to_dict(orient='records')
                }), 200)
        else:
            return make_response(jsonify({"status": "failed"}), 400)
        
    except Exception as e:
        return make_response(jsonify({
            "status": "failed",
            "error": str(e)
            }), 400)
   
  

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
    
    if len(datas) == 0:
        return make_response(jsonify({'error': 'datas be must empty'}), 400)
    
    
    try:
        df = pd.DataFrame(datas)
        results = DatabaseConnect.update_data(table,df,update_key)
        
        if len(results) > 0:
            return make_response(jsonify({
                "status": "success",
                "datas": results.to_dict(orient='records')
                }), 200)
        else:
            return make_response(jsonify({"status": "failed"}), 400)
    except Exception as e:
        return make_response(jsonify({
            "status": "failed",
            "error": str(e)
            }), 400)
        
    
    


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
    
        
@app.route('/line_sendmsg', methods=['POST'])
def line_sendmsg():
    json_data = request.get_json()
    
    if 'user_id' not in json_data:
       return make_response(jsonify({'error': 'user_id is require'}), 400)
   
    if 'msg' not in json_data:
       return make_response(jsonify({'error': 'msg is require'}), 400)
   
    user_id = json_data['user_id']
    msg = json_data['msg']
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=msg)]
            ))
        
    
    return make_response(jsonify({"status": "success"}), 200)

@app.route('/line_send_flexmsg', methods=['POST'])
def line_send_flexmsg():
    json_data = request.get_json()
    
    flex_name = 'New Message'
    
    if 'user_id' not in json_data:
       return make_response(jsonify({'error': 'user_id is require'}), 400)

   
    if 'flex_msg' not in json_data:
       return make_response(jsonify({'error': 'flex_msg is require'}), 400)
   

    if 'flex_name' in json_data:
        if not is_empty_string(json_data['flex_name']):
            flex_name = json_data['flex_name']
   
    user_id = json_data['user_id']
    flex_msg = json_data['flex_msg']

    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[FlexMessage(
                    alt_text=flex_name,
                    contents=FlexContainer.from_dict(flex_msg)
                )]
            ))
        
    return make_response(jsonify({"status": "success"}), 200)


@app.route('/line_sendimg', methods=['POST'])
def line_sendimg():

    json_data = request.get_json()
    
    if 'user_id' not in json_data:
       return make_response(jsonify({'error': 'user_id is require'}), 400)
   
    if 'img_url' not in json_data:
       return make_response(jsonify({'error': 'img_url is require'}), 400)
   
    user_id = json_data['user_id']
    img_url = json_data['img_url']
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[ImageMessage(
                        original_content_url=img_url,
                        preview_image_url=img_url
                    )]
            ))
        
    return make_response(jsonify({"status": "success"}), 200)


# Get the current date and time in the specified time zone
current_time = datetime.datetime.now(timezone)
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

print("Server is starting up...", flush=True)
print(f"Server is running [{MODE}] - {formatted_time}", flush=True)
if __name__ == '__main__':
    app.run(debug=True, port=3000)
