#!/usr/bin/env python3
"""
Test if cookies.txt file contains valid YouTube authentication.
Run this to diagnose cookie issues before using yt-dlp.
"""
import os
import sys
from datetime import datetime

COOKIES_FILE = os.getenv("COOKIES_FILE", "/app/cookies/cookies.txt")

def test_cookies():
    print("\n" + "="*70)
    print("YouTube Cookies Authentication Test")
    print("="*70)
    
    if not os.path.exists(COOKIES_FILE):
        print(f"❌ Cookie file NOT found: {COOKIES_FILE}")
        return False
    
    print(f"✓ Cookie file found: {COOKIES_FILE}")
    print(f"  Size: {os.path.getsize(COOKIES_FILE)} bytes")
    
    try:
        with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    print(f"  Lines: {len(lines)}")
    
    # Parse cookies
    critical_cookies = {
        'SAPISID': 'Google API Session ID',
        'SSID': 'Secure Session ID', 
        '__Secure-1PSID': 'Primary Session ID (Secure)',
        '__Secure-3PSID': 'Third Party Session ID (Secure)',
        'CONSENT': 'Cookie Consent',
        'VISITOR_INFO1_LIVE': 'YouTube Visitor Info',
    }
    
    found_cookies = {}
    youtube_domains = []
    all_cookies = []
    expired_cookies = []
    
    now = int(datetime.now().timestamp())
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split('\t')
        if len(parts) < 7:
            continue
        
        domain = parts[0]
        expiry = parts[4]
        cookie_name = parts[5]
        cookie_value = parts[6]
        
        # Check if expired
        try:
            expiry_timestamp = int(expiry)
            if expiry_timestamp < now:
                expired_cookies.append((cookie_name, domain))
                continue
        except:
            pass
        
        # Track YouTube/Google cookies
        if 'youtube.com' in domain or 'google.com' in domain:
            if domain not in youtube_domains:
                youtube_domains.append(domain)
            all_cookies.append(cookie_name)
            
            if cookie_name in critical_cookies:
                found_cookies[cookie_name] = {
                    'domain': domain,
                    'value_length': len(cookie_value),
                    'expiry': expiry
                }
    
    print(f"\n📊 Cookie Statistics:")
    print(f"  Total valid cookies: {len(all_cookies)}")
    print(f"  YouTube/Google domains: {len(youtube_domains)}")
    print(f"  Expired cookies: {len(expired_cookies)}")
    
    if expired_cookies:
        print(f"  ⚠️  Expired: {', '.join(set(c[0] for c in expired_cookies[:5]))}")
    
    print(f"\n🔐 Critical Authentication Cookies:")
    all_found = True
    for cookie_name, description in critical_cookies.items():
        if cookie_name in found_cookies:
            info = found_cookies[cookie_name]
            expiry_date = datetime.fromtimestamp(int(info['expiry'])).strftime('%Y-%m-%d')
            print(f"  ✓ {cookie_name:25} ({description})")
            print(f"    Domain: {info['domain']}, Value length: {info['value_length']}, Expires: {expiry_date}")
        else:
            print(f"  ❌ {cookie_name:25} ({description}) - MISSING!")
            all_found = False
    
    print(f"\n📋 YouTube Domains Found:")
    for domain in youtube_domains[:5]:
        print(f"  - {domain}")
    if len(youtube_domains) > 5:
        print(f"  ... and {len(youtube_domains) - 5} more")
    
    print("\n" + "="*70)
    if not all_cookies:
        print("❌ RESULT: NO YouTube/Google cookies found!")
        print("   You must be LOGGED IN to YouTube when exporting cookies.")
        print("\n🔧 HOW TO FIX:")
        print("   1. Open YouTube in browser and LOG IN")
        print("   2. Install 'Get cookies.txt LOCALLY' extension")
        print("   3. Click extension icon on youtube.com")
        print("   4. Save as cookies.txt")
        return False
    
    elif not all_found:
        print("⚠️  RESULT: Cookie file exists but MISSING critical authentication cookies!")
        print("   Your cookies may be expired or incomplete.")
        print("\n🔧 HOW TO FIX:")
        print("   1. Make sure you're LOGGED IN to YouTube first")
        print("   2. Re-export cookies using 'Get cookies.txt LOCALLY'")
        print("   3. Replace the old cookies.txt file")
        return False
    
    else:
        print("✅ RESULT: All critical authentication cookies found!")
        print("   Your cookies should work with yt-dlp.")
        print("\n   If downloads still fail, cookies may be expired or flagged.")
        print("   Try re-exporting fresh cookies from your browser.")
        return True
    
    print("="*70 + "\n")

if __name__ == "__main__":
    success = test_cookies()
    sys.exit(0 if success else 1)
