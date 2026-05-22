#!/usr/bin/env python3
"""
Dummy Flight Price Server
Runs on http://localhost:8000/api/flights/price/
Usage: python dummy_flight_price_server.py
"""

import random
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

MOCK_PRICES = {
    'del-bom': (3000, 7000),
    'blr-hyd': (1500, 4000),
    'del-blr': (4000, 9000),
    'bom-goa': (2000, 5000),
}


class FlightPriceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        
        # Check if the path is /api/flights/price/
        if parsed_url.path == '/api/flights/price/':
            # Parse query parameters
            query_params = parse_qs(parsed_url.query)
            route = query_params.get('route', [None])[0]
            
            if not route:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'Route parameter is required'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Normalize route to lowercase
            route_lower = route.lower()
            
            if route_lower not in MOCK_PRICES:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': f'Route "{route}" not found'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Generate random price within the range
            price_range = MOCK_PRICES[route_lower]
            price = random.randint(*price_range)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'route': route, 'price': price}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.client_address[0]}] {format % args}")


if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, FlightPriceHandler)
    print("🚀 Dummy Flight Price Server started on http://localhost:8000")
    print("📍 Endpoint: http://localhost:8000/api/flights/price/?route=del-bom")
    print("\nAvailable routes:")
    for route in MOCK_PRICES.keys():
        price_range = MOCK_PRICES[route]
        print(f"  - {route}: ₹{price_range[0]} - ₹{price_range[1]}")
    print("\nPress Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Server stopped")
        httpd.server_close()
