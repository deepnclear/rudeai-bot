# 🔧 Railway Deployment Troubleshooting Guide

## 🚨 **Common Issues & Solutions**

### 1. **Build Failures**

**Check Railway → Deployments → Build Logs**

#### Issue: `ModuleNotFoundError`
```bash
# Fix: Update requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements.txt"
git push
```

#### Issue: `Python version mismatch`
```bash
# Fix: Add runtime.txt
echo "python-3.11" > runtime.txt
git add runtime.txt
git commit -m "Specify Python version"
git push
```

---

### 2. **Environment Variable Issues**

**Check Railway → Variables**

#### Missing Variables Checklist:
- [ ] `OPENAI_API_KEY` (starts with `sk-proj-` or `sk-`)
- [ ] `TELEGRAM_BOT_TOKEN` (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
- [ ] `WEBHOOK_SECRET` (any long random string)
- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL` (auto-provided by PostgreSQL service)
- [ ] `PORT` (auto-provided by Railway)

#### Fix Missing Variables:
1. Go to Railway Dashboard
2. Click your project → Variables
3. Add missing variables
4. Redeploy (Railway auto-deploys on variable changes)

---

### 3. **Database Connection Errors**

#### Issue: `connection to server failed`
**Solutions:**
1. **Add PostgreSQL Service:**
   ```
   Railway Dashboard → + New → Database → PostgreSQL
   ```

2. **Check DATABASE_URL:**
   - Should be auto-provided
   - Format: `postgresql://user:pass@host:port/db`

3. **Test Connection:**
   ```bash
   # In Railway logs, look for:
   "Database tables created successfully"
   ```

#### Issue: `relation "users" does not exist`
**Solution:** Database tables not created
```python
# Tables are auto-created on startup
# Check logs for: "Database tables created successfully"
```

---

### 4. **Webhook Configuration Issues**

#### Issue: Telegram can't reach webhook
**Debug Steps:**

1. **Check Railway Domain:**
   ```bash
   # In Railway Dashboard → Settings → Domains
   # Should show: your-app-name-production-hash.up.railway.app
   ```

2. **Test Health Endpoint:**
   ```bash
   curl https://your-domain.up.railway.app/health
   # Should return: {"status": "healthy"}
   ```

3. **Check Telegram Webhook:**
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"
   ```

4. **Manual Webhook Setup:**
   ```bash
   curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://your-domain.up.railway.app/webhook/YOUR_SECRET"}'
   ```

---

### 5. **Application Startup Errors**

#### Issue: `Port binding failed`
**Solution:** Use Railway's PORT variable
```python
# In settings.py - should already be configured
PORT = int(os.environ.get("PORT", 8000))
```

#### Issue: `Address already in use`
**Solution:** Railway handles this automatically
- Don't specify PORT in environment variables
- Let Railway assign it automatically

#### Issue: `Timeout waiting for application`
**Solutions:**
1. **Check startup time** (should be < 60 seconds)
2. **Reduce startup complexity**
3. **Check health endpoint responds quickly**

---

## 🔍 **Step-by-Step Debugging Process**

### **Step 1: Check Build Status**
```bash
Railway Dashboard → Deployments
✅ Look for "Deployed" status
❌ If "Failed", check build logs
```

### **Step 2: Check Runtime Logs**
```bash
Railway Dashboard → Logs → Deploy
✅ Look for: "Webhook server is ready!"
❌ Look for error messages
```

### **Step 3: Test Health Endpoint**
```bash
curl https://your-domain.up.railway.app/health
✅ Should return 200 with health status
❌ If 503/404, app isn't running properly
```

### **Step 4: Test Telegram Webhook**
```bash
# Send message to your bot on Telegram
✅ Bot responds appropriately
❌ Check webhook logs in Railway
```

### **Step 5: Check Database Connection**
```bash
curl https://your-domain.up.railway.app/metrics
✅ Should show user/conversation counts
❌ Database connection issues
```

---

## 🚀 **Quick Fixes Checklist**

### **Immediate Actions:**
- [ ] Check all environment variables are set
- [ ] Verify PostgreSQL service is running
- [ ] Test health endpoint accessibility
- [ ] Check Railway deployment status
- [ ] Review recent logs for errors

### **Common Fix Commands:**
```bash
# Redeploy latest commit
git commit --allow-empty -m "Trigger redeploy"
git push

# Update requirements
pip freeze > requirements.txt
git add requirements.txt && git commit -m "Update deps" && git push

# Check webhook status
curl "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"
```

---

## 📊 **Health Check URLs**

Once deployed, test these endpoints:

```bash
# Basic health check
https://your-domain.up.railway.app/health

# Root endpoint
https://your-domain.up.railway.app/

# Metrics (basic stats)
https://your-domain.up.railway.app/metrics
```

---

## 🆘 **Last Resort Solutions**

### **Complete Redeployment:**
1. Delete Railway project
2. Create new Railway project
3. Deploy from GitHub again
4. Add PostgreSQL service
5. Set environment variables

### **Reset Telegram Webhook:**
```bash
# Delete current webhook
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/deleteWebhook"

# Wait 2 minutes, then set new one
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://NEW-DOMAIN.up.railway.app/webhook/YOUR_SECRET"}'
```

---

## 📞 **Getting Help**

**Railway Discord:** https://discord.gg/railway
**Railway Docs:** https://docs.railway.app

**This Project's Debug Script:**
```bash
python debug_railway.py
```