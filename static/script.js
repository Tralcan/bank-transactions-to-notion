document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const messageDiv = document.getElementById('message');
    
    if (!fileInput.files.length) {
        messageDiv.textContent = 'Por favor, selecciona un archivo.';
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            messageDiv.textContent = result.message;
            messageDiv.style.color = 'green';
        } else {
            messageDiv.textContent = result.error;
            messageDiv.style.color = 'red';
        }
    } catch (error) {
        messageDiv.textContent = 'Error al subir el archivo: ' + error.message;
        messageDiv.style.color = 'red';
    }
});