import pandas as pd
import numpy as np 
import psycopg2
import datetime


# HOST = "localhost"
# DATABASE = "marine_db"
# USER = "ubuntu"
# PASSWORD = "ubuntu"
# TABLE = "chatbot_dialog"

class PSQLConnect:
    def __init__(self,host:str,database:str,user:str,password:str):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
    
    def test_connection(self)->bool:
        conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password)

        cur = conn.cursor()
        
        try:
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            cur.close()
            conn.close()
            return False
        finally:
            if conn is not None:
                conn.close()
       
    
    def get_data(self,table:str,columns:str="*",query:str=""):
        
        res_datas = []
        sql_query = ""

           
        if columns == None or columns == "":
           columns = "*"
          
           
        if query != None and query != "":
            sql_query = f"SELECT * FROM {table} {query}"
        else:
            sql_query = f"SELECT * FROM {table}"
        

        try:
              
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password)

            cur = conn.cursor()
            
            cur.execute(sql_query)
            records = cur.fetchall()
            #get column names
            column_names = [desc[0] for desc in cur.description]
            
            #convert to json
         
            for record in records:
                data = {}
                for i in range(len(column_names)):
                    if isinstance(record[i], datetime.datetime):
                        data[column_names[i]] = record[i].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        data[column_names[i]] = record[i]
                        
                res_datas.append(data)
            
          
            
           
        except (Exception, psycopg2.DatabaseError) as error:
            if conn is not None:
                conn.close()
            if cur is not None:
                cur.close()
            return {"status":"failed","datas":[],"sql_query":sql_query}
                
        finally:
            if conn is not None:
                conn.close()
            if cur is not None:
                cur.close() 
            return {"status":"success","datas":res_datas,"sql_query":sql_query}
      

    def insert_data(self,table:str,json_data:list):
        
        try:
            if type(json_data) != list:
                raise Exception('Data must be a list')
        
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password)

            cur = conn.cursor()
            #get all column names without create_at and id
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name NOT IN ('id','create_at');"
            cur.execute(query)
            
            column_names = cur.fetchall()
            column_names = [column_name[0] for column_name in column_names]

            if column_names == []:
                raise Exception('Table not found')
            
      
            #get all values
            for data in json_data:
                
                #get contains key column_names in json_data into keys
                keys = [key for key in data.keys() if key in column_names]   
                             
                value = ','.join(f"'{str(data[column_name])}'" for column_name in keys)
                
                keys = ','.join(keys)
                query = f"INSERT INTO {table} ({keys}) VALUES ({value})"
                cur.execute(query)
                print(query)
            
            conn.commit()
       
            
            #get data after insert
            query = f"SELECT * FROM {table} ORDER BY id DESC LIMIT {len(json_data)}"
            # print(query)
            cur.execute(query)
            records = cur.fetchall()
            
            #get column
            columns = [desc[0] for desc in cur.description]

            #convert to json
            result_datas = []
            for record in records:
                data = {}
                for i in range(len(columns)):
                    if isinstance(record[i], datetime.datetime):
                        data[columns[i]] = record[i].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        data[columns[i]] = record[i]
                        
                result_datas.append(data)
            
            cur.close()
            conn.close()
            return result_datas
            
        except (Exception, psycopg2.DatabaseError) as error:
            cur.close()
            conn.close()
            return []
                
        finally:
            if conn is not None:
                conn.close()

    def update_data(self,table:str,json_data:list, primary_key:str="id"):
        #primary_key is empty
        if primary_key == "" or primary_key == None:
            primary_key = "id"
        
        if type(json_data) != list:
            raise Exception('Data must be a list')
        
        if len(json_data) == 0:
            raise Exception('Data must be not empty')
        
        
        conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)

        cur = conn.cursor()
        
         #get all column names without create_at and id
        query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name NOT IN ('id','create_at');"
        cur.execute(query)
        
        column_names = cur.fetchall()
        column_names = [column_name[0] for column_name in column_names]
        if column_names == []:
            raise Exception('Table not found')
        

        try:

            #update data
            for data in json_data:
                #check column_names in json_data
 
                #get all values
                values = ','.join(f"{column_name} = '{str(data[column_name])}'" for column_name in column_names if column_name != primary_key)
                
                query = f"UPDATE {table} SET {values} WHERE {primary_key} = {data[primary_key]}"
                # print(query)
                cur.execute(query)
   
            conn.commit()
            cur.close()
            conn.close()
            return True
            
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error : ", error)
            cur.close()
            conn.close()
            return False
                
        finally:
            if conn is not None:
                conn.close()
        
    def delete_data(self,table:str,key_values:list,delete_key:str):
        #primary_key is empty
        if delete_key == "" or delete_key == None:
            raise Exception('Delete key not found')
            
            
        conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)
    
        cur = conn.cursor()
        try:
            values = ','.join(str(key_value) for key_value in key_values)
            
            query = f"DELETE FROM {table} WHERE {delete_key} IN ({values})"
            
            print(values)

            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()
            return True
            
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error : ", error)
            cur.close()
            conn.close()
            return False
                
        finally:
            if conn is not None:
                conn.close()
                
   

# delete_data('chatbot_dialog',4)
# psql = PSQLConnect("localhost","marine_db","ubuntu","ubuntu")

# psql.update_data(
#     'chatbot_answer',
#     [
#         {
#     "id": -1,
#     "uuid": "a87c2b23-5756-4b35-866d-ab557a49ab6e",
#     "text": "test",
#     "dialog_id": 1,
#     "created_at": "",
#     "action_status": "insert"
#   }])
# results = psql.insert_data(
#     'chatbot_keyword',
#     [
#         {
#     "id": -1,
#     "uuid": "a87c2b23-5756-4b35-866d-ab557a49ab6e",
#     "text": "test",
#     "dialog_id": 1,
#     "created_at": "",
#     "action_status": "insert"
#   }])

# print(results)


# results =  psql.insert_data('chatbot_keyword',[{'text':'1331','dialog_id':6,'age':300},{'text':'312','dialog_id':8}])
# data = psql.get_data('chatbot_dialog')
# successed = psql.delete_data('chatbot_keyword',[2,3],delete_key="dialog_id")

# print(results)

    