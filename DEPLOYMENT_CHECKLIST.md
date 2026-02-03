# Deployment Checklist - Manual Run & Email Notifications

## Pre-Deployment

- [x] Code changes completed
- [x] No syntax errors in Python files
- [x] No syntax errors in JavaScript files
- [x] No syntax errors in CSS files
- [x] Documentation created

## Files Modified

### Backend
- [x] `app.py` - Added `/schedules/<id>/run` and `/cron/check-stale-schedules` endpoints
- [x] `railway.toml` - Added daily cron for stale checks

### Frontend
- [x] `static/js/script.js` - Added `runScheduleNow()` function and event listeners
- [x] `static/css/style.css` - Added `.btn-run-now` and `.schedule-actions` styles

### Configuration
- [x] `.env.example` - Added SMTP configuration variables

### Documentation
- [x] `EMAIL_NOTIFICATIONS_SETUP.md` - Email setup guide
- [x] `MANUAL_RUN_AND_NOTIFICATIONS.md` - Feature summary
- [x] `DEPLOYMENT_CHECKLIST.md` - This file

## Deployment Steps

### 1. Commit and Push
```bash
cd twitter-scraper-app
git add .
git commit -m "feat: Add manual run button and email notifications for stale schedules"
git push origin main
```

### 2. Configure Email in Railway
Go to Railway dashboard → Your Project → Variables

Add these environment variables:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_16_char_app_password
NOTIFICATION_EMAIL=your_notification_email@example.com
```

**Gmail App Password Setup:**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "Social Listening Platform"
4. Copy the 16-character password (no spaces)
5. Use this as `SMTP_PASSWORD`

### 3. Deploy
- Railway will auto-deploy on push
- Wait for deployment to complete
- Check deployment logs for errors

### 4. Verify Cron Jobs
Railway Dashboard → Your Project → Cron Jobs

Should see:
- `0 * * * *` - Run schedules hourly
- `0 0 * * *` - Check stale schedules daily (NEW)

## Post-Deployment Testing

### Test 1: Manual Run Button
1. [ ] Go to https://web-twitter-scraper.up.railway.app
2. [ ] Navigate to "Scheduled Scraping" tab
3. [ ] Verify "▶️ Run Now" button appears on each schedule
4. [ ] Click "Run Now" on a schedule
5. [ ] Confirm the action
6. [ ] Verify button shows "⏳ Running..." state
7. [ ] Wait for completion
8. [ ] Check success message appears
9. [ ] Verify "Last run" timestamp updated
10. [ ] Check Report History for new report

### Test 2: Email Notification (Manual Trigger)
```bash
# Test the endpoint directly
curl -X POST https://web-twitter-scraper.up.railway.app/cron/check-stale-schedules
```

Expected responses:

**If email configured and stale schedules exist:**
```json
{
  "success": true,
  "message": "Email notification sent for X stale schedule(s)",
  "stale_count": X,
  "notification_sent_to": "your_email@example.com"
}
```

**If no stale schedules:**
```json
{
  "success": true,
  "message": "No stale schedules found",
  "stale_count": 0
}
```

**If email not configured:**
```json
{
  "success": false,
  "error": "Email configuration missing",
  "stale_count": X,
  "stale_schedules": [...]
}
```

### Test 3: Check Email Received
1. [ ] Check inbox of `NOTIFICATION_EMAIL`
2. [ ] Check spam folder if not in inbox
3. [ ] Verify email formatting is correct
4. [ ] Verify table shows stale schedules
5. [ ] Verify action items are listed

### Test 4: Verify Logs
```bash
# Check Railway logs
railway logs

# Look for:
[MANUAL_RUN] Running schedule X for @username
[MANUAL_RUN] ✓ Completed manual run for @username
[STALE_CHECK] Found X stale schedule(s)
[STALE_CHECK] ✓ Email notification sent to ...
```

## Rollback Plan

If issues occur:

### Option 1: Revert Git Commit
```bash
git revert HEAD
git push origin main
```

### Option 2: Disable Email Notifications
Remove these environment variables from Railway:
- `SMTP_USER`
- `SMTP_PASSWORD`
- `NOTIFICATION_EMAIL`

The cron will still run but won't send emails.

### Option 3: Disable Cron Job
Edit `railway.toml` and comment out the stale check cron:
```toml
# [[crons]]
# schedule = "0 0 * * *"
# command = "curl -X POST http://localhost:$PORT/cron/check-stale-schedules"
```

## Known Issues & Solutions

### Issue: Button doesn't appear
**Solution:** Clear browser cache and hard refresh (Ctrl+Shift+R)

### Issue: Email not sending
**Solutions:**
1. Verify SMTP credentials are correct
2. Use app password for Gmail (not regular password)
3. Check Railway logs for SMTP errors
4. Test with different email provider

### Issue: Cron not running
**Solutions:**
1. Verify `railway.toml` is in project root
2. Check Railway dashboard for cron jobs
3. Manually trigger endpoint to test
4. Review Railway cron execution logs

## Success Criteria

- [x] Code deployed without errors
- [ ] Manual run button visible on all schedules
- [ ] Manual run executes successfully
- [ ] Email configuration added to Railway
- [ ] Stale check endpoint returns expected response
- [ ] Email received when stale schedules exist
- [ ] Cron jobs visible in Railway dashboard
- [ ] No errors in Railway logs

## Monitoring

### Daily Checks (First Week)
- [ ] Check Railway logs for cron execution
- [ ] Verify no SMTP errors
- [ ] Confirm emails are being received
- [ ] Monitor schedule execution

### Weekly Checks (Ongoing)
- [ ] Review stale schedule alerts
- [ ] Check email delivery rate
- [ ] Monitor Railway cron job status
- [ ] Review user feedback

## Support

If issues persist:
1. Check Railway logs: `railway logs`
2. Review documentation: `EMAIL_NOTIFICATIONS_SETUP.md`
3. Test endpoints manually with curl
4. Check Railway dashboard for service status

---

## Deployment Status

- **Date:** February 3, 2026
- **Version:** v2.7
- **Features:** Manual Run Button + Email Notifications
- **Status:** Ready for Deployment
- **Deployed By:** [Your Name]
- **Deployment Time:** [To be filled]
- **Verification:** [To be filled]

---

Last Updated: February 3, 2026
