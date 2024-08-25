function initCKEditor(uploadUrl, csrfToken) {
    ClassicEditor
        .create(document.querySelector('#content'), {
            simpleUpload: {
                uploadUrl: uploadUrl,
                headers: {
                    'X-CSRF-TOKEN': csrfToken
                }
            }
        })
        .then(editor => {
            // Store the editor instance
            window.editor = editor;
        })
        .catch(error => {
            console.error(error);
        });

    document.getElementById('articleForm').addEventListener('submit', function(e) {
        e.preventDefault();
        // Update the hidden textarea with the editor content
        document.querySelector('#content').value = window.editor.getData();
        // Submit the form
        this.submit();
    });
}