from flask import Flask, jsonify, request


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/get', methods=['GET'])
def hello_world():
    return jsonify([{"id": 1, "name": "Draft"}, {"id": 2, "name": "Tester"}])


if __name__ == '__main__':
    app.run(debug=True)
