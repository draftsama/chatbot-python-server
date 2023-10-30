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
            
            #check column_names in json_data
            for data in json_data:
                for column_name in column_names:
                    if column_name not in data.keys():
                        raise Exception(f'Column name {column_name} not found')
                    
            #get all column names
            column_names = ','.join(column_names)
            
            #get all values
            values = []
            for data in json_data:
                value = ','.join(f"'{str(data[column_name])}'" for column_name in data.keys())
                values.append(f"({value})")
                
            values = ','.join(values)
            
            query = f"INSERT INTO {table} ({column_names}) VALUES {values}"
            
            cur.execute(query)
            conn.commit()
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
        
        
        #check table exists
        try:

            
            for datas in json_data:
                if primary_key not in datas.keys():
                    raise Exception(f'Primary key {primary_key} not found')
                
                set_values=','.join(f"{column_name}='{datas[column_name]}'" for column_name in datas.keys() if column_name != primary_key)
                # print(query)
                query = f"UPDATE {table} SET {set_values} WHERE {primary_key}={datas[primary_key]}"

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
# psql.update_data('chatbot_keyword',[{'id':3,'text':'test1','dialog_id':2},{'id':4,'text':'test2','dialog_id':2}])

# successed =  psql.insert_data('chatbot_keyword',[{'text':'1331','dialog_id':3},{'text':'312','dialog_id':3}])
# data = psql.get_data('chatbot_dialog')
# successed = psql.delete_data('chatbot_keyword',[2,3],delete_key="dialog_id")

# print(successed)

    