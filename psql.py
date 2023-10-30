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
       
    
    def get_data(self,table:str,query:str=""):
        if query == None:
           query = ""
       
        conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password)

        cur = conn.cursor()
        
        try:
            query = f"SELECT * FROM {table} {query}"
            
            cur.execute(query)
            records = cur.fetchall()
            #get column 
            columns = [desc[0] for desc in cur.description]
            
            #convert to json
            datas = []
            for record in records:
                data = {}
                for i in range(len(columns)):
                    if isinstance(record[i], datetime.datetime):
                        data[columns[i]] = record[i].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        data[columns[i]] = record[i]
                        
                datas.append(data)
            
            cur.close()
            conn.close()
            
            return datas
        except (Exception, psycopg2.DatabaseError) as error:
            cur.close()
            conn.close()
                
        finally:
            if conn is not None:
                conn.close()
        

    def insert_data(self,table:str,json_data:list):
        
        if type(json_data) != list:
            raise Exception('Data must be a dictionary')
        
        exit()
        conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)

        cur = conn.cursor()
        
        try:
            
            #get all column names without create_at and id
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name NOT IN ('id','create_at');"
            cur.execute(query)
            
            column_names = cur.fetchall()
            column_names = [column_name[0] for column_name in column_names]
            if column_names == []:
                raise Exception('Table not found')
            
            #get values and keys from json_datas equal to column_names remove other keys and values
            values = ','.join( f"'{str(json_data[column_name])}'" for column_name in column_names)
            keys = ','.join(str(column_name) for column_name in column_names)

            query = f"INSERT INTO {table} ({keys}) VALUES ({values})"
            
            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()
            
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error : ", error)
            cur.close()
            conn.close()
                
        finally:
            if conn is not None:
                conn.close()

    def update_data(self,table:str,json_data:dict, primary_key:str="id"):
        #primary_key is empty
        if primary_key == "" or primary_key == None:
            primary_key = "id"
        
        if type(json_data) != dict:
            raise Exception('Data must be a dictionary')
        
        #check primary_key in json_data
        if primary_key not in json_data.keys():
            raise Exception('Primary key not found')
        
        conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password)

        cur = conn.cursor()
        
        #check table exists
        try:
            query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name NOT IN ('{primary_key}','create_at');"
            cur.execute(query)
            
            column_names = cur.fetchall()
            column_names = [column_name[0] for column_name in column_names]
            if column_names == []:
                raise Exception('Table not found')
            
            
            #get data from table by primary_key
            query = f"SELECT * FROM {table} WHERE {primary_key} = {json_data[primary_key]}"
            cur.execute(query)
            data = cur.fetchall()
        
            #if data not found raise exception
            if data == []:
                raise Exception('Data not found')
            
            
            values = ','.join( f"{column_name} = '{str(json_data[column_name])}'" for column_name in column_names)
            query = f"UPDATE {table} SET {values} WHERE {primary_key} = {json_data[primary_key]}"
            
            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()
            
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error : ", error)
            cur.close()
            conn.close()
                
        finally:
            if conn is not None:
                conn.close()
        
    def delete_data(self,table:str,primary_value:str,primary_key:str="id"):
        #primary_key is empty
        if primary_key == "" or primary_key == None:
            primary_key = "id"
            
            conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password)
        
            cur = conn.cursor()
            
            try:
                query = f"SELECT * FROM {table} WHERE {primary_key} = {primary_value}"
                cur.execute(query)
                data = cur.fetchall()
                
                if data == []:
                    raise Exception('Data not found')
                
                query = f"DELETE FROM {table} WHERE {primary_key} = {primary_value}"
                cur.execute(query)
                conn.commit()
                cur.close()
                conn.close()
                
            except (Exception, psycopg2.DatabaseError) as error:
                print("Error : ", error)
                cur.close()
                conn.close()
                    
            finally:
                if conn is not None:
                    conn.close()

# update_data('chatbot_dialog',{'id':5,'name':'1231sqd','age':20})
# delete_data('chatbot_dialog',4)
# psql = PSQLConnect("localhost","marine_db","ubuntu","ubuntu")
# psql.insert_data('chatbot_keyword',[{'text':'สวัสดี','dialog_id':1},{'text':'ดีจ้า','dialog_id':1}])
# data = psql.get_data('chatbot_dialog')

# print(data)

    