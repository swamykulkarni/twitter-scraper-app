# Email Notifications Setup Guide

## Overview

The Social Listening Platform now includes email notifications for stale schedules. If a schedule hasn't run for 2 or more days, you'll receive an automated email alert.

---

## Features

### 1. Manual "Run Now" Button
- Each schedule now has a green "▶️ Run Now" button
- Triggers the schedule immediately without affecting regular timing
- Shows loading state while running
- Displays success message with tweet count and lead score
- Updates the "Last run" timestamp
- Option to view the new report immediately

### 2. Stale Schedule Email Alerts
- Automatically checks for schedules that haven't run in 2+ days
- Sends HTML email with detailed table of stale schedules
- Runs daily at midnight UTC via Railway Cron
- Includes actionable troubleshooting steps

---

## Email Configuration

### Required Environment Variables

Add these to your Railway project environment variables:

```bash
# SMTP Server Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Email Credentials
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# Notification Recipient
NOTIFICATION_EMAIL=your_notification_email@example.com
```

### Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "Social Listening Platform"
   - Copy the 16-character password
3. **Add to Railway:**
   - `SMTP_USER`: your_email@gmail.com
   - `SMTP_PASSWORD`: the 16-character app password (no spaces)
   - `NOTIFICATION_EMAIL`: where you want to receive alerts

### Other Email Providers

**Outlook/Hotmail:**
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
```

**Yahoo:**
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your_email@yahoo.com
SMTP_PASSWORD=your_app_password
```

**Custom SMTP:**
```bash
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USER=your_username
SMTP_PASSWORD=your_password
```

---

## Railway Cron Configuration

The `railway.toml` file now includes two cron jobs:

```toml
# Run scheduled scrapes every hour
[[crons]]
schedule = "0 * * * *"
command = "curl -X POST http://localhost:$PORT/cron/run-schedules"

# Check for stale schedules daily at midnight UTC
[[crons]]
schedule = "0 0 * * *"
command = "curl -X POST http://localhost:$PORT/cron/check-stale-schedules"
```

---

## API Endpoints

### POST `/schedules/<schedule_id>/run`
Manually trigger a schedule to run immediately.

**Response:**
```json
{
  "success": true,
  "message": "Successfully scraped @elonmusk",
  "tweet_count": 42,
  "report_id": 126,
  "account_type": "Business",
  "lead_score": 7
}
```

### POST `/cron/check-stale-schedules`
Check for stale schedules and send email notification.

**Response (Email Configured):**
```json
{
  "success": true,
  "message": "Email notification sent for 2 stale schedule(s)",
  "stale_count": 2,
  "notification_sent_to": "your_email@example.com"
}
```

**Response (Email Not Configured):**
```json
{
  "success": false,
  "error": "Email configuration missing",
  "stale_count": 2,
  "stale_schedules": [
    {
      "id": 1,
      "username": "elonmusk",
      "last_run": "2026-01-30T12:00:00",
      "days_since_run": 4
    }
  ]
}
```

---

## Email Template

The stale schedule alert email includes:

- **Subject:** ⚠️ Stale Schedule Alert - X Schedule(s) Not Running
- **Content:**
  - Table with schedule details (ID, username, frequency, last run, days since run)
  - Action items for troubleshooting
  - Timestamp of the check

**Example Email:**

```
⚠️ Stale Schedule Alert

The following schedule(s) have not run for 2 or more days:

┌────┬──────────────┬───────────┬─────────────────────┬────────────────┐
│ ID │ Username     │ Frequency │ Last Run            │ Days Since Run │
├────┼──────────────┼───────────┼─────────────────────┼────────────────┤
│ 1  │ @elonmusk    │ daily     │ 2026-01-30 12:00 UTC│ 4              │
│ 2  │ @openai      │ hourly    │ Never               │ N/A            │
└────┴──────────────┴───────────┴─────────────────────┴────────────────┘

Action Required:
• Check if Railway Cron Jobs are running properly
• Verify the /cron/run-schedules endpoint is accessible
• Review Railway deployment logs for errors
• Consider manually running schedules using the "Run Now" button
```

---

## Testing

### Test Manual Run
1. Go to Scheduled Scraping tab
2. Click "▶️ Run Now" on any schedule
3. Confirm the action
4. Wait for completion (shows loading state)
5. Check Report History for the new report

### Test Email Notifications (Manual)
```bash
# Call the endpoint directly
curl -X POST https://web-twitter-scraper.up.railway.app/cron/check-stale-schedules
```

### Test Email Notifications (Automatic)
1. Create a schedule
2. Wait 2+ days without it running
3. Check your email at midnight UTC the next day

---

## Troubleshooting

### Email Not Sending

**Check 1: Environment Variables**
```bash
# Verify in Railway dashboard
echo $SMTP_USER
echo $SMTP_PASSWORD
echo $NOTIFICATION_EMAIL
```

**Check 2: SMTP Credentials**
- Gmail: Use App Password, not regular password
- Verify 2FA is enabled for Gmail
- Check for typos in email addresses

**Check 3: Firewall/Network**
- Railway should allow outbound SMTP connections
- Port 587 (TLS) is standard
- Port 465 (SSL) is alternative

**Check 4: Logs**
```bash
# Check Railway logs for errors
[STALE_CHECK] ✗ Failed to send email: ...
```

### Cron Not Running

**Check Railway Cron Status:**
1. Go to Railway dashboard
2. Navigate to your project
3. Check "Cron Jobs" tab
4. Verify both crons are listed and active

**Manual Test:**
```bash
# Test the endpoint directly
curl -X POST https://web-twitter-scraper.up.railway.app/cron/check-stale-schedules
```

### No Stale Schedules Detected

The system only alerts if:
- Schedule is enabled
- Last run was 2+ days ago OR
- Schedule was created 2+ days ago and never run

---

## Best Practices

1. **Use App Passwords:** Never use your main email password
2. **Separate Email:** Consider a dedicated email for notifications
3. **Test First:** Test email configuration before relying on it
4. **Monitor Logs:** Check Railway logs regularly
5. **Backup Monitoring:** Don't rely solely on email alerts

---

## Security Notes

- Email credentials are stored as environment variables (encrypted by Railway)
- Never commit email credentials to git
- Use app-specific passwords when possible
- Consider using a dedicated notification email account
- SMTP connections use TLS encryption (port 587)

---

## Future Enhancements

Potential improvements:
- Slack/Discord webhook notifications
- SMS alerts via Twilio
- Configurable alert thresholds (1 day, 3 days, etc.)
- Weekly summary emails
- Success notifications for completed scrapes
- Custom email templates

---

Last Updated: February 3, 2026
