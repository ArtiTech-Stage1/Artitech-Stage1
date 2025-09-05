#!/usr/bin/env python3
"""
简单的HTTP服务器，用于提供前端静态文件
使用方法：python server.py
然后在浏览器中访问 http://localhost:3000
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    # 确保在正确的目录中
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"前端服务器启动在 http://localhost:{PORT}")
        print("请确保后端服务器已在 http://localhost:8000 运行")
        print("按 Ctrl+C 停止服务器")
        
        # 自动打开浏览器
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    main()
