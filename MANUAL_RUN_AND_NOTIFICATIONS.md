# Manual Run & Email Notifications Feature Summary

## What's New

Two powerful features have been added to improve schedule management and monitoring:

### 1. ▶️ Manual "Run Now" Button
Run any schedule on-demand without affecting its regular timing.

### 2. 📧 Email Notifications for Stale Schedules
Get automatic alerts when schedules haven't run for 2+ days.

---

## Feature 1: Manual "Run Now" Button

### What It Does
- Adds a green "▶️ Run Now" button next to each schedule
- Triggers the schedule immediately
- Does NOT affect the regular schedule timing
- Updates the "Last run" timestamp
- Saves report to database and deep_history

### Use Cases
- Test a schedule before waiting for the next run
- Manually collect data when needed
- Verify schedule configuration is working
- Get immediate results without creating a new quick scrape

### How to Use
1. Go to **Scheduled Scraping** tab
2. Find the schedule you want to run
3. Click the green **"▶️ Run Now"** button
4. Confirm the action
5. Wait for completion (button shows "⏳ Running...")
6. View success message with results
7. Optionally switch to Report History to see the new report

### Technical Details
- **Endpoint:** `POST /schedules/<schedule_id>/run`
- **Scrape Type:** Saved as `'manual'` in deep_history
- **Schedule Timing:** Next run time is NOT changed
- **Last Run:** Updated to current time
- **Report:** Saved to both `reports` and `deep_history` tables

---

## Feature 2: Email Notifications for Stale Schedules

### What It Does
- Checks all enabled schedules daily at midnight UTC
- Identifies schedules that haven't run for 2+ days
- Sends HTML email with detailed table
- Includes actionable troubleshooting steps

### Stale Schedule Criteria
A schedule is considered "stale" if:
- It's enabled AND
- Last run was 2+ days ago OR
- It was created 2+ days ago and never run

### Email Content
The alert email includes:
- **Subject:** ⚠️ Stale Schedule Alert - X Schedule(s) Not Running
- **Table:** Schedule ID, Username, Frequency, Last Run, Days Since Run
- **Action Items:** Troubleshooting checklist
- **Timestamp:** When the check was performed

### Setup Required

#### 1. Add Environment Variables to Railway
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=where_to_send_alerts@example.com
```

#### 2. Gmail Setup (Recommended)
1. Enable 2-Factor Authentication
2. Generate App Password at: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (not your regular password)

#### 3. Deploy to Railway
The `railway.toml` already includes the daily cron job:
```toml
[[crons]]
schedule = "0 0 * * *"  # Midnight UTC daily
command = "curl -X POST http://localhost:$PORT/cron/check-stale-schedules"
```

### Technical Details
- **Endpoint:** `POST /cron/check-stale-schedules`
- **Schedule:** Daily at 00:00 UTC (Railway Cron)
- **Email Format:** HTML with styled table
- **SMTP:** TLS encryption on port 587
- **Fallback:** Returns JSON with stale schedules if email fails

---

## UI Changes

### Schedule Item (Before)
```
┌─────────────────────────────────────────────────────┐
│ @elonmusk • Keywords: AI, technology                │
│ 📅 Daily                                            │
│ ⏱️ Next run: In 2 hours                            │
│ Last run: 2026-02-03 10:00 UTC                     │
│                                        [Delete]     │
└─────────────────────────────────────────────────────┘
```

### Schedule Item (After)
```
┌─────────────────────────────────────────────────────┐
│ @elonmusk • Keywords: AI, technology                │
│ 📅 Daily                                            │
│ ⏱️ Next run: In 2 hours                            │
│ Last run: 2026-02-03 10:00 UTC                     │
│                          [▶️ Run Now]  [Delete]    │
└─────────────────────────────────────────────────────┘
```

---

## Code Changes Summary

### Backend (app.py)
- **New Endpoint:** `/schedules/<schedule_id>/run` - Manual schedule execution
- **New Endpoint:** `/cron/check-stale-schedules` - Stale schedule checker
- **Email Logic:** SMTP integration with HTML email template
- **Error Handling:** Graceful fallback if email not configured

### Frontend (script.js)
- **New Function:** `runScheduleNow()` - Handles manual run button clicks
- **UI Updates:** Button loading states, success messages
- **Event Listeners:** Attached to all "Run Now" buttons

### Styling (style.css)
- **New Class:** `.schedule-actions` - Container for buttons
- **New Class:** `.btn-run-now` - Green button styling
- **States:** Hover, disabled, loading states

### Configuration (railway.toml)
- **New Cron:** Daily stale schedule check at midnight UTC

### Environment (.env.example)
- **New Variables:** SMTP configuration for email notifications

---

## Testing Checklist

### Manual Run Feature
- [ ] Click "Run Now" on a schedule
- [ ] Verify button shows loading state
- [ ] Confirm success message appears
- [ ] Check Report History for new report
- [ ] Verify "Last run" timestamp updated
- [ ] Confirm "Next run" time unchanged

### Email Notifications
- [ ] Add SMTP environment variables to Railway
- [ ] Create a test schedule
- [ ] Manually call `/cron/check-stale-schedules` endpoint
- [ ] Verify email received (if schedule is stale)
- [ ] Check email formatting and content
- [ ] Verify no email sent if no stale schedules

---

## Deployment Steps

1. **Commit Changes:**
   ```bash
   git add .
   git commit -m "Add manual run button and email notifications"
   git push
   ```

2. **Configure Email in Railway:**
   - Go to Railway dashboard
   - Navigate to your project
   - Add environment variables:
     - `SMTP_HOST`
     - `SMTP_PORT`
     - `SMTP_USER`
     - `SMTP_PASSWORD`
     - `NOTIFICATION_EMAIL`

3. **Deploy:**
   - Railway will auto-deploy on push
   - Verify deployment succeeds
   - Check cron jobs are active

4. **Test:**
   - Test manual run button
   - Manually trigger stale check endpoint
   - Verify email received

---

## Monitoring

### Check Cron Execution
```bash
# View Railway logs
railway logs

# Look for:
[CRON] Found X schedules to check
[STALE_CHECK] Found X stale schedule(s)
[STALE_CHECK] ✓ Email notification sent to ...
```

### Check Email Delivery
- Gmail: Check "Sent" folder of SMTP_USER account
- Recipient: Check inbox and spam folder
- Logs: Look for SMTP errors in Railway logs

### Manual Testing
```bash
# Test stale check endpoint
curl -X POST https://web-twitter-scraper.up.railway.app/cron/check-stale-schedules

# Test manual run
curl -X POST https://web-twitter-scraper.up.railway.app/schedules/1/run
```

---

## Troubleshooting

### "Run Now" Button Not Working
1. Check browser console for JavaScript errors
2. Verify schedule ID is valid
3. Check Railway logs for backend errors
4. Ensure schedule is enabled

### Email Not Sending
1. Verify environment variables are set
2. Check SMTP credentials (use app password for Gmail)
3. Review Railway logs for SMTP errors
4. Test with curl to isolate issue
5. Check spam folder

### Cron Not Running
1. Verify `railway.toml` is in project root
2. Check Railway dashboard for cron jobs
3. Manually trigger endpoint to test
4. Review Railway cron execution logs

---

## Future Enhancements

Potential improvements:
- [ ] Slack/Discord webhook notifications
- [ ] SMS alerts via Twilio
- [ ] Configurable alert thresholds
- [ ] Weekly summary emails
- [ ] Success notifications
- [ ] Batch manual run (run multiple schedules)
- [ ] Schedule pause/resume functionality
- [ ] Email templates customization

---

## Related Documentation

- `EMAIL_NOTIFICATIONS_SETUP.md` - Detailed email setup guide
- `RAILWAY_CRON_SETUP.md` - Railway cron configuration
- `API_ENDPOINTS.md` - Complete API reference
- `ROBUST_SCHEDULER.md` - Scheduler architecture

---

Last Updated: February 3, 2026
