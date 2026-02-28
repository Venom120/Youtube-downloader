# Quick Fix: "Sign in to confirm you're not a bot" Error

## The Problem

You're seeing this error even though cookies.txt exists:
```
ERROR: [youtube] WgTMeICssXY: Sign in to confirm you're not a bot
```

## Why This Happens

YouTube changed their bot detection in 2024. Even with valid cookies, you need:
1. ✅ Cookies in **Netscape format** (not JSON)
2. ✅ **Fresh cookies** (exported after logging in)
3. ✅ **iOS player client** configuration (most reliable)
4. ✅ **Deno** for JavaScript challenges

## Immediate Fix Steps

### Step 1: Export Fresh Cookies (CRITICAL)

**Your cookies may be:**
- In wrong format (JSON instead of Netscape)
- Expired (older than 30 days)
- Missing required authentication tokens

**Fix:**

1. **Install Chrome extension:**
   - Go to: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Click "Add to Chrome"

2. **Export cookies:**
   ```
   1. Go to https://youtube.com
   2. Log out completely
   3. Log back in
   4. Click the "Get cookies.txt LOCALLY" extension icon
   5. Click "Export"
   6. Save as cookies.txt
   ```

3. **Verify format:**
   ```bash
   # On your computer, check first line:
   head -1 cookies.txt
   # Should say: # Netscape HTTP Cookie File
   
   # If it says { or [ it's JSON - WRONG FORMAT!
   ```

### Step 2: Deploy Fresh Cookies

```bash
# On your computer:
scp -i your-key.pem cookies.txt ubuntu@your-ec2-ip:/tmp/cookies.txt

# SSH to server:
ssh -i your-key.pem ubuntu@your-ec2-ip

# Backup old cookies:
sudo mv /opt/docker-stack/cookies/cookies.txt /opt/docker-stack/cookies/cookies.txt.old

# Copy new cookies:
sudo cp /tmp/cookies.txt /opt/docker-stack/cookies/cookies.txt
sudo chmod 644 /opt/docker-stack/cookies/cookies.txt
sudo chown root:root /opt/docker-stack/cookies/cookies.txt

# Verify:
head -1 /opt/docker-stack/cookies/cookies.txt
# Should output: # Netscape HTTP Cookie File
```

### Step 3: Rebuild and Restart Backend

The new code has iOS player client enabled which is more reliable:

```bash
cd /home/ubuntu/YTDownloader/Android/Backend

# Rebuild image:
docker build -t ytdownloader-backend .

# Restart:
cd /opt/docker-stack
docker-compose down
docker-compose up -d

# Check logs:
docker logs -f ytdownloader
```

**You should see:**
```
========================================
COOKIE VALIDATION
========================================
[✓] Cookies file found: /app/cookies/cookies.txt (12218 bytes)
[✓] Cookie file format looks valid
========================================

========================================
JAVASCRIPT RUNTIME CHECK
========================================
[✓] Deno JavaScript runtime found:
    deno 2.7.1 (stable, release, x86_64-unknown-linux-gnu)
    v8 14.5.201.2-rusty
    typescript 5.9.2
========================================
```

### Step 4: Test Search

Try searching from mobile app or test in container:

```bash
# Test inside container:
docker exec -it ytdownloader bash

# Test yt-dlp directly:
yt-dlp --cookies /app/cookies/cookies.txt \
       --extractor-args "youtube:player_client=ios,web" \
       --dump-json "https://youtube.com/watch?v=dQw4w9WgXcQ" \
       | head -20

# If successful, you should see video JSON data
# If it fails, cookies are invalid
```

## What Changed in the Code

The fix adds:

1. **iOS Player Client** (most reliable with cookies):
   ```python
   "extractor_args": {
       "youtube": {
           "player_client": ["ios", "web"],
       }
   }
   ```

2. **Cookie Validation** at startup:
   - Checks file exists
   - Validates Netscape format
   - Shows clear error messages

3. **Better Error Messages**:
   - Explains cookie format requirements
   - Shows what to fix

## Still Not Working?

### Check 1: Cookie File Content

```bash
# View cookies (some data removed for security):
sudo cat /opt/docker-stack/cookies/cookies.txt | head -20
```

**Must have:**
- First line: `# Netscape HTTP Cookie File`
- Multiple lines with `.youtube.com` domain
- Tab-separated values (not spaces)
- Cookies named: `__Secure-3PSID`, `VISITOR_INFO1_LIVE`, `LOGIN_INFO`

### Check 2: Test with yt-dlp CLI

```bash
docker exec -it ytdownloader bash

# Try with iOS client:
yt-dlp --cookies /app/cookies/cookies.txt \
       --extractor-args "youtube:player_client=ios" \
       --get-title "https://youtube.com/watch?v=dQw4w9WgXcQ"

# If this works, your cookies are fine
# If this fails with same error, cookies are invalid
```

### Check 3: Cookie Expiry

YouTube cookies expire after ~30 days. Check when you last exported:

```bash
# Check file modification time:
stat /opt/docker-stack/cookies/cookies.txt

# If older than 30 days, definitely expired - export fresh ones
```

## Advanced: Using Browser Cookies Directly

If you have GUI access to the server (or use local Docker), you can skip the export step:

**In `ytdlp_service.py`, change:**
```python
# From:
if os.path.exists(COOKIES_FILE):
    ydl_opts["cookiefile"] = COOKIES_FILE

# To:
ydl_opts["cookiesfrombrowser"] = ("chrome", "Default")  # or "firefox"
```

This reads cookies directly from browser database (must be on same machine).

## Prevention: Automated Cookie Refresh

**Option 1: Manual monthly reminder**
- Set calendar reminder for 1st of each month
- Export fresh cookies
- Deploy to server

**Option 2: Automated script (advanced)**
- Use Playwright/Puppeteer to log in
- Extract cookies programmatically
- Update on server
- **Security risk:** Stores credentials

## Common Mistakes

❌ **Using Chrome's built-in cookie export**
- Only exports JSON format
- Use extension instead

❌ **Not logging in before export**
- Must be logged into YouTube
- Guest cookies won't work

❌ **Old cookies**
- YouTube expires sessions
- Export fresh every 30 days

❌ **Wrong file location**
- Must be exactly: `/opt/docker-stack/cookies/cookies.txt`
- Check docker-compose.yml volume mount

❌ **Wrong file permissions**
- Must be readable: `chmod 644`
- Check with: `ls -la /opt/docker-stack/cookies/`

## Verification Checklist

Before asking for help, verify:

- [ ] Cookies exported using browser extension (not Chrome's built-in)
- [ ] Exported AFTER logging into YouTube
- [ ] First line of file is: `# Netscape HTTP Cookie File`
- [ ] File contains `.youtube.com` cookies
- [ ] File is at: `/opt/docker-stack/cookies/cookies.txt`
- [ ] File permissions: `-rw-r--r--` (644)
- [ ] Docker container restarted after updating cookies
- [ ] Container logs show: `[✓] Cookie file format looks valid`
- [ ] Backend logs show `[✓] Using cookies for search`
- [ ] Cookies exported less than 30 days ago

## Success Indicators

After fixing, you should see:

**In container logs:**
```
[✓] Cookies file found: /app/cookies/cookies.txt (xxxxx bytes)
[✓] Cookie file format looks valid
[✓] Deno JavaScript runtime found
[✓] Using cookies for search: /app/cookies/cookies.txt
```

**No more errors:**
- ❌ "Sign in to confirm you're not a bot" → ✅ Videos load
- ❌ "No supported JavaScript runtime" → ✅ Deno found
- ❌ Empty thumbnails → ✅ Thumbnails display

**In mobile app:**
- Search returns results with thumbnails
- Video downloads work
- No authentication errors

## Need More Help?

If still not working after following ALL steps:

1. **Export completely fresh cookies** (log out, log in, export)
2. **Verify format** (check first line)
3. **Check container logs** for validation messages
4. **Test yt-dlp directly** in container
5. **Check YouTube account** (not suspended/limited)

Provide in support request:
- Container logs: `docker logs ytdownloader 2>&1 | tail -50`
- Cookie file first line: `head -1 /opt/docker-stack/cookies/cookies.txt`
- Cookie file age: `stat /opt/docker-stack/cookies/cookies.txt`
- yt-dlp test output: `docker exec ytdownloader yt-dlp --version`
