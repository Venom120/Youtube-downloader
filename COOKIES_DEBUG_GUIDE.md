# Cookies Debug & Troubleshooting Guide

## Problem: Thumbnails Not Showing, "Sign in to confirm you're not a bot" Error

This happens when **cookies are not being found or loaded by the backend**.

## Step 1: Check Backend Logs for Cookies Status

### 🔍 Check Docker Logs

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# View backend logs (last 50 lines)
docker logs ytdownloader | tail -50

# Or follow logs in real-time
docker logs -f ytdownloader
```

**Look for these messages:**

✅ **Good** (cookies found):
```
[✓] Cookies file found: /app/cookies/cookies.txt (1234 bytes)
[✓] Using cookies for search: /app/cookies/cookies.txt
[✓] Using cookies for video info: /app/cookies/cookies.txt
[✓] Using cookies for download: /app/cookies/cookies.txt
```

❌ **Bad** (cookies NOT found):
```
[!] Cookies file NOT found: /app/cookies/cookies.txt
[!] yt-dlp will run WITHOUT authentication (guest mode)
[!] Some videos may be unavailable or blocked
```

---

## Step 2: Verify Cookies File Exists in Docker Container

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Check if cookies.txt exists in the container
docker exec ytdownloader ls -lah /app/cookies/

# Expected output:
# -rw------- 1 root root 1234 Mar  1 12:00 cookies.txt
```

If file doesn't exist, go to **Step 3**.

---

## Step 3: Upload Cookies to EC2

### 3A. From Windows (Local Machine)

```powershell
# Option 1: SCP upload (if you have cookies.txt locally)
scp D:\Github\Youtube-downloader\Android\Backend\cookies\cookies.txt ubuntu@YOUR_EC2_IP:/home/ubuntu/YTDownloader/Android/Backend/cookies/

# Option 2: Copy via SSH
scp ~/Downloads/cookies.txt ubuntu@YOUR_EC2_IP:/home/ubuntu/YTDownloader/Android/Backend/cookies/
```

### 3B. Verify Upload on EC2

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Check if file was uploaded
ls -lah /home/ubuntu/YTDownloader/Android/Backend/cookies/

# Check file size
stat /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt

# View first few lines (should start with "# Netscape HTTP Cookie File")
head -n 5 /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt
```

---

## Step 4: Verify Docker Volume Mount

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Navigate to docker-compose directory
cd /home/ubuntu/server-files

# Inspect the ytdownloader service volumes
docker-compose config | grep -A 10 "ytdownloader:"

# Expected output should show:
# volumes:
#   - ytdownloader_cookies:/app/cookies
#   - ytdownloader_downloads:/app/downloads
```

---

## Step 5: Check Docker Volume Content

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# List contents of the Docker volume
docker volume inspect ytdownloader_cookies

# Expected output shows Mountpoint like:
# "Mountpoint": "/var/lib/docker/volumes/ytdownloader_cookies/_data"

# Check if cookies.txt is in the volume
sudo ls -lah /var/lib/docker/volumes/ytdownloader_cookies/_data/
```

If cookies.txt is NOT there, the volume mount may not be synced.

---

## Step 6: Manual Upload to Docker Volume

If the volume doesn't contain the cookies:

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Copy cookies directly to Docker volume
sudo cp /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt \
        /var/lib/docker/volumes/ytdownloader_cookies/_data/

# Verify copy
sudo ls -lah /var/lib/docker/volumes/ytdownloader_cookies/_data/

# Fix permissions
sudo chmod 644 /var/lib/docker/volumes/ytdownloader_cookies/_data/cookies.txt
sudo chown 1000:1000 /var/lib/docker/volumes/ytdownloader_cookies/_data/cookies.txt
```

---

## Step 7: Restart Docker Container

```bash
# SSH into EC2
ssh ubuntu@YOUR_EC2_IP

# Navigate to docker-compose directory
cd /home/ubuntu/server-files

# Restart the ytdownloader container
docker-compose restart ytdownloader

# Wait 5 seconds for it to start
sleep 5

# Check logs for cookies status
docker logs ytdownloader | grep -i "cookies"
```

---

## Step 8: Test Search Again

1. Go back to your mobile app
2. Search for a video
3. Check backend logs again:
   ```bash
   docker logs -f ytdownloader
   ```
4. Look for:
   - `[✓] Using cookies for search`
   - No "Sign in to confirm you're not a bot" errors

---

## Common Issues & Solutions

### Issue: "Sign in to confirm you're not a bot" Error Still Appearing

**Cause**: Cookies file exists but is invalid or expired

**Solution**:
1. Export fresh cookies from your browser
2. Make sure you used **Incognito/Private mode**
3. Make sure first line is: `# Netscape HTTP Cookie File`
4. Upload new cookies.txt to EC2
5. Restart container

### Issue: Cookies file exists but not being used

**Cause**: Docker volume not mounted properly

**Solution**:
```bash
# Stop containers
cd /home/ubuntu/server-files
docker-compose down

# Remove old volumes
docker volume rm ytdownloader_cookies

# Restart with fresh volume
docker-compose up -d

# Copy cookies to new volume
sudo cp /home/ubuntu/YTDownloader/Android/Backend/cookies/cookies.txt \
        /var/lib/docker/volumes/ytdownloader_cookies/_data/

# Restart
docker-compose restart ytdownloader
```

### Issue: "No Title Found" or Missing Metadata

**Cause**: Cookies work but yt-dlp needs JavaScript runtime

**Solution**: Install JavaScript runtime in Docker

Update Dockerfile:
```dockerfile
# Add after "apt-get install"
RUN apt-get install -y nodejs npm
```

Rebuild image:
```bash
cd /home/ubuntu/YTDownloader/Android/Backend
docker build -t ytdownloader-backend .
cd /home/ubuntu/server-files
docker-compose restart ytdownloader
```

---

## debug Checklist

- [ ] Backend logs show `[✓] Cookies file found`
- [ ] `docker exec ytdownloader ls /app/cookies/cookies.txt` shows file
- [ ] `docker volume inspect ytdownloader_cookies` shows volume path
- [ ] Cookies.txt first line is `# Netscape HTTP Cookie File`
- [ ] No "Sign in to confirm" errors in logs
- [ ] Container restarted after uploading cookies
- [ ] Search test returns thumbnail URLs

---

## Next Steps if Still Not Working

If cookies still aren't being used after all these steps:

1. **Export fresh cookies** - Your current cookies may have expired
2. **Use different video** - Try a non-age-restricted video first
3. **Check yt-dlp version** - Update: `pip install --upgrade yt-dlp`
4. **Check JavaScript runtime** - Install Node.js in Docker
5. **Ask for help** - Provide:
   - Output of `docker logs ytdownloader | tail -30`
   - Output of `ls -lah /var/lib/docker/volumes/ytdownloader_cookies/_data/`
   - Which video you're testing
