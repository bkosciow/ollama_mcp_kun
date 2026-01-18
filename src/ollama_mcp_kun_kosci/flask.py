from flask import Flask, request, jsonify
from flask import request, abort

app = Flask(__name__)


def init_server(callback):
    @app.route('/chat', methods=['POST'])
    def webhook():

        return jsonify({"success": True}), 200

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({"status": "healthy"}), 200
