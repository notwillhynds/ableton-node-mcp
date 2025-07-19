#!/usr/bin/env python3
"""
HTTP wrapper for MCP server functions
Provides HTTP API that CLI can call directly
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add MCP_Server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'MCP_Server'))
from server import AbletonConnection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AbletonHTTPWrapper")

class AbletonHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.ableton = AbletonConnection(host="localhost", port=9877)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_json_response(200, {"status": "ok"})
        else:
            self.send_json_response(404, {"error": "Endpoint not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/add_device':
                result = self.add_device(data)
                self.send_json_response(200, {"success": True, "result": result})
            else:
                self.send_json_response(404, {"error": "Endpoint not found"})
                
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            self.send_json_response(500, {"error": str(e)})
    
    def add_device(self, data):
        """Add device using existing MCP server logic"""
        track_index = data.get('track_index')
        device_name = data.get('device_name')
        category = data.get('category', 'audio_effects')
        
        if track_index is None or not device_name:
            raise ValueError("track_index and device_name required")
        
        # Map device names to URIs (simplified approach)
        device_uris = {
            'EQ Eight': 'query:Audio%20Effects#Ableton#EQ%20Eight',
            'Compressor': 'query:Audio%20Effects#Ableton#Compressor',
            'Reverb': 'query:Audio%20Effects#Ableton#Reverb',
            'Delay': 'query:Audio%20Effects#Ableton#Delay'
        }
        
        device_uri = device_uris.get(device_name)
        if not device_uri:
            # Try to construct URI from device name
            device_uri = f'query:Audio%20Effects#Ableton#{device_name.replace(" ", "%20")}'
        
        logger.info(f"Loading device {device_name} with URI {device_uri} on track {track_index}")
        
        return self.ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": device_uri
        })
    
    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Override to use logger"""
        logger.info(format % args)

def main():
    """Start the HTTP wrapper server"""
    port = 8080
    
    try:
        server = HTTPServer(('localhost', port), AbletonHandler)
        logger.info(f"Ableton HTTP wrapper starting on http://localhost:{port}")
        logger.info("Available endpoints:")
        logger.info("  GET  /health - Health check")
        logger.info("  POST /add_device - Add device to track")
        
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")

if __name__ == "__main__":
    main()