let currentReportContent = '';

document.getElementById('scrapeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const keywords = document.getElementById('keywords').value.trim();
    
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
            body: JSON.stringify({ username, keywords })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store report content
            currentReportContent = data.report_content;
            
            // Show success
            document.getElementById('resultMessage').textContent = 
                `Found ${data.tweet_count} tweets from @${username}`;
            
            document.getElementById('downloadTxt').href = `/download/${data.report_file}`;
            document.getElementById('downloadJson').href = `/download/${data.json_file}`;
            
            resultsDiv.style.display = 'block';
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

// View Report Button
document.getElementById('viewReportBtn').addEventListener('click', () => {
    document.getElementById('reportContent').textContent = currentReportContent;
    document.getElementById('reportViewer').style.display = 'flex';
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
        
        // Load schedules if switching to schedule tab
        if (tabName === 'schedule') {
            loadSchedules();
        }
    });
});

// Schedule Form
document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('schedule-username').value.trim();
    const keywords = document.getElementById('schedule-keywords').value.trim();
    const frequency = document.getElementById('schedule-frequency').value;
    const time = document.getElementById('schedule-time').value;
    
    try {
        const response = await fetch('/schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, keywords, frequency, time })
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
        
        if (data.schedules.length === 0) {
            container.innerHTML = '<p style="color: #666;">No schedules yet. Add one above!</p>';
            return;
        }
        
        container.innerHTML = data.schedules.map(schedule => `
            <div class="schedule-item">
                <div class="schedule-info">
                    <strong>@${schedule.username}</strong>
                    ${schedule.keywords ? `<span style="color: #666;"> • Keywords: ${schedule.keywords.join(', ')}</span>` : ''}
                    <div class="schedule-meta">
                        ${schedule.frequency} at ${schedule.time}
                        ${schedule.last_run ? ` • Last run: ${new Date(schedule.last_run).toLocaleString()}` : ''}
                    </div>
                </div>
                <button class="btn-delete" onclick="deleteSchedule(${schedule.id})">Delete</button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading schedules:', error);
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
