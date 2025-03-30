 
// Main JavaScript for CSV Analyzer

// Check if file has been selected for upload
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const submitButton = document.querySelector('form button[type="submit"]');
    
    if (fileInput && submitButton) {
        // Initially disable the submit button
        submitButton.disabled = true;
        
        // Enable button only when a file is selected
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                submitButton.disabled = false;
                
                // Check file extension
                const fileName = fileInput.files[0].name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                
                if (fileExt !== 'csv') {
                    alert('Please select a CSV file.');
                    submitButton.disabled = true;
                    fileInput.value = '';
                }
            } else {
                submitButton.disabled = true;
            }
        });
    }
    
    // Handle histogram/pie chart selection to hide y-axis for these chart types
    const graphTypeSelect = document.getElementById('graph-type');
    const yColumnSelect = document.getElementById('y-column');
    const yColumnLabel = yColumnSelect ? yColumnSelect.previousElementSibling : null;
    
    if (graphTypeSelect && yColumnSelect && yColumnLabel) {
        graphTypeSelect.addEventListener('change', function() {
            if (graphTypeSelect.value === 'histogram') {
                yColumnSelect.disabled = true;
                yColumnLabel.classList.add('text-muted');
            } else {
                yColumnSelect.disabled = false;
                yColumnLabel.classList.remove('text-muted');
            }
        });
    }
    
    // Make graphs responsive
    window.addEventListener('resize', function() {
        const graphContainers = document.querySelectorAll('.graph-container');
        graphContainers.forEach(container => {
            if (container.firstChild) {
                Plotly.relayout(container.id, {
                    autosize: true
                });
            }
        });
    });
});

// Helper function to download graph as image
function downloadGraphImage(graphId, filename) {
    const graphElement = document.getElementById(graphId);
    if (!graphElement) return;
    
    Plotly.downloadImage(graphId, {
        format: 'png',
        width: 800,
        height: 600,
        filename: filename || 'graph'
    });
}