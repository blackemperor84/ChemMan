document.addEventListener('DOMContentLoaded', () => {
    console.log("manage_users.html: DOMContentLoaded - Skrypt załadowany.");
    
    // Przełączanie widoczności formularza edycji uprawnień
    document.querySelectorAll('.edit-permissions-btn').forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.dataset.userId;
            const form = document.getElementById(`edit-permissions-form-${userId}`);
            if (form) {
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
            }
        });
    });
    
    // Anulowanie edycji uprawnień
    document.querySelectorAll('.cancel-edit-permissions-btn').forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.dataset.userId;
            const form = document.getElementById(`edit-permissions-form-${userId}`);
            if (form) {
                form.style.display = 'none';
            }
        });
    });
    
    // Obsługa przycisku resetowania hasła
    const resetModal = document.getElementById('reset-password-modal');
    const deleteModal = document.getElementById('delete-user-modal');
    let currentUserId = null;
    
    // Przycisk resetowania hasła
    document.querySelectorAll('.reset-password-btn').forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.dataset.userId;
            const username = button.dataset.username;
            currentUserId = userId;
            
            document.getElementById('reset-username').textContent = username;
            resetModal.style.display = 'block';
        });
    });
    
    // Anuluj reset hasła
    document.getElementById('cancel-reset').addEventListener('click', () => {
        resetModal.style.display = 'none';
    });
    
    // Potwierdź reset hasła
    document.getElementById('confirm-reset').addEventListener('click', () => {
        if (currentUserId) {
            document.getElementById(`reset-password-form-${currentUserId}`).submit();
        }
    });
    
    // Przycisk usuwania użytkownika
    document.querySelectorAll('.delete-user-btn').forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.dataset.userId;
            const username = button.dataset.username;
            currentUserId = userId;
            
            document.getElementById('delete-username').textContent = username;
            deleteModal.style.display = 'block';
        });
    });
    
    // Anuluj usuwanie 
    document.getElementById('cancel-delete').addEventListener('click', () => {
        deleteModal.style.display = 'none';
    });
    
    // Potwierdź usuwanie
    document.getElementById('confirm-delete').addEventListener('click', () => {
        if (currentUserId) {
            document.getElementById(`delete-user-form-${currentUserId}`).submit();
        }
    });
    
    // Zamknij okno dialogowe po kliknięciu poza nim
    window.addEventListener('click', function(event) {
        if (event.target === resetModal) {
            resetModal.style.display = 'none';
        }
        if (event.target === deleteModal) {
            deleteModal.style.display = 'none';
        }
    });
});