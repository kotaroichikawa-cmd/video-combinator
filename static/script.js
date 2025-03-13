document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const uploadForm = document.getElementById('upload-form');
    const hooksInput = document.getElementById('hooks');
    const middleInput = document.getElementById('middle_cta');
    const endInput = document.getElementById('end_cta');
    const musicInput = document.getElementById('bg_music');
    const volumeInput = document.getElementById('music_volume');
    const volumeDisplay = document.getElementById('volume-display');
    const submitBtn = document.getElementById('submit-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressStatus = document.getElementById('progress-status');
    const resultsContainer = document.getElementById('results-container');
    const resultsList = document.getElementById('results-list');
    const downloadAllBtn = document.getElementById('download-all-btn');
    
    // File selection display
    const hooksFiles = document.getElementById('hooks-files');
    const middleFiles = document.getElementById('middle-files');
    const endFiles = document.getElementById('end-files');
    const musicFiles = document.getElementById('music-files');
    
    // Update file selection displays
    hooksInput.addEventListener('change', function() {
        updateFileDisplay(this, hooksFiles);
    });
    
    middleInput.addEventListener('change', function() {
        updateFileDisplay(this, middleFiles);
    });
    
    endInput.addEventListener('change', function() {
        updateFileDisplay(this, endFiles);
    });
    
    musicInput.addEventListener('change', function() {
        updateFileDisplay(this, musicFiles);
    });
    
    // Update volume display
    volumeInput.addEventListener('input', function() {
        const volumePercent = Math.round(this.value * 100);
        volumeDisplay.textContent = volumePercent + '%';
    });
    
    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate required fields
        if (!hooksInput.files.length || !middleInput.files.length) {
            alert('Please select at least one hook video and one middle/CTA video.');
            return;
        }
        
        // Disable submit button and show progress
        submitBtn.disabled = true;
        uploadForm.style.display = 'none';
        progressContainer.style.display = 'block';
        
        // Create FormData object
        const formData = new FormData(uploadForm);
        
        // Upload files
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Start processing and tracking progress
            const jobId = data.job_id;
            
            // Prepare data for processing
            const processingData = {
                hook_paths: Array.from(hooksInput.files).map(file => 
                    'uploads/' + encodeURIComponent(file.name)),
                middle_cta_paths: Array.from(middleInput.files).map(file => 
                    'uploads/' + encodeURIComponent(file.name)),
                end_cta_paths: endInput.files.length ? 
                    Array.from(endInput.files).map(file => 'uploads/' + encodeURIComponent(file.name)) : [],
                bg_music_paths: musicInput.files.length ? 
                    Array.from(musicInput.files).map(file => 'uploads/' + encodeURIComponent(file.name)) : [],
                music_volume: parseFloat(volumeInput.value)
            };
            
            // Start processing
            startProcessing(jobId);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while uploading files: ' + error.message);
            resetForm();
        });
    });
    
    // Function to update file display
    function updateFileDisplay(input, displayElement) {
        if (input.files.length === 0) {
            displayElement.textContent = 'No files selected';
            return;
        }
        
        let fileList = '';
        for (let i = 0; i < input.files.length; i++) {
            fileList += `<div>${input.files[i].name}</div>`;
        }
        
        displayElement.innerHTML = fileList;
    }
    
    // Function to start processing
    function startProcessing(jobId) {
        // Update status
        progressStatus.textContent = 'Processing videos...';
        
        // Send processing request - no need to send file paths as they're stored on the server
        fetch(`/process/${jobId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({}) // Empty body since we're using stored paths
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Job not found. Please try uploading the files again.');
                }
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Processing started:", data);
            
            // Update progress
            updateProgress(0, 'processing');
            
            // Start polling for progress updates
            pollProgress(jobId);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during processing: ' + error.message);
            resetForm();
        });
    }
    
    // Function to poll for progress updates
    function pollProgress(jobId) {
        setTimeout(() => {
            fetch(`/progress/${jobId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch progress');
                }
                return response.json();
            })
            .then(data => {
                // Update progress bar
                updateProgress(data.progress, data.status);
                
                // Check status
                if (data.status === 'processing') {
                    // Continue polling
                    pollProgress(jobId);
                } else if (data.status === 'complete') {
                    // Show results
                    showResults(jobId, data.output_files);
                } else if (data.status === 'error') {
                    // Show error
                    alert('An error occurred during processing: ' + (data.error || 'Unknown error'));
                    resetForm();
                }
            })
            .catch(error => {
                console.error('Error polling progress:', error);
                // Wait a bit longer before retrying in case of error
                setTimeout(() => pollProgress(jobId), 2000);
            });
        }, 1000); // Poll every second
    }
    
    // Function to update progress bar
    function updateProgress(percent, status) {
        progressBar.style.width = percent + '%';
        progressPercentage.textContent = percent + '%';
        
        if (status === 'complete') {
            progressStatus.textContent = 'Processing complete!';
        }
    }
    
    // Function to show results
    function showResults(jobId, outputFiles) {
        // Hide progress, show results
        progressContainer.style.display = 'none';
        resultsContainer.style.display = 'block';
        
        // Clear previous results
        resultsList.innerHTML = '';
        
        // Add each output file to the list
        outputFiles.forEach(filename => {
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = `/download/${jobId}/${filename}`;
            link.textContent = filename;
            link.setAttribute('download', '');
            li.appendChild(link);
            resultsList.appendChild(li);
        });
        
        // Set up download all button
        if (outputFiles.length > 0) {
            downloadAllBtn.style.display = 'inline-block';
            downloadAllBtn.onclick = function() {
                // Download all files as a zip
                window.location.href = `/download-all/${jobId}`;
            };
        } else {
            downloadAllBtn.style.display = 'none';
        }
        
        // Set up create more videos button
        const createMoreBtn = document.getElementById('create-more-btn');
        createMoreBtn.onclick = function() {
            // Reset the form and show it again
            resetForm();
            
            // Clear file inputs
            document.getElementById('hooks').value = '';
            document.getElementById('middle_cta').value = '';
            document.getElementById('end_cta').value = '';
            document.getElementById('bg_music').value = '';
            
            // Reset file selection displays
            document.getElementById('hooks-files').textContent = 'No files selected';
            document.getElementById('middle-files').textContent = 'No files selected';
            document.getElementById('end-files').textContent = 'No files selected';
            document.getElementById('music-files').textContent = 'No files selected';
            
            // Reset volume slider
            document.getElementById('music_volume').value = 0.3;
            document.getElementById('volume-display').textContent = '30%';
        };
    }
    
    // Function to reset the form
    function resetForm() {
        submitBtn.disabled = false;
        uploadForm.style.display = 'block';
        progressContainer.style.display = 'none';
        resultsContainer.style.display = 'none';
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        progressStatus.textContent = 'Starting...';
    }
});
