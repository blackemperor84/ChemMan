document.addEventListener('DOMContentLoaded', function() {
    // Elementy UI
    const clearBtn = document.getElementById('clear-logs-btn');
    const modal = document.getElementById('clear-logs-modal');
    const cancelBtn = document.getElementById('cancel-clear');
    
    if (clearBtn) {
        // Otwórz okno dialogowe po kliknięciu przycisku
        clearBtn.addEventListener('click', function() {
            if (modal) {
                modal.style.display = 'block';
            }
        });
    }
    
    if (cancelBtn) {
        // Zamknij okno dialogowe po kliknięciu anuluj
        cancelBtn.addEventListener('click', function() {
            if (modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    // Zamknij okno dialogowe po kliknięciu poza nim
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});