let currentReportContent = '';

document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const keywords = document.getElementById('keywords').value.trim();
    const minKeywordMentions = document.getElementById('min-keyword-mentions').value;
    
    // Collect advanced filters
    const filters = {};
    const minLikes = document.getElementById('min-likes').value;
    const minRetweets = document.getElementById('min-retweets').value;
    const minReplies = document.getElementById('min-replies').value;
    
    if (minLikes) filters.min_likes = parseInt(minLikes);
    if (minRetweets) filters.min_retweets = parseInt(minRetweets);
    if (minReplies) filters.min_replies = parseInt(minReplies);
    
    filters.has_links = document.getElementById('has-links').checked;
    filters.has_media = document.getElementById('has-media').checked;
    filters.is_retweet = !document.getElementById('no-retweets').checked;
    
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    
    // Hide previous results
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnLoader.style.display = 'block';
    
    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                username, 
                keywords, 
                filters,
                min_keyword_mentions: minKeywordMentions ? parseInt(minKeywordMentions) : 1
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store report content
            currentReportContent = data.report_content;
            
            console.log('Report generated successfully');
            console.log('Report content length:', currentReportContent.length);
            
            // Show success with lead quality info
            let message = `Found ${data.tweet_count} tweets from @${username}`;
            if (data.account_type) {
                message += ` | Account Type: ${data.account_type}`;
            }
            if (data.lead_score) {
                message += ` | Lead Score: ${data.lead_score}/7`;
            }
            
            document.getElementById('resultMessage').textContent = message;
            
            document.getElementById('downloadTxt').href = `/download/${data.report_file}`;
            document.getElementById('downloadJson').href = `/download/${data.json_file}`;
            
            resultsDiv.style.display = 'block';
            
            // Verify button exists
            const viewBtn = document.getElementById('viewReportBtn');
            console.log('View Report button found:', viewBtn !== null);
        } else {
            // Show error
            document.getElementById('errorMessage').textContent = data.error;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        document.getElementById('errorMessage').textContent = 
            'Network error. Please check your connection and try again.';
        errorDiv.style.display = 'block';
    } finally {
        // Reset button
        submitBtn.disabled = false;
        btnText.textContent = 'Generate Report';
        btnLoader.style.display = 'none';
    }
});

// View Report Button (using event delegation since button is initially hidden)
document.addEventListener('click', (e) => {
    console.log('Click detected on:', e.target.id, e.target.className);
    if (e.target && e.target.id === 'viewReportBtn') {
        console.log('View Report clicked! Content length:', currentReportContent.length);
        document.getElementById('reportContent').textContent = currentReportContent;
        document.getElementById('reportViewer').style.display = 'flex';
    }
});

// Close Modal
document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('reportViewer').style.display = 'none';
});

// Close modal when clicking outside
document.getElementById('reportViewer').addEventListener('click', (e) => {
    if (e.target.id === 'reportViewer') {
        document.getElementById('reportViewer').style.display = 'none';
    }
});


// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update buttons
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Load data when switching tabs
        if (tabName === 'schedule') {
            loadSchedules();
        } else if (tabName === 'history') {
            loadReports();
        }
    });
});

// Load schedules on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load schedules if on schedule tab
    if (document.getElementById('schedule-tab').classList.contains('active')) {
        loadSchedules();
    }
});

// Show/hide day selector based on frequency
document.getElementById('schedule-frequency').addEventListener('change', (e) => {
    const daySelector = document.getElementById('day-selector');
    const timeSelector = document.getElementById('time-selector');
    
    if (e.target.value === 'weekly') {
        daySelector.style.display = 'block';
        timeSelector.style.display = 'block';
    } else if (e.target.value === 'hourly') {
        daySelector.style.display = 'none';
        timeSelector.style.display = 'none';
    } else {
        daySelector.style.display = 'none';
        timeSelector.style.display = 'block';
    }
});

// Schedule Form
document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('schedule-username').value.trim();
    const keywords = document.getElementById('schedule-keywords').value.trim();
    const frequency = document.getElementById('schedule-frequency').value;
    const time = document.getElementById('schedule-time').value;
    const day = document.getElementById('schedule-day').value;
    
    try {
        const response = await fetch('/schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, keywords, frequency, time, day })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Schedule added successfully!');
            document.getElementById('scheduleForm').reset();
            loadSchedules();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
});

// Load schedules
async function loadSchedules() {
    try {
        const response = await fetch('/schedules');
        const data = await response.json();
        
        const container = document.getElementById('schedules-container');
        const statusLabel = document.getElementById('schedule-status');
        
        if (data.schedules.length === 0) {
            container.innerHTML = '<p style="color: #666;">No schedules yet. Add one above!</p>';
            if (statusLabel) {
                statusLabel.textContent = 'No active schedules';
                statusLabel.className = 'status-label status-inactive';
            }
            return;
        }
        
        // Update status label
        if (statusLabel) {
            statusLabel.textContent = `${data.schedules.length} Active Schedule${data.schedules.length > 1 ? 's' : ''}`;
            statusLabel.className = 'status-label status-active';
        }
        
        container.innerHTML = data.schedules.map(schedule => {
            let scheduleText = schedule.frequency;
            if (schedule.frequency === 'weekly' && schedule.day) {
                scheduleText = `Weekly on ${schedule.day.charAt(0).toUpperCase() + schedule.day.slice(1)}`;
            }
            if (schedule.time && schedule.frequency !== 'hourly') {
                scheduleText += ` at ${schedule.time}`;
            }
            
            // Calculate next run time
            let nextRunText = '';
            if (schedule.last_run) {
                const lastRun = new Date(schedule.last_run);
                nextRunText = `Last run: ${lastRun.toLocaleString()}`;
            } else {
                nextRunText = 'Never run yet';
            }
            
            return `
                <div class="schedule-item">
                    <div class="schedule-info">
                        <strong>@${schedule.username}</strong>
                        ${schedule.keywords ? `<span style="color: #666;"> • Keywords: ${schedule.keywords.join(', ')}</span>` : ''}
                        <div class="schedule-meta">
                            📅 ${scheduleText}
                            <br>
                            ⏱️ ${nextRunText}
                        </div>
                    </div>
                    <button class="btn-delete" data-schedule-id="${schedule.id}">Delete</button>
                </div>
            `;
        }).join('');
        
        // Add event listeners to delete buttons
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', function() {
                const scheduleId = parseInt(this.getAttribute('data-schedule-id'));
                deleteSchedule(scheduleId);
            });
        });
    } catch (error) {
        console.error('Error loading schedules:', error);
        const container = document.getElementById('schedules-container');
        container.innerHTML = '<p style="color: #f44336;">Error loading schedules. Make sure PostgreSQL is set up.</p>';
        
        const statusLabel = document.getElementById('schedule-status');
        if (statusLabel) {
            statusLabel.textContent = 'Error loading schedules';
            statusLabel.className = 'status-label status-error';
        }
    }
}

// Delete schedule
async function deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    
    try {
        const response = await fetch(`/schedules/${scheduleId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('✓ Schedule deleted');
            loadSchedules();
        } else {
            alert('Error deleting schedule');
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}


// Load reports history
async function loadReports() {
    try {
        const response = await fetch('/reports');
        const data = await response.json();
        
        const container = document.getElementById('reports-container');
        
        if (!data.reports || data.reports.length === 0) {
            container.innerHTML = '<p style="color: #666;">No reports yet. Generate one in the Quick Scrape tab!</p>';
            return;
        }
        
        container.innerHTML = data.reports.map(report => `
            <div class="report-item">
                <div class="report-info">
                    <strong>@${report.username}</strong>
                    ${report.keywords ? `<span style="color: #666;"> • Keywords: ${report.keywords.join(', ')}</span>` : ''}
                    <div class="report-meta">
                        ${report.tweet_count} tweets • ${report.account_type || 'N/A'} • Lead Score: ${report.lead_score || 'N/A'}/7
                        <br>Generated: ${new Date(report.created_at).toLocaleString()}
                    </div>
                </div>
                <div class="report-actions">
                    <button class="btn-view" data-report-id="${report.id}">View</button>
                </div>
            </div>
        `).join('');
        
        // Add event listeners to view buttons
        document.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', async function() {
                const reportId = parseInt(this.getAttribute('data-report-id'));
                await viewStoredReport(reportId);
            });
        });
    } catch (error) {
        console.error('Error loading reports:', error);
        document.getElementById('reports-container').innerHTML = 
            '<p style="color: #f44336;">Error loading reports</p>';
    }
}

// View stored report
async function viewStoredReport(reportId) {
    try {
        const response = await fetch(`/reports/${reportId}`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('reportContent').textContent = data.report_content;
            document.getElementById('reportViewer').style.display = 'flex';
        } else {
            alert('Error loading report: ' + data.error);
        }
    } catch (error) {
        alert('Network error: ' + error.message);
    }
}

// Update tab switching to load reports
const originalTabSwitching = document.querySelectorAll('.tab-btn');
originalTabSwitching.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        if (tabName === 'history') {
            loadReports();
        }
    });
});


// Update timezone display
function updateTimeDisplay() {
    const now = new Date();
    
    // UTC time
    const utcTime = now.toUTCString().split(' ')[4]; // HH:MM:SS
    const utcElement = document.getElementById('utc-time');
    if (utcElement) {
        utcElement.textContent = utcTime;
    }
    
    // Local time
    const localTime = now.toLocaleTimeString();
    const localElement = document.getElementById('local-time');
    if (localElement) {
        localElement.textContent = localTime;
    }
}

// Update time every second
setInterval(updateTimeDisplay, 1000);
updateTimeDisplay(); // Initial call
