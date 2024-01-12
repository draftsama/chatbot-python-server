import re
import ssl
from urllib.request import urlopen
import pandas as pd
import json
import psycopg2
# from psycopg2 import sql
from psycopg2.extras import execute_values

from sqlalchemy import create_engine
import sys


class DatabaseConnect:
    HOST = "localhost"
    DATABASE = "marine_db"
    USER = "ubuntu"
    PASSWORD = "ubuntu"
    # TILE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQUKmtWleDEeUOIUxm0y-mKf7q91DOaWtC2NO3bUYGoDyuS8tS9nRVsfk339lbN_g/pub?gid=1689578933&single=true&output=csv"

    tile_columns = [
    {
       'raw_key': 'Item Code',
        'sql_key': 'sku'
    },
    {
       'raw_key': 'Product Name',
        'sql_key': 'product_name'
    },
    {
       'raw_key': 'Indicator',
        'sql_key': 'indicator'
    },
    {
       'raw_key': 'Size',
        'sql_key': 'size'
    },
    {
       'raw_key': 'Brand',
        'sql_key': 'brand'
    },
    {
       'raw_key': 'Design',
        'sql_key': 'design'
    },
    {
       'raw_key': 'Type',
        'sql_key': 'type'
    },
    {
       'raw_key': 'Material',
        'sql_key': 'material'
    },
    {
       'raw_key': 'Surface',
        'sql_key': 'surface'
    },
    {
        'raw_key': 'Random',
        'sql_key': 'random'
    },
    {
       'raw_key': 'Pattern',
        'sql_key': 'pattern'
    },
    {
       'raw_key': 'Rectifiled',
        'sql_key': 'rectifiled'
    },
    {
       'raw_key': 'Product Detail',
        'sql_key': 'product_detail'
    },
    {
       'raw_key': 'Anti Slip',
        'sql_key': 'anti_slip'
    },
    {
       'raw_key': 'Size Package',
        'sql_key': 'size_package'
    },
    {
       'raw_key': 'Package',
        'sql_key': 'package'
    }
]
     
    @staticmethod
    def update_marine_tiles_db(path,table_name,sheet_name):
        
        df = None
        
        try:
            df = pd.read_excel(path, sheet_name=sheet_name)
        except Exception as e:
            return {'status': 'failed', 'message': str(e)}

        #filtering the columns raw key
        df = df.filter(items=[column['raw_key'] for column in DatabaseConnect.tile_columns])


        #droping the row if value in 'Item Code' is Nan
        df.dropna(subset=['Item Code'], inplace=True)

        #converting the 'Item Code' to string with no decimal
        df['Item Code'] = df['Item Code'].astype(int)
        

        #rename the columns
        df.rename(columns={column['raw_key']: column['sql_key'] for column in DatabaseConnect.tile_columns}, inplace=True)

        
        #analyzing the package column to get unit_per_box and sqm
        #sample form "บรรจุกล่องละ 4 แผ่นปูได้ 1.44 ตรม."
        df['unit_per_box']= ""
        df['sqm']= ""
        for index, row in df.iterrows():
                package = str(row['package'])
                if package is None or package == "":
                    continue
                

                #use regex to find all int and float type in text assign to array
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", package)
                if len(numbers) == 1:
                    #assign value to unit_per_box and sqm column
                    df.at[index, 'unit_per_box'] = str(numbers[0])
                elif len(numbers) == 2:
                    #assign value to unit_per_box and sqm column
                    df.at[index, 'unit_per_box'] = str(numbers[0])
                    df.at[index, 'sqm'] = str(numbers[1])

            

       
        # analyzing the random column to get random_count
        
        df['random_count'] = 0
        
        #mapping random to random_count if random use regex to find number type in text then get that number assign to random_count else assign 0
        df['random_count'] = df['random'].str.extract('(\d+)', expand=False).fillna(0).astype(int)
    

        conn = None
        
        try:
            conn = psycopg2.connect(
                host=DatabaseConnect.HOST,
                database=DatabaseConnect.DATABASE,
                user=DatabaseConnect.USER,
                password=DatabaseConnect.PASSWORD)
            engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)
            # dump dataframe to postgresql database table
            df.to_sql(table_name, engine, if_exists='replace', index=False)

            conn.close()
        
        except (Exception, psycopg2.DatabaseError) as error:
            return {'status': 'failed', 'message': error.message}

        return {'status': 'success', 'message': 'update success'}
            
    
    

    @staticmethod
    def get_data(query):

        conn = None
        dataframe = None
        # connect to postgresql database
        try:
            conn = psycopg2.connect(
                host=DatabaseConnect.HOST,
                database=DatabaseConnect.DATABASE,
                user=DatabaseConnect.USER,
                password=DatabaseConnect.PASSWORD)

            engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)

            # get all column names without create_at if not exists reture None
            dataframe = pd.read_sql(query, engine)

        except (Exception) as error:
            print("Error : ", error)

        if conn is not None:
            conn.close()
            print('Database connection closed.')

        return dataframe
    
    @staticmethod
    def insert_data(table:str, df:pd.DataFrame ,target_key:str):
        
        #target_key be must to NOT NULL and UNIQUE
        
        # connect to postgresql database
        with psycopg2.connect(
            host=DatabaseConnect.HOST,
            database=DatabaseConnect.DATABASE,
            user=DatabaseConnect.USER,
            password=DatabaseConnect.PASSWORD) as conn:

            with conn.cursor() as cur:
                #build the query
                
                #get all column names without
                query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"
                cur.execute(query)
                
                column_names = cur.fetchall()
                column_names = [column_name[0] for column_name in column_names]
                
                #if column_names is empty
                if column_names == []:
                    raise Exception('Table not found')
                
                # Prepare the insert query
                keys = [key for key in df.keys() if key in column_names]
                keys = ','.join(keys)
                
                if target_key is not None:
                    query = f"INSERT INTO {table} ({keys}) VALUES %s ON CONFLICT ({target_key}) DO UPDATE SET "
                    query += ','.join(f"{key} = EXCLUDED.{key}" for key in column_names)
                    query += " RETURNING *"
                else:
                    query = f"INSERT INTO {table} ({keys}) VALUES %s RETURNING *"

                #Prepare the values
                #if value is nan then replace to None
                df = df.where(pd.notnull(df), None)
                values = [tuple(row) for row in df.values]

                # Execute the query
                psycopg2.extras.execute_values(cur, query, values, template=None, page_size=100)
                conn.commit()

                # Fetch all the returned rows
                rows = cur.fetchall()

                # Convert the rows to a DataFrame
                result = pd.DataFrame(rows, columns=column_names)
                
                return result
            
            
    @staticmethod
    def update_data(table:str,df:pd.DataFrame, primary_key:str="id"):
        #primary_key is empty
        if primary_key == "" or primary_key == None:
            primary_key = "id"
        
        if type(df) != pd.DataFrame:
            raise Exception('Data must be a DataFrame')
        
        if df.empty:
            raise Exception('Data must be not empty')
        
        
        
        with psycopg2.connect(
                host=DatabaseConnect.HOST,
                database=DatabaseConnect.DATABASE,
                user=DatabaseConnect.USER,
                password=DatabaseConnect.PASSWORD) as conn:

            with conn.cursor() as cur:
        
                #get value of primary_key from df
                primary_key_values = df[primary_key].to_list()
                
                #get data from database where primary_key in primary_key_values
                query = f"SELECT * FROM {table} WHERE {primary_key} IN ({','.join(str(value) for value in primary_key_values)})"
                cur.execute(query)
                
                current_datas = cur.fetchall()
                current_datas = pd.DataFrame(current_datas)
                
                result_datas = []
                #update data by primary_key in df
                for index, row in df.iterrows():
                 
                    #check column_names in df
                    column_names = [column_name for column_name in df.columns if column_name != primary_key]
                    
                    #setup the keys
                    keys = ','.join(column_names)
                    
                    #setup values
                    #if value is string then add single quote 
                    #if value is null then replace to NULL
                    
                    values = ','.join(f"{column_name} = '{str(row[column_name])}'" if type(row[column_name]) == str else f"{column_name} = {row[column_name]}" if row[column_name] is not None else f"{column_name} = NULL" for column_name in column_names)                    
                    
                    #build the query to update and return that data
                    query = f"UPDATE {table} ({keys}) VALUES ({values}) WHERE {primary_key} = {row[primary_key]} RETURNING *"
                    cur.execute(query)
                    
                    conn.commit()
                    
                    # Fetch all the returned row
                    row_updated = cur.fetchall()
                    
                    #add to result_datas
                    result_datas.append(row_updated)
                    
                    
                # Convert the rows to a DataFrame
                result = pd.DataFrame(result_datas)
                
                return result
                    

                    
                    
                    
                    
                    
     
                    
               
                    
                
                

                
   
            
        
       