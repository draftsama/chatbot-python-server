import re
import ssl
from urllib.request import urlopen
import pandas as pd
import json
import psycopg2
from sqlalchemy import create_engine
import sys


class DatabaseConnect:
    HOST = "localhost"
    DATABASE = "marine_db"
    USER = "ubuntu"
    PASSWORD = "ubuntu"
    TILE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQUKmtWleDEeUOIUxm0y-mKf7q91DOaWtC2NO3bUYGoDyuS8tS9nRVsfk339lbN_g/pub?gid=1689578933&single=true&output=csv"

    @staticmethod
    def replace_tiles_db():

        conn = None
        table_name = "tiles"
        create_tiles_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
                sku int PRIMARY KEY,
                product_name VARCHAR(250),
                tile_size VARCHAR(100),
                type VARCHAR(100),
                material VARCHAR(100),
                surface VARCHAR(100),
                text_search VARCHAR(500),
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
        """

        # connect to postgresql database
        try:
            conn = psycopg2.connect(
                host=DatabaseConnect.HOST,
                database=DatabaseConnect.DATABASE,
                user=DatabaseConnect.USER,
                password=DatabaseConnect.PASSWORD)

            # check existing table
            cursor = conn.cursor()
            # select tiles table without column create_at and text_search
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name=%s)", (table_name,))

            table_exists = cursor.fetchone()[0]
            if not table_exists:
                # create table
                cursor.execute(create_tiles_table_query)
                conn.commit()
            # get all column names without create_at

            
            column_names =['sku','product_name','tile_size','type','material','surface','random','product_note','price_per_box','price_per_sqm']

            ssl._create_default_https_context = ssl._create_default_https_context = ssl._create_unverified_context
            # Use urlopen to read the CSV data.
            response = urlopen(DatabaseConnect.TILE_CSV_URL)

            df = pd.read_csv(response, usecols=column_names)


            
            # add random_count column
            df['random_count'] = 0
            #mapping random to random_count if random use regex to find number type in text then get that number assign to random_count else assign 0
            df['random_count'] = df['random'].str.extract('(\d+)', expand=False).fillna(0).astype(int)  
           
           #add unit_per_box column and sqm column
            df['unit_per_box'] = 0
            df['sqm'] = 0
             
            #get value from product note
            #example value: "บรรจุกล่องละ 4 แผ่นปูได้ 1.44 ตรม."
            for index, row in df.iterrows():
                product_note = row['product_note']
                #use regex to find all int and float type in text assign to array
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", product_note)
                #assign value to unit_per_box and sqm column
                df.at[index, 'unit_per_box'] = numbers[0]
                df.at[index, 'sqm'] = numbers[1]
    
                
            
            #drop random and product_note column
            df = df.drop(['random','product_note'], axis=1)
         
            # replace data into table
            engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)

            # dump dataframe to postgresql database table
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            # concat all column to text_search if value Nan or empty string replace to ''

            text_search = df['product_name'] + ' ' + df['tile_size'] + \
                ' ' + df['type'] + ' ' + df['material'] + ' ' + df['surface']
        
            

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        if conn is not None:
            conn.close()

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
    def insert_data(table, data):
        conn = None
        # connect to postgresql database
        try:
            conn = psycopg2.connect(
                host=DatabaseConnect.HOST,
                database=DatabaseConnect.DATABASE,
                user=DatabaseConnect.USER,
                password=DatabaseConnect.PASSWORD)

            engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)

            # get all column names without create_at if not exists reture None
            data.to_sql(table, engine, if_exists='append', index=False)
            
            

        except (Exception) as error:
            print("Error : ", error)

        if conn is not None:
            conn.close()
            print('Database connection closed.')


args = sys.argv
if __name__ == "__main__":
    if (len(args) < 2):
        print("Please input command")
        exit()
        
    
    order = args[1]
  
    
    if (order == '--update'):
        DatabaseConnect.replace_tiles_db()
        exit()

    if(len(args) < 3):
        print("Please input command")
        exit()
    
    text = args[2]
    if(order == '--tile-id'):
        # data = get_data(f"""
        #         SELECT *
        #         FROM tiles
        #         WHERE '{text}' % ANY(STRING_TO_ARRAY(text_search,' '))
        #         """)
        
         
        data = DatabaseConnect.get_data(f"""
                SELECT *
                FROM tiles
                WHERE sku = {text}
                """)

        print(data.to_json(orient='records', force_ascii=False))
        exit()


# be must to create >  CREATE EXTENSION pg_trgm;

# data = get_data("""
#                 SELECT *
#                 FROM tiles
#                 WHERE 'ซุปเปอร์' % ANY(STRING_TO_ARRAY(product_name,' ')
# """)


# data = get_data("SELECT * FROM tiles WHERE material = 'เซรามิค' LIMIT 10 ")
# print(data)
