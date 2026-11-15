#!/usr/bin/env python3
"""
Test connection to local cTrader MCP Server on Windows PC (port 9876).
Run on Windows:
    python tools/test_ctrader_mcp.py
"""

import sys
import json
import urllib.request
import urllib.error

MCP_URL = "http://127.0.0.1:9876/mcp/"

def test_connection():
    print("=" * 60)
    print("🔍 Testing cTrader MCP Server Connection on Windows PC...")
    print(f"Target URL: {MCP_URL}")
    print("=" * 60)
    
    # 1. Test basic HTTP Reachability
    req = urllib.request.Request(
        MCP_URL,
        headers={"User-Agent": "cBot-MCP-Tester/1.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            headers = dict(response.getheaders())
            print(f"✅ Success! cTrader MCP server responded with HTTP {status}")
            print(f"Content-Type: {headers.get('Content-Type', 'N/A')}")
            return True
    except urllib.error.HTTPError as e:
        # Some MCP servers return 405 Method Not Allowed or 400 on GET, which still proves server is alive!
        print(f"✅ Server is ONLINE and listening (HTTP {e.code}: {e.reason})")
        print(f"Headers: {dict(e.headers)}")
        return True
    except urllib.error.URLError as e:
        print(f"❌ Connection Failed: {e.reason}")
        print("\n🛠️ วิธีแก้ไข (Troubleshooting):")
        print("1. ตรวจสอบว่าเปิด cTrader Desktop อยู่หรือไม่")
        print("2. ไปที่ cTrader Desktop -> Settings (รูปฟันเฟืองมุมซ้ายล่าง)")
        print("3. เลือกแท็บ 'MCP Server' แล้วติ๊กถูกที่ 'Enable MCP server'")
        print("4. ตรวจสอบว่าพอร์ตตั้งค่าเป็น 9876 หรือไม่")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
