from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/whoami', methods=['GET'])
def home():
    print("Got pinged. Receiveed a request.")
    return jsonify({"name": "BioAmp"})

if __name__ == '__main__':
    app.run(host='0.0.0.0')