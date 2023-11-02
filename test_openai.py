
import os
from dotenv import load_dotenv
from aes import AES
import openai


ASSISTANT_NAME = "ดอลฟิน"
load_dotenv()
OPENAI_API_KEY_ENCRYPTED = os.getenv('OPENAI_API_KEY_ENCRYPTED')
if OPENAI_API_KEY_ENCRYPTED == None or OPENAI_API_KEY_ENCRYPTED == "": 
    print("OPENAI_API_KEY is empty")
    exit()

openai.api_key = AES.decrypt(OPENAI_API_KEY_ENCRYPTED)

    
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
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": msg},
            ],
            temperature=0.8,
        )
    except Exception as e:
        print(e)
        return "ไม่เข้าใจคำถามของคุณ"
    # check if the response is empty
    if len(res.choices) == 0:
        return "ไม่เข้าใจคำถามของคุณ"
    # return the first choice
    return str(res.choices[0].message['content'])


print(chat_gpt_reply("สวัสดีครับ"))
