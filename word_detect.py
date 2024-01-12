import datetime
from psql import PSQLConnect
#panda
import pandas as pd

class WordDetect:

  def __init__(self, database:PSQLConnect):
      self.database = database

  def keyword_detect(self, text:str):
      
        reslut_answer = None
        result_options = []
      
        res = self.database.get_data('chatbot_keyword')
        if res is None or  res['status'] == 'failed':
          return None,None
        
        keywords = res['datas']
        if keywords is None or len(keywords) == 0:
          return None,None
      #check text is equals to keyword.text
        df_keywords = pd.DataFrame(keywords, columns=['id','text','dialog_id'])

        for index, row in df_keywords.iterrows():

          if row['text'] == text:
            
            dialog_id = row['dialog_id']
            
            # print("dialog_id:",dialog_id)
            
            #get answer by dialog_id first row
            res = self.database.get_data('chatbot_answer',"*", f"WHERE id = {dialog_id} LIMIT 1")
            
            if res is None or res['status'] == 'failed':
                return None,None
              
            answers = res['datas']
   
            if answers is None or len(answers) == 0:
                return None,None
            
            df_answers = pd.DataFrame(answers, columns=['id','text'])
            
            res = self.database.get_data('chatbot_dialog_option',"*", f"WHERE dialog_id = {dialog_id}")
            result_options = None
            print(res)
            if res is not None and res['status'] == 'success':
                options = res['datas']
                if options is not None and len(options) > 0:
                    df_options = pd.DataFrame(options, columns=['id','text'])
                    result_options = df_options['text'].to_list()
                  
            
            
            
           
            
            reslut_answer = df_answers['text'].to_list()[0]
            break
            
        return reslut_answer,result_options
               
    

db = PSQLConnect("localhost","marine_db","ubuntu","ubuntu")

# #get time run

start_time = datetime.datetime.now()
wd = WordDetect(db)
reply,options = wd.keyword_detect("ดีครับ")
end_time = datetime.datetime.now()

#report time as milisecond
ms = (end_time - start_time).total_seconds() * 1000
print(f"Time: {ms} ms")
print(reply)
print(options)
