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

            get_columns_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'tiles' AND column_name != 'create_at' AND column_name != 'text_search';
    """

            cursor.execute(get_columns_query)
            column_names = cursor.fetchall()

            # convert tuple to list
            column_names = [i[0] for i in column_names]
            # Disable SSL certificate verification
            ssl._create_default_https_context = ssl._create_default_https_context = ssl._create_unverified_context
            # Use urlopen to read the CSV data.
            response = urlopen(DatabaseConnect.TILE_CSV_URL)

            df = pd.read_csv(response)

            # df = df.head(10)

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
            print('Database connection closed.')

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
