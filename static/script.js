document.getElementById('addMore').addEventListener('click', function() {
    const fileInputs = document.getElementById('fileInputs');
    const newFileInput = document.createElement('div');
    newFileInput.classList.add('fileInput');
    newFileInput.innerHTML = `
        <input type="file" name="files" accept=".xlsx,.xls,.pdf" required>
        <select name="tags" required>
            <option value="">Select Tag</option>
            <option value="TypeA">Type A (Excel)</option>
            <option value="TypeB">Type B (Excel)</option>
            <option value="TypeC">Type C (PDF)</option>
            <option value="TypeD">Type D (PDF)</option>
        </select>
    `;
    fileInputs.appendChild(newFileInput);
});


document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Display loading indicator
    document.getElementById('loading').style.display = 'block';
    document.getElementById('downloadLink').style.display = 'none'; // Hide previous download link

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        // Get the filename from the Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
        const filename = filenameMatch ? filenameMatch[1] : 'downloaded_file.xlsx'; // Default filename

        // Create a blob from the response
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        // Set the download link and display it
        const downloadLink = document.getElementById('downloadLink').querySelector('a');
        downloadLink.href = url;
        downloadLink.download = filename; // Set the filename for the download
        document.getElementById('downloadLink').style.display = 'block';

    } catch (error) {
        console.error('Error:', error);
        alert(`An error occurred: ${error.message}`); // User-friendly error message
    } finally {
        // Hide loading indicator
        document.getElementById('loading').style.display = 'none';
    }
});