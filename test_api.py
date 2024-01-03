#create upload api server uisng flask

import os
import json
import zipfile
import pandas as pd
import psycopg2
import requests
from flask import Flask, jsonify, request, abort, make_response, render_template, send_from_directory
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename

from database import DatabaseConnect




app = Flask(__name__)
app.config["DEBUG"] = True

@app.route('/update_marine_tiles_db', methods=['POST'])
def update_marine_data():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    # If the user does not select a file, the browser submits an empty file without a filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'})


    #get table from request
    table_name = request.form.get('table_name')
    if table_name is None:
        return jsonify({'error': 'No table name'})
    
    #get sheet name from request
    sheet_name = request.form.get('sheet_name')
    if sheet_name is None:
        return jsonify({'error': 'No sheet name'})

    
    folder_name = 'datas'
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    
    # If the file is provided, save it to the 'datas' directory
    if file:
        save_path = os.path.join(folder_name, 'input.zip')
        app.logger.info(f'Saving file to {save_path}')
        file.save(save_path)
        
        # Unzip the file
        app.logger.info(f'Unzipping file...')
        with zipfile.ZipFile(save_path, 'r') as zip_ref:
            zip_ref.extractall(folder_name)
            
        # Delete the zip file
        app.logger.info(f'Deleting zip file...')
        os.remove(save_path)
        
        # find .xlsx file
        filename = None
        for f in os.listdir(folder_name):
            if f.endswith('.xlsx'):
                filename = f
                break
        
        if filename is None:
            return jsonify({'error': 'No .xlsx file found'})
        
        
        app.logger.info(f'{os.path.join("datas", filename)} to database...')
 
        is_success = DatabaseConnect.update_marine_tiles_db(os.path.join('datas', filename),table_name,sheet_name)
        
       
        if is_success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'failed'})
    
    return jsonify({'status': 'failed'})
 
    


# if __name__ == '__main__':
#     app.run(host='localhost', port=3000, debug=True)


datas =[
    {
        "article":"222222",
        "article_name":"222222"
    },
    {
        "article":"333333",
        "article_name":"test",
        "mc2":"กระเบื้อเซรามิค",
    }
]

df = pd.DataFrame(datas)

res = DatabaseConnect.insert_data('marine_tiles',df,'article')

print(res.to_dict(orient='records'))