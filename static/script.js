document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-button');
    const loading = document.getElementById('loading');
    const message = document.getElementById('message');

    if (!fileInput.files.length) {
        message.textContent = 'Por favor, selecciona un archivo .xlsx';
        message.className = 'message error';
        message.classList.remove('hidden');
        return;
    }

    // Mostrar spinner y deshabilitar botón
    loading.classList.remove('hidden');
    uploadButton.disabled = true;
    message.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Ocultar spinner
        loading.classList.add('hidden');
        uploadButton.disabled = false;

        // Mostrar mensaje
        if (response.ok) {
            message.textContent = result.message;
            message.className = 'message success';
        } else {
            message.textContent = result.error || 'Error al subir el archivo';
            message.className = 'message error';
        }
        message.classList.remove('hidden');

    } catch (error) {
        // Ocultar spinner
        loading.classList.add('hidden');
        uploadButton.disabled = false;

        // Mostrar error
        message.textContent = 'Error de conexión con el servidor';
        message.className = 'message error';
        message.classList.remove('hidden');
    }
});
