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
    
    if (e.target.value === 'weekly') {
        daySelector.style.display = 'block';
    } else {
        daySelector.style.display = 'none';
    }
});

// Set minimum datetime to current time on page load
document.addEventListener('DOMContentLoaded', () => {
    const datetimeInput = document.getElementById('schedule-start-datetime');
    if (datetimeInput) {
        // Set min to current UTC time
        const now = new Date();
        const year = now.getUTCFullYear();
        const month = String(now.getUTCMonth() + 1).padStart(2, '0');
        const day = String(now.getUTCDate()).padStart(2, '0');
        const hours = String(now.getUTCHours()).padStart(2, '0');
        const minutes = String(now.getUTCMinutes()).padStart(2, '0');
        
        const minDatetime = `${year}-${month}-${day}T${hours}:${minutes}`;
        datetimeInput.min = minDatetime;
        
        // Set default to 5 minutes from now
        const defaultTime = new Date(now.getTime() + 5 * 60000);
        const defaultYear = defaultTime.getUTCFullYear();
        const defaultMonth = String(defaultTime.getUTCMonth() + 1).padStart(2, '0');
        const defaultDay = String(defaultTime.getUTCDate()).padStart(2, '0');
        const defaultHours = String(defaultTime.getUTCHours()).padStart(2, '0');
        const defaultMinutes = String(defaultTime.getUTCMinutes()).padStart(2, '0');
        
        datetimeInput.value = `${defaultYear}-${defaultMonth}-${defaultDay}T${defaultHours}:${defaultMinutes}`;
    }
});

// Schedule Form
document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('schedule-username').value.trim();
    const keywords = document.getElementById('schedule-keywords').value.trim();
    const frequency = document.getElementById('schedule-frequency').value;
    const startDatetime = document.getElementById('schedule-start-datetime').value;
    const day = document.getElementById('schedule-day').value;
    
    // Validate start datetime is in the future
    const startDate = new Date(startDatetime + 'Z'); // Add Z to indicate UTC
    const now = new Date();
    
    if (startDate <= now) {
        alert('⚠️ Start date/time must be in the future (UTC time)');
        return;
    }
    
    try {
        const response = await fetch('/schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username, 
                keywords, 
                frequency, 
                start_datetime: startDatetime,
                day 
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Schedule added successfully!');
            document.getElementById('scheduleForm').reset();
            // Reset datetime to default (5 minutes from now)
            const datetimeInput = document.getElementById('schedule-start-datetime');
            const defaultTime = new Date(new Date().getTime() + 5 * 60000);
            const year = defaultTime.getUTCFullYear();
            const month = String(defaultTime.getUTCMonth() + 1).padStart(2, '0');
            const day = String(defaultTime.getUTCDate()).padStart(2, '0');
            const hours = String(defaultTime.getUTCHours()).padStart(2, '0');
            const minutes = String(defaultTime.getUTCMinutes()).padStart(2, '0');
            datetimeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
            
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
            // Format frequency text
            let frequencyText = schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1);
            if (schedule.frequency === 'weekly' && schedule.day) {
                frequencyText = `Weekly on ${schedule.day.charAt(0).toUpperCase() + schedule.day.slice(1)}`;
            } else if (schedule.frequency === 'once') {
                frequencyText = 'One-time';
            }
            
            // Format start datetime
            let startDateText = '';
            if (schedule.start_datetime) {
                const startDate = new Date(schedule.start_datetime + 'Z');
                startDateText = startDate.toLocaleString('en-US', { 
                    timeZone: 'UTC',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                }) + ' UTC';
            }
            
            // Format next run time
            let nextRunText = '';
            if (schedule.next_run) {
                const nextRun = new Date(schedule.next_run + 'Z');
                const now = new Date();
                const diffMs = nextRun - now;
                const diffMins = Math.floor(diffMs / 60000);
                
                if (diffMins < 0) {
                    nextRunText = '<span style="color: #f39c12;">Pending...</span>';
                } else if (diffMins < 60) {
                    nextRunText = `<span style="color: #27ae60;">In ${diffMins} minute${diffMins !== 1 ? 's' : ''}</span>`;
                } else if (diffMins < 1440) {
                    const hours = Math.floor(diffMins / 60);
                    nextRunText = `<span style="color: #3498db;">In ${hours} hour${hours !== 1 ? 's' : ''}</span>`;
                } else {
                    const days = Math.floor(diffMins / 1440);
                    nextRunText = `<span style="color: #9b59b6;">In ${days} day${days !== 1 ? 's' : ''}</span>`;
                }
            } else if (schedule.start_datetime) {
                nextRunText = `<span style="color: #3498db;">First run: ${startDateText}</span>`;
            }
            
            // Format last run
            let lastRunText = schedule.last_run ? 
                `Last run: ${new Date(schedule.last_run + 'Z').toLocaleString('en-US', { timeZone: 'UTC' })} UTC` : 
                'Never run';
            
            const keywordsText = schedule.keywords && schedule.keywords.length > 0 ? 
                schedule.keywords.join(', ') : 
                'All tweets';
            
            return `
                <div class="schedule-item">
                    <div class="schedule-info">
                        <strong>@${schedule.username}</strong>
                        <span style="color: #666;"> • Keywords: ${keywordsText}</span>
                        <div class="schedule-meta">
                            📅 ${frequencyText}
                            <br>
                            ⏱️ Next run: ${nextRunText}
                            <br>
                            <small style="color: #999;">${lastRunText}</small>
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
    console.log('[REPORTS] Loading reports...');
    try {
        const response = await fetch('/reports');
        const data = await response.json();
        
        console.log('[REPORTS] Response:', data);
        console.log('[REPORTS] Total reports:', data.total);
        
        const container = document.getElementById('reports-container');
        
        if (!data.reports || data.reports.length === 0) {
            console.log('[REPORTS] No reports found');
            container.innerHTML = '<p style="color: #666;">No reports yet. Generate one in the Twitter or Reddit Scraping tabs!</p>';
            return;
        }
        
        console.log('[REPORTS] Rendering', data.reports.length, 'reports');
        
        container.innerHTML = data.reports.map(report => {
            const platform = report.platform || 'twitter';
            const platformIcon = platform === 'reddit' ? '🔍' : '🐦';
            const platformLabel = platform === 'reddit' ? 'Reddit' : 'Twitter';
            const usernamePrefix = platform === 'reddit' ? 'r/' : '@';
            
            return `
                <div class="report-item">
                    <div class="report-info">
                        <strong>${platformIcon} ${usernamePrefix}${report.username}</strong>
                        <span style="color: #999; font-size: 0.9em;"> • ${platformLabel}</span>
                        ${report.keywords && report.keywords.length > 0 ? `<span style="color: #666;"> • Keywords: ${report.keywords.join(', ')}</span>` : ''}
                        <div class="report-meta">
                            ${report.tweet_count || 0} ${platform === 'reddit' ? 'posts' : 'tweets'}
                            ${report.account_type ? ` • ${report.account_type}` : ''}
                            ${report.lead_score ? ` • Lead Score: ${report.lead_score}/7` : ''}
                            <br>Generated: ${new Date(report.created_at).toLocaleString()}
                        </div>
                    </div>
                    <div class="report-actions">
                        <button class="btn-view" data-report-id="${report.id}">View</button>
                    </div>
                </div>
            `;
        }).join('');
        
        console.log('[REPORTS] HTML rendered, adding event listeners');
        
        // Add event listeners to view buttons
        document.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', async function() {
                const reportId = parseInt(this.getAttribute('data-report-id'));
                console.log('[REPORTS] Viewing report ID:', reportId);
                await viewStoredReport(reportId);
            });
        });
        
        console.log('[REPORTS] Load complete');
    } catch (error) {
        console.error('[REPORTS] Error loading reports:', error);
        document.getElementById('reports-container').innerHTML = 
            `<p style="color: #f44336;">Error loading reports: ${error.message}</p>`;
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


// Reddit Form Handler
document.getElementById('redditForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const subreddit = document.getElementById('subreddit').value.trim();
    const keywords = document.getElementById('reddit-keywords').value.trim();
    const timeFilter = document.getElementById('time-filter').value;
    const minKeywordMentions = document.getElementById('reddit-min-keyword-mentions').value;
    
    const submitBtn = document.getElementById('redditSubmitBtn');
    const btnText = document.getElementById('redditBtnText');
    const btnLoader = document.getElementById('redditBtnLoader');
    const resultsDiv = document.getElementById('reddit-results');
    const errorDiv = document.getElementById('reddit-error');
    
    // Hide previous results
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.textContent = 'Analyzing...';
    btnLoader.style.display = 'block';
    
    try {
        const response = await fetch('/scrape-reddit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                subreddit, 
                keywords,
                time_filter: timeFilter,
                min_keyword_mentions: minKeywordMentions ? parseInt(minKeywordMentions) : 1
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store report content
            currentReportContent = data.report_content;
            
            // Show success
            let message = `Found ${data.post_count} posts from r/${subreddit}`;
            
            document.getElementById('redditResultMessage').textContent = message;
            document.getElementById('redditDownloadTxt').href = `/download/${data.report_file}`;
            document.getElementById('redditDownloadJson').href = `/download/${data.json_file}`;
            
            resultsDiv.style.display = 'block';
        } else {
            // Show error
            document.getElementById('redditErrorMessage').textContent = data.error;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        document.getElementById('redditErrorMessage').textContent = 
            'Network error. Please check your connection and try again.';
        errorDiv.style.display = 'block';
    } finally {
        // Reset button
        submitBtn.disabled = false;
        btnText.textContent = 'Generate Report';
        btnLoader.style.display = 'none';
    }
});

// View Reddit Report Button
document.addEventListener('click', (e) => {
    if (e.target.id === 'viewRedditReportBtn' || e.target.closest('#viewRedditReportBtn')) {
        if (currentReportContent) {
            document.getElementById('reportContent').textContent = currentReportContent;
            document.getElementById('reportViewer').style.display = 'flex';
        }
    }
});


// Account Discovery
let discoveredAccounts = [];
let selectedAccounts = new Set();

document.getElementById('discoverForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const keywords = document.getElementById('discover-keywords').value.trim();
    const maxResults = document.getElementById('discover-max-results').value;
    
    const submitBtn = document.getElementById('discoverBtn');
    const btnText = document.getElementById('discoverBtnText');
    const btnLoader = document.getElementById('discoverBtnLoader');
    const resultsDiv = document.getElementById('discovery-results');
    const errorDiv = document.getElementById('discover-error');
    
    // Hide previous results
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    document.getElementById('bulk-results').style.display = 'none';
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.textContent = '🔍 Searching...';
    btnLoader.style.display = 'block';
    
    try {
        const response = await fetch('/discover-accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords, max_results: parseInt(maxResults) })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            discoveredAccounts = data.accounts;
            selectedAccounts.clear();
            
            displayDiscoveredAccounts(data.accounts);
            
            document.getElementById('accounts-count').textContent = 
                `${data.total_accounts} account${data.total_accounts !== 1 ? 's' : ''} found`;
            
            resultsDiv.style.display = 'block';
        } else {
            document.getElementById('discoverErrorMessage').textContent = data.error;
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        document.getElementById('discoverErrorMessage').textContent = 
            'Network error. Please check your connection and try again.';
        errorDiv.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = '🔍 Discover Accounts';
        btnLoader.style.display = 'none';
    }
});

function displayDiscoveredAccounts(accounts) {
    const container = document.getElementById('accounts-container');
    
    if (accounts.length === 0) {
        container.innerHTML = '<p style="color: #666;">No accounts found. Try different keywords.</p>';
        return;
    }
    
    container.innerHTML = accounts.map(account => `
        <div class="account-card" data-username="${account.username}">
            <input type="checkbox" class="account-checkbox" data-username="${account.username}">
            <img src="${account.profile_image_url || 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'}" 
                 alt="${account.name}" class="account-avatar">
            <div class="account-info">
                <div class="account-name">
                    ${account.name}
                    ${account.verified ? '<span class="verified-badge">✓</span>' : ''}
                </div>
                <div class="account-username">@${account.username}</div>
                ${account.description ? `<div class="account-description">${account.description.substring(0, 150)}${account.description.length > 150 ? '...' : ''}</div>` : ''}
                <div class="account-stats">
                    <div class="account-stat">
                        <span>👥</span>
                        <strong>${formatNumber(account.followers_count)}</strong> followers
                    </div>
                    <div class="account-stat">
                        <span>📝</span>
                        <strong>${account.matching_tweets}</strong> matching tweets
                    </div>
                    ${account.location ? `<div class="account-stat"><span>📍</span>${account.location}</div>` : ''}
                </div>
            </div>
        </div>
    `).join('');
    
    // Add event listeners to checkboxes
    document.querySelectorAll('.account-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const username = this.getAttribute('data-username');
            const card = this.closest('.account-card');
            
            if (this.checked) {
                selectedAccounts.add(username);
                card.classList.add('selected');
            } else {
                selectedAccounts.delete(username);
                card.classList.remove('selected');
            }
            
            updateSelectedCount();
        });
    });
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function updateSelectedCount() {
    document.getElementById('selected-count').textContent = selectedAccounts.size;
    document.getElementById('bulk-scrape-btn').disabled = selectedAccounts.size === 0;
}

// Select/Deselect All
document.getElementById('select-all-accounts').addEventListener('click', () => {
    document.querySelectorAll('.account-checkbox').forEach(checkbox => {
        checkbox.checked = true;
        const username = checkbox.getAttribute('data-username');
        selectedAccounts.add(username);
        checkbox.closest('.account-card').classList.add('selected');
    });
    updateSelectedCount();
});

document.getElementById('deselect-all-accounts').addEventListener('click', () => {
    document.querySelectorAll('.account-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        const username = checkbox.getAttribute('data-username');
        selectedAccounts.delete(username);
        checkbox.closest('.account-card').classList.remove('selected');
    });
    updateSelectedCount();
});

// Bulk Scrape
document.getElementById('bulk-scrape-btn').addEventListener('click', async () => {
    if (selectedAccounts.size === 0) {
        alert('Please select at least one account');
        return;
    }
    
    const keywords = document.getElementById('discover-keywords').value.trim();
    const usernames = Array.from(selectedAccounts);
    
    const progressDiv = document.getElementById('bulk-progress');
    const resultsDiv = document.getElementById('bulk-results');
    const progressDetails = document.getElementById('bulk-progress-details');
    
    progressDiv.style.display = 'block';
    resultsDiv.style.display = 'none';
    progressDetails.innerHTML = '<p>Starting bulk scrape...</p>';
    
    try {
        const response = await fetch('/bulk-scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                usernames, 
                keywords,
                min_keyword_mentions: 1
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            progressDiv.style.display = 'none';
            
            // Show results
            document.getElementById('bulk-results-message').textContent = 
                `Successfully scraped ${data.successful} of ${data.total_processed} accounts`;
            
            let detailsHTML = '<div style="margin-top: 15px;">';
            
            // Successful scrapes
            if (data.results.length > 0) {
                detailsHTML += '<h4 style="color: #4caf50;">✓ Successful:</h4>';
                data.results.forEach(result => {
                    detailsHTML += `
                        <div class="bulk-progress-item success">
                            <strong>@${result.username}</strong>: ${result.tweet_count} tweets
                            ${result.account_type ? ` • ${result.account_type}` : ''}
                            ${result.lead_score ? ` • Lead Score: ${result.lead_score}/7` : ''}
                        </div>
                    `;
                });
            }
            
            // Errors
            if (data.errors.length > 0) {
                detailsHTML += '<h4 style="color: #f44336; margin-top: 15px;">✗ Failed:</h4>';
                data.errors.forEach(error => {
                    detailsHTML += `
                        <div class="bulk-progress-item error">
                            <strong>@${error.username}</strong>: ${error.error}
                        </div>
                    `;
                });
            }
            
            detailsHTML += '</div>';
            detailsHTML += '<p style="margin-top: 15px;"><a href="#" onclick="document.querySelector(\'[data-tab=\\\'history\\\']\').click(); return false;">View all reports in Report History →</a></p>';
            
            document.getElementById('bulk-results-details').innerHTML = detailsHTML;
            resultsDiv.style.display = 'block';
            
            // Clear selections
            selectedAccounts.clear();
            updateSelectedCount();
            document.querySelectorAll('.account-checkbox').forEach(cb => {
                cb.checked = false;
                cb.closest('.account-card').classList.remove('selected');
            });
        } else {
            progressDiv.style.display = 'none';
            alert('Error: ' + data.error);
        }
    } catch (error) {
        progressDiv.style.display = 'none';
        alert('Network error: ' + error.message);
    }
});
