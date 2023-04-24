from flask import Flask, jsonify, request
from waitress import serve


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/get', methods=['GET'])
def hello_world():
    return jsonify([{"id": 1, "name": "Draft"}, {"id": 2, "name": "Tester"}])


mode = "pro"


if __name__ == '__main__':
    if mode == "dev":
        app.run(host='0.0.0.0', port=50100, debug=True)
    else:
        serve(app, host='0.0.0.0', port=50100, threads=1)
