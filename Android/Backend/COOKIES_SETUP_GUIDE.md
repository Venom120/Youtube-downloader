# YouTube Cookies Setup Guide

## Why Cookies Are Needed

YouTube now requires authentication for many videos to prevent bot access. Cookies from your browser session allow yt-dlp to access YouTube as if you were logged in.

## ⚠️ IMPORTANT: Cookie Format

**yt-dlp ONLY accepts cookies in Netscape format** (also called Netscape HTTP Cookie File format).

❌ **This will NOT work:**
- Chrome's JSON cookie export
- Firefox's JSON cookie export  
- Raw cookie strings

✅ **This WILL work:**
- Netscape format `.txt` file (tab-separated values)

## Step-by-Step: Export Cookies

### Method 1: Using Browser Extension (Recommended)

#### For Chrome/Edge:
1. Install extension: **"Get cookies.txt LOCALLY"** by Rahul Shaw
   - Chrome Store: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. Go to https://youtube.com and **log in**

3. Click the extension icon → **"Export"**

4. Save the file as `cookies.txt`

#### For Firefox:
1. Install add-on: **"cookies.txt"** by Lennon Hill
   - Firefox Add-ons: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. Go to https://youtube.com and **log in**

3. Click the extension icon → Save cookies

4. Save the file as `cookies.txt`

### Method 2: Using yt-dlp Built-in (Alternative)

Instead of exporting cookies manually, you can tell yt-dlp to extract them directly from your browser:

```python
# In ytdlp_service.py, replace cookiefile with cookiesfrombrowser:
ydl_opts = {
    "cookiesfrombrowser": ("chrome",),  # or "firefox", "edge", "safari"
    # ... other options
}
```

**Note:** This only works if yt-dlp runs on the same machine as your browser.

## Deploy Cookies to Docker Container

Once you have `cookies.txt` in Netscape format:

### On EC2:

```bash
# 1. Copy cookies.txt to server
scp -i your-key.pem cookies.txt ubuntu@your-ec2-ip:/home/ubuntu/cookies.txt

# 2. SSH into server
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Copy to Docker volume mount location
sudo cp cookies.txt /opt/docker-stack/cookies/cookies.txt

# 4. Set permissions
sudo chmod 644 /opt/docker-stack/cookies/cookies.txt

# 5. Restart container
cd /opt/docker-stack
docker-compose down
docker-compose up -d

# 6. Check logs
docker logs ytdownloader
```

You should see:
```
========================================
COOKIE VALIDATION
========================================
[✓] Cookies file found: /app/cookies/cookies.txt (12218 bytes)
[✓] Cookie file format looks valid
========================================
```

## Verify Cookies Work

### Correct Netscape Format Example:
```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+cb.20210
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	abcd1234
.youtube.com	TRUE	/	TRUE	1234567890	__Secure-3PSIDCC	efgh5678
```

Format rules:
- First line: `# Netscape HTTP Cookie File`
- Each cookie line has **7 tab-separated fields**:
  1. Domain
  2. Flag (TRUE/FALSE)
  3. Path
  4. Secure (TRUE/FALSE)
  5. Expiration timestamp
  6. Cookie name
  7. Cookie value

### Test in Container:
```bash
# Access container shell
docker exec -it ytdownloader bash

# Check file exists
ls -lh /app/cookies/cookies.txt

# View first 5 lines
head -5 /app/cookies/cookies.txt

# Test with yt-dlp directly
yt-dlp --cookies /app/cookies/cookies.txt --dump-json "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

## Troubleshooting

### Error: "Sign in to confirm you're not a bot"

**Causes:**
1. Cookies are expired (YouTube sessions typically expire after 30 days)
2. Cookies are in wrong format (must be Netscape, not JSON)
3. Cookies don't include required authentication cookies

**Solutions:**

#### 1. Export Fresh Cookies
- Log out of YouTube and log back in
- Immediately export new cookies using browser extension
- Replace old cookies.txt file

#### 2. Check Cookie Format
```bash
# First line should be: # Netscape HTTP Cookie File
head -1 /opt/docker-stack/cookies/cookies.txt

# Should NOT be JSON:
head -1 /opt/docker-stack/cookies/cookies.txt | grep -q "{" && echo "WRONG FORMAT - This is JSON!"
```

#### 3. Check Important Cookies
Your cookies.txt should include these domains:
- `.youtube.com`
- `.google.com`

Important cookie names:
- `__Secure-3PSID`
- `__Secure-3PAPISID`
- `VISITOR_INFO1_LIVE`
- `LOGIN_INFO`
- `SSID`, `APISID`, `SAPISID`

```bash
# Check if important cookies exist:
grep -E "(PSID|LOGIN_INFO|VISITOR_INFO)" /opt/docker-stack/cookies/cookies.txt
```

### Error: "Cookie file may not be in Netscape format"

This means the file doesn't start with `# Netscape HTTP Cookie File` or doesn't have tab-separated values.

**Fix:**
1. Delete the current cookies.txt
2. Re-export using the browser extension method above
3. Make sure to use "Export" button in the extension, not Chrome's built-in cookie export

### Cookies Keep Expiring

YouTube cookies typically expire after **30 days**. You need to:
1. Set up automated cookie refresh (advanced)
2. Manually export fresh cookies monthly
3. Use `cookiesfrombrowser` option if the server has a browser installed

### Using cookiesfrombrowser Instead

If your server has a browser installed (e.g., headless Chrome), you can use:

```python
# In ytdlp_service.py:
ydl_opts = {
    "cookiesfrombrowser": ("chrome", "Default"),  # Browser name and profile
    # ... other options
}
```

This automatically reads cookies from the browser's cookie database.

## Security Note

⚠️ **IMPORTANT:** Cookie files contain your authentication session!

- **Never share** your cookies.txt file publicly
- **Never commit** cookies.txt to Git repositories
- **Add to .gitignore:**
  ```
  cookies.txt
  /cookies/
  ```
- **Use environment variables** or secrets management for production
- **Rotate cookies** regularly (every 30 days)

## Additional Resources

- yt-dlp Cookie Documentation: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp
- YouTube Cookie Guide: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies
- Browser Extension (Chrome): https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Browser Extension (Firefox): https://addons.mozilla.org/firefox/addon/cookies-txt/

## Summary

1. **Export cookies in Netscape format** using browser extension
2. **Copy to server** at `/opt/docker-stack/cookies/cookies.txt`
3. **Set permissions** to 644
4. **Restart backend** container
5. **Check logs** for validation messages
6. **Re-export every 30 days** when cookies expire

If issues persist after following these steps, check the main documentation or open an issue with:
- Backend container logs (`docker logs ytdownloader`)
- First 5 lines of cookies.txt (with sensitive data removed)
- Browser and OS version used for cookie export
