


#get all images (png | jpg) in folder and order them by date
import os

from dotenv import load_dotenv
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
from linebot.v3 import (
    WebhookHandler
)
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET') 


configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        followers = line_bot_api.get_followers()
        
        print(followers)