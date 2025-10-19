# app.py - отдельный веб-сервер
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 NFT Bot is running on Render!"

@app.route('/health')
def health():
    return "✅ Bot is healthy"

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)