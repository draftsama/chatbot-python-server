import datetime
from psql import PSQLConnect
#panda
import pandas as pd

class WordDetect:

  def __init__(self, database:PSQLConnect):
      self.database = database

  def keyword_detect(self, text:str):
      keywords = self.database.get_data('chatbot_keyword')
      
      if keywords is None or len(keywords) == 0:
          return None
      
      #check text is equals to keyword.text
      df_keywords = pd.DataFrame(keywords, columns=['id','text','dialog_id'])
      
      for index, row in df_keywords.iterrows():
          if row['text'] == text:
            dialog_id = row['dialog_id']
              
            #get answer by dialog_id first row
            answers = self.database.get_data('chatbot_answer', f"WHERE id = {dialog_id} LIMIT 1")
            
            if answers is None or len(answers) == 0:
                return None
            
            df_answers = pd.DataFrame(answers, columns=['id','text'])
            
            return df_answers['text'][0]
               
    

# db = PSQLConnect("localhost","marine_db","ubuntu","ubuntu")
# #get time run

# start_time = datetime.datetime.now()
# wd = WordDetect(db)
# reply = wd.keyword_detect("ดีจ้า")
# end_time = datetime.datetime.now()

# #report time as milisecond
# ms = (end_time - start_time).total_seconds() * 1000
# print(f"Time: {ms} ms")
# print(reply)
