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
