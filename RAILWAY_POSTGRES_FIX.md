# 🔧 URGENT FIX: Railway PostgreSQL Not Connecting

## Current Problem

Your logs show:
```
[DATABASE] DATABASE_URL exists: False
[DATABASE] ⚠️ WARNING: Using SQLite for local development
```

This means Railway is **NOT passing the DATABASE_URL** to your web service, even though you added it manually.

## Root Cause

Railway requires the PostgreSQL service to be **linked** to the web service, not just manually copying the variable. Manual variables don't get injected properly.

---

## ✅ SOLUTION: Link PostgreSQL Service to Web Service

### Step 1: Remove Manual DATABASE_URL Variable

1. Go to Railway dashboard
2. Click on your **web service** (social-listening-platform)
3. Go to **"Variables"** tab
4. Find `DATABASE_URL` variable
5. Click the **trash icon** to delete it
6. Click **"Save"** or it auto-saves

### Step 2: Link PostgreSQL Service

Railway has two ways to link services:

#### Option A: Using Service Variables (Recommended)

1. Click on your **web service**
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Click **"Add Reference"** (not "Add Variable")
5. Select your **PostgreSQL service** from dropdown
6. Select **`DATABASE_URL`** from the variable list
7. This creates a reference like: `${{Postgres.DATABASE_URL}}`

#### Option B: Using Railway CLI (Alternative)

```bash
# In your project directory
railway link

# Link the PostgreSQL service
railway service link postgres

# Verify variables
railway variables
```

### Step 3: Verify the Link

1. Go to your **web service**
2. Go to **"Variables"** tab
3. You should now see `DATABASE_URL` with a **chain link icon** 🔗
4. The value should show as a reference: `${{Postgres.DATABASE_URL}}`

### Step 4: Redeploy

Railway should auto-deploy when you change variables, but to be sure:

```bash
# Make a small change to trigger redeploy
cd twitter-scraper-app
echo "# Force redeploy" >> README.md
git add .
git commit -m "Force redeploy to test PostgreSQL connection"
git push
```

Or manually trigger:
1. Go to **"Deployments"** tab
2. Click **"Redeploy"** on latest deployment

### Step 5: Check Logs

After deployment completes (1-2 minutes):

1. Go to **"Deployments"** tab
2. Click on the latest deployment
3. Look for these lines in logs:

**✅ SUCCESS - You should see:**
```
[DATABASE] Checking for database connection...
[DATABASE] DATABASE_URL exists: True
[DATABASE] Using PostgreSQL database
[DATABASE] Connection string: postgresql://postgres:...
[DATABASE] ✓ Database engine created successfully
Database initialized successfully
```

**❌ FAILURE - If you still see:**
```
[DATABASE] DATABASE_URL exists: False
[DATABASE] ⚠️ WARNING: Using SQLite for local development
```

Then the link didn't work - proceed to troubleshooting below.

---

## 🔍 Troubleshooting

### Issue 1: PostgreSQL Service Doesn't Exist

**Check:**
1. Go to Railway project dashboard
2. Count the services - you should see **2 services**:
   - Your web app
   - PostgreSQL database

**If you only see 1 service:**
1. Click **"+ New"**
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Wait 30 seconds for provisioning
5. Then follow linking steps above

### Issue 2: Can't Find "Add Reference" Option

**Railway UI has changed:**
- Older UI: "Add Reference" button
- Newer UI: When adding variable, there's a dropdown to select "Service Variable"

**Steps for newer UI:**
1. Click **"+ New Variable"**
2. In the variable name field, type: `DATABASE_URL`
3. Look for a **dropdown or toggle** that says "Reference" or "Service Variable"
4. Select your PostgreSQL service
5. Select `DATABASE_URL` from that service

### Issue 3: Variable Shows But Still Not Working

**Check variable format:**
1. The variable should show as: `${{Postgres.DATABASE_URL}}`
2. NOT as a plain string: `postgresql://postgres:...`

**If it's a plain string:**
- Delete it
- Re-add using "Reference" method

### Issue 4: Multiple DATABASE_URL Variables

**Check for duplicates:**
1. Go to Variables tab
2. Look for multiple `DATABASE_URL` entries
3. Delete the manual one (plain string)
4. Keep only the referenced one (with 🔗 icon)

---

## 🧪 Verification

### Test 1: Health Check

```bash
curl https://social-listening-platform-production.up.railway.app/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "database": {
    "status": "connected",
    "type": "PostgreSQL",
    "url_set": true
  }
}
```

### Test 2: Create Schedule

1. Go to your app URL
2. Create a schedule
3. **Refresh the page**
4. Schedule should still be there ✅

### Test 3: Generate Report

1. Generate a quick scrape report
2. Go to "Report History" tab
3. Report should appear ✅
4. **Refresh the page**
5. Report should still be there ✅

---

## 📊 Understanding Railway's Variable System

Railway has 3 types of variables:

1. **Service Variables** (Auto-generated)
   - Created by Railway services (like PostgreSQL)
   - Example: `DATABASE_URL`, `PGHOST`, `PGPASSWORD`
   - Only visible in that service

2. **Referenced Variables** (What you need) 🔗
   - Links a variable from one service to another
   - Format: `${{ServiceName.VARIABLE_NAME}}`
   - Properly injected at runtime

3. **Manual Variables** (What you did - doesn't work)
   - Plain text values you type in
   - NOT connected to the actual service
   - Won't update if service changes

**You need #2 (Referenced Variables)!**

---

## 🚀 Alternative: Use Railway's Auto-Connect

Railway should auto-connect services in the same project. If linking isn't working:

### Check Service Names

1. Click on PostgreSQL service
2. Note the exact service name (might be "Postgres", "PostgreSQL", or custom)
3. When referencing, use exact name: `${{ExactServiceName.DATABASE_URL}}`

### Check Project Structure

1. Both services must be in the **same Railway project**
2. If they're in different projects, they can't link
3. Solution: Move them to same project or use public URL

---

## 📝 Quick Checklist

- [ ] PostgreSQL service exists in Railway project
- [ ] PostgreSQL service is running (green status)
- [ ] Removed manual DATABASE_URL from web service
- [ ] Added DATABASE_URL as **reference** to PostgreSQL service
- [ ] Variable shows with 🔗 chain link icon
- [ ] Triggered redeploy
- [ ] Checked logs for "Using PostgreSQL database"
- [ ] Tested /health endpoint shows PostgreSQL
- [ ] Tested schedule persistence after page refresh
- [ ] Tested report persistence after page refresh

---

## 🆘 Still Not Working?

If you've tried everything above and it's still not working:

### Last Resort: Use Public URL

1. Click on **PostgreSQL service**
2. Go to **"Connect"** tab
3. Copy the **"Public URL"** (not internal URL)
4. Go to **web service** → **"Variables"**
5. Add manual variable:
   - Name: `DATABASE_URL`
   - Value: (paste the public URL)
6. Redeploy

**Note:** Public URL is less secure and slower, but will work if linking fails.

---

## 📞 Need Help?

If none of this works, the issue might be:
- Railway platform bug
- Account permissions issue
- Service configuration problem

**Next steps:**
1. Check Railway status: https://status.railway.app/
2. Railway Discord: https://discord.gg/railway
3. Railway support: help@railway.app

**Provide them with:**
- Project ID
- Service names
- Screenshot of Variables tab
- Deployment logs showing SQLite warning
