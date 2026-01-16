# Timezone Guide for Scheduled Scraping

## ⏰ Important: All Schedules Run in UTC

The platform uses **UTC (Coordinated Universal Time)** for all scheduled tasks.

## Why UTC?

- ✅ Consistent across all deployments
- ✅ No daylight saving time confusion
- ✅ Standard for server applications
- ✅ Works globally without ambiguity

## Converting Your Local Time to UTC

### Quick Reference Table

| Your Timezone | UTC Offset | Example: 9:00 AM Local → UTC |
|---------------|------------|------------------------------|
| **IST** (India) | UTC +5:30 | 9:00 AM IST = **3:30 AM UTC** |
| **PST** (US West) | UTC -8:00 | 9:00 AM PST = **5:00 PM UTC** |
| **EST** (US East) | UTC -5:00 | 9:00 AM EST = **2:00 PM UTC** |
| **GMT** (UK) | UTC +0:00 | 9:00 AM GMT = **9:00 AM UTC** |
| **CET** (Europe) | UTC +1:00 | 9:00 AM CET = **8:00 AM UTC** |
| **JST** (Japan) | UTC +9:00 | 9:00 AM JST = **12:00 AM UTC** (midnight) |
| **AEST** (Australia) | UTC +10:00 | 9:00 AM AEST = **11:00 PM UTC** (previous day) |

### Conversion Formula

**To convert TO UTC:**
- If your timezone is **ahead** of UTC (e.g., IST +5:30): **Subtract** the offset
- If your timezone is **behind** UTC (e.g., PST -8:00): **Add** the offset

**Examples:**

1. **India (IST = UTC +5:30)**
   - Want to run at 2:00 PM IST
   - 2:00 PM - 5:30 hours = 8:30 AM UTC
   - **Set schedule time: 08:30**

2. **California (PST = UTC -8:00)**
   - Want to run at 9:00 AM PST
   - 9:00 AM + 8 hours = 5:00 PM UTC (17:00)
   - **Set schedule time: 17:00**

3. **New York (EST = UTC -5:00)**
   - Want to run at 10:00 AM EST
   - 10:00 AM + 5 hours = 3:00 PM UTC (15:00)
   - **Set schedule time: 15:00**

## Using the Platform

### 1. Check Current Times

When you open the "Scheduled Scraping" tab, you'll see:
```
⏰ Timezone: All times are in UTC
Current UTC time: 14:30:45
Your local time: 8:00:45 PM IST
```

### 2. Calculate Your Schedule Time

**Example: You're in India and want daily scrapes at 9:00 AM IST**

1. Your timezone: IST (UTC +5:30)
2. Desired time: 9:00 AM IST
3. Convert to UTC: 9:00 AM - 5:30 = 3:30 AM UTC
4. **Enter in schedule: 03:30**

### 3. Verify Schedule

After creating a schedule, the platform shows:
```
📅 Daily at 03:30
⏱️ Last run: 2026-01-15 03:30:00 UTC
```

## Common Scheduling Scenarios

### Morning Reports (9:00 AM Local)

| Location | Local Time | UTC Time to Set |
|----------|------------|-----------------|
| Mumbai, India | 9:00 AM IST | **03:30** |
| London, UK | 9:00 AM GMT | **09:00** |
| New York, USA | 9:00 AM EST | **14:00** |
| Los Angeles, USA | 9:00 AM PST | **17:00** |
| Tokyo, Japan | 9:00 AM JST | **00:00** (midnight) |

### End of Business Day (6:00 PM Local)

| Location | Local Time | UTC Time to Set |
|----------|------------|-----------------|
| Mumbai, India | 6:00 PM IST | **12:30** |
| London, UK | 6:00 PM GMT | **18:00** |
| New York, USA | 6:00 PM EST | **23:00** |
| Los Angeles, USA | 6:00 PM PST | **02:00** (next day) |

## Online Conversion Tools

If you need help converting:
- https://www.timeanddate.com/worldclock/converter.html
- https://www.worldtimebuddy.com/
- Google: "9am IST to UTC"

## Daylight Saving Time (DST)

**Important:** UTC does NOT observe daylight saving time.

If your region uses DST:
- **During DST:** Your offset changes
- **Example:** PST (UTC -8) becomes PDT (UTC -7) in summer
- **Solution:** Update your schedules when DST changes

## Tips for Global Teams

1. **Use UTC for coordination** - Everyone sets schedules in UTC
2. **Document local times** - Note "Runs at 3:30 AM UTC (9:00 AM IST)"
3. **Set reminders** - Update schedules when DST changes
4. **Test first** - Create a test schedule to verify timing

## Troubleshooting

### "My schedule ran at the wrong time!"

1. **Check your conversion:**
   - Use an online converter
   - Verify your timezone offset
   - Account for DST if applicable

2. **Check the logs:**
   - Look at "Last run" timestamp
   - It shows UTC time
   - Convert to your local time to verify

3. **Verify server time:**
   - Visit `/health` endpoint
   - Check database timestamps

### "Schedule shows wrong last run time"

The "Last run" time is in UTC. Convert it to your local time:
- Last run: `2026-01-15 03:30:00 UTC`
- In IST: `2026-01-15 09:00:00 IST` (add 5:30 hours)

## Future Enhancement

We're considering adding:
- ✨ Timezone selector in UI
- ✨ Automatic conversion from local time
- ✨ Display times in user's timezone
- ✨ DST-aware scheduling

For now, use UTC and the conversion tables above!

---

**Quick Tip:** Bookmark a timezone converter and keep it handy when creating schedules! 🌍
