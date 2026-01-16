# Schedule Update Summary

## What Changed

### 1. Start Date/Time Picker
- Added `datetime-local` input field for precise scheduling
- Shows in UTC timezone
- Automatically sets minimum to current time (can't schedule in the past)
- Defaults to 5 minutes from now for convenience

### 2. Validation
- Frontend validates that start time is in the future
- Backend validates the same before saving
- Clear error messages if validation fails

### 3. New "Once" Frequency Option
- Schedule a one-time scrape at a specific date/time
- Automatically disables after running
- Perfect for testing or one-off data collection

### 4. Enhanced Schedule Display
- Shows "Next run: In X minutes/hours/days"
- Color-coded countdown:
  - Green: Running soon (< 1 hour)
  - Blue: Running later today
  - Purple: Running in days
  - Orange: Pending execution
- Shows last run time
- Shows frequency type clearly

### 5. Database Schema Update
- Added `start_datetime` field (replaces old `time` field)
- Added `next_run` field for tracking
- Supports one-time schedules with `frequency='once'`

## How to Use

### Schedule a Scrape

1. Go to "Scheduled Scraping" tab
2. Enter Twitter handle and keywords
3. **Set Start Date & Time** (in UTC):
   - Click the datetime picker
   - Select date and time when you want the FIRST run
   - Must be in the future
4. Choose frequency:
   - **Once**: Runs one time only at the start date/time
   - **Hourly**: Runs every hour starting from the start time
   - **Daily**: Runs daily at the same time
   - **Weekly**: Runs weekly on the selected day
5. Click "Add Schedule"

### Example Scenarios

**Test immediately:**
- Set start time to 2-3 minutes from now
- Choose "Once" frequency
- Watch it run in a few minutes

**Daily morning report (India time):**
- Current time: 1:30 PM IST = 8:00 AM UTC
- Want to run at 9:00 AM IST tomorrow = 3:30 AM UTC tomorrow
- Set start datetime: Tomorrow at 03:30 UTC
- Choose "Daily" frequency

**Hourly data collection:**
- Set start time to next hour (e.g., 8:00 AM UTC)
- Choose "Hourly" frequency
- Will run at 8:00, 9:00, 10:00, etc.

## Time Zone Reference

**India (IST = UTC +5:30)**
- 12:00 PM IST = 06:30 AM UTC
- 1:00 PM IST = 07:30 AM UTC
- 2:00 PM IST = 08:30 AM UTC
- 9:00 AM IST = 03:30 AM UTC

**Quick conversion:** Subtract 5 hours 30 minutes from IST to get UTC

## Testing the Schedule

1. Create a schedule with start time 2-3 minutes from now
2. Choose "Once" frequency
3. Wait for the scheduled time
4. Check "Report History" tab - new report should appear
5. Refresh page - report should persist (tests PostgreSQL)

## Important Notes

- All times are in **UTC** (not your local time)
- The datetime picker shows UTC time
- Current UTC time is displayed at the top of the form
- Schedules persist across deployments (stored in PostgreSQL)
- One-time schedules auto-disable after running
- You can delete any schedule before it runs

## Migration from Old Schedules

Old schedules (with just time field) will need to be recreated with the new start_datetime field. The system will handle this gracefully by:
- Ignoring schedules without start_datetime
- Logging a warning in the console
- Not crashing or breaking

**Action:** Delete old schedules and recreate them with the new date/time picker.
