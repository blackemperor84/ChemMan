/**
 * Pobiera token CSRF z meta tagu w <head>.
 * @returns {string|null} Wartość tokenu CSRF lub null, jeśli meta tag nie został znaleziony.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("locations.js: DOMContentLoaded - Skrypt załadowany.");
    const locationsList = document.getElementById('locations-list');
    console.log("locations.js: Znaleziono element #locations-list:", locationsList ? 'TAK' : 'NIE');

    // Sprawdź czy funkcja showToast jest dostępna (powinna być z base.js)
    if (typeof showToast !== 'function') {
        console.warn("Funkcja showToast nie jest zdefiniowana. Implementuję ją lokalnie.");
        // Implementacja funkcji showToast na wypadek, gdyby nie była załadowana z base.js
        window.showToast = function(message, type = 'info', duration = 3000) {
            // Znajdź kontener na alerty lub stwórz nowy jeśli nie istnieje
            let container = document.querySelector('.toast-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
            
            // Stwórz nowy alert
            const toast = document.createElement('div');
            toast.className = `toast-message ${type}`;
            toast.role = 'alert';
            
            // Wypełnij treścią
            toast.innerHTML = `
                <div class="toast-content">${message}</div>
                <button type="button" class="toast-close-btn">&times;</button>
            `;
            
            // Dodaj alert do kontenera
            container.appendChild(toast);
            
            // Dodaj klasę z timerem po dodaniu do DOM
            setTimeout(() => {
                toast.classList.add('with-timer');
            }, 10);
            
            // Obsługa automatycznego znikania
            const hideTimeout = setTimeout(() => {
                toast.classList.add('fade-out');
                setTimeout(() => {
                    if (toast && document.body.contains(toast)) {
                        toast.remove();
                    }
                }, 500);
            }, duration);
            
            // Obsługa przycisku zamknięcia
            const closeBtn = toast.querySelector('.toast-close-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    clearTimeout(hideTimeout);
                    toast.classList.add('fade-out');
                    setTimeout(() => {
                        if (toast && document.body.contains(toast)) {
                            toast.remove();
                        }
                    }, 500);
                });
            }
            
            return toast;
        };
    }


    if (locationsList) {
        locationsList.addEventListener('click', async (event) => {
            console.log("locations.js: Kliknięcie wewnątrz #locations-list.");
            const target = event.target; // Element, który został kliknięty

            // --- Obsługa kliknięcia "Usuń Lokalizację" ---
            if (target.classList.contains('delete-location-btn')) {
                console.log("locations.js: Kliknięto .delete-location-btn");
                const button = target;
                const locationId = button.dataset.locationId;
                const locationName = button.dataset.locationName || 'tej lokalizacji';

                if (!locationId) {
                    console.error("locations.js: Brak locationId w przycisku usuwania!");
                    showToast('Błąd wewnętrzny: Brak ID lokalizacji.', 'error');
                    return;
                }
                if (!confirm(`Czy na pewno chcesz usunąć lokalizację "${locationName}"?\nUWAGA: Usunięte zostaną również WSZYSTKIE substancje przypisane do tej lokalizacji!`)) {
                    console.log("locations.js: Anulowano usuwanie.");
                    return;
                }

                console.log(`locations.js: Próba usunięcia lokalizacji ID: ${locationId}`);
                try {
                    const apiUrl = `/location/${locationId}/delete`;
                    const csrfToken = getCsrfToken(); // Pobierz token
                    if (!csrfToken) {
                        showToast('Błąd bezpieczeństwa: Brak tokenu CSRF.', 'error');
                        return;
                    }

                    const response = await fetch(apiUrl, {
                        method: 'POST', // Serwer oczekuje POST dla tej akcji
                        headers: {
                            'Content-Type': 'application/json', // Mimo braku body, serwer może tego oczekiwać
                            'X-CSRFToken': csrfToken // <-- DODANY NAGŁÓWEK CSRF
                        }
                    });

                    const responseData = await response.json(); // Zakładamy, że zawsze jest JSON
                    console.log("Odpowiedź (usuwanie):", responseData);

                    if (!response.ok) {
                        throw new Error(responseData.message || `Błąd serwera: ${response.status}`);
                    }

                    showToast(responseData.message || `Lokalizacja "${locationName}" została usunięta.`, 'success', 2500);
                    setTimeout(() => { location.reload(); }, 1500);

                } catch (error) {
                    console.error("locations.js: Błąd podczas usuwania lokalizacji:", error);
                    showToast(`Wystąpił błąd podczas usuwania: ${error.message}`, 'error');
                }
                return;
            }

            // --- Obsługa kliknięcia "Edytuj" ---
            if (target.classList.contains('edit-location-btn')) {
                console.log("locations.js: Kliknięto .edit-location-btn");
                const locationId = target.dataset.locationId;
                const displaySpan = document.getElementById(`location-display-${locationId}`);
                const editSpan = document.getElementById(`location-edit-${locationId}`);
                const inputField = document.getElementById(`location-input-${locationId}`);
                const nameSpan = document.getElementById(`location-name-${locationId}`);

                if (displaySpan && editSpan && inputField && nameSpan) {
                    inputField.dataset.originalValue = nameSpan.textContent || inputField.value;
                    displaySpan.style.display = 'none';
                    editSpan.style.display = 'flex';
                    inputField.focus();
                    inputField.select();
                    console.log(`locations.js: Włączono edycję dla ID: ${locationId}`);
                } else {
                    console.error(`locations.js: Nie znaleziono elementów edycji dla ID: ${locationId}`);
                }
                return;
            }

            // --- Obsługa kliknięcia "Anuluj" ---
            if (target.classList.contains('cancel-location-btn')) {
                 console.log("locations.js: Kliknięto .cancel-location-btn");
                const locationId = target.dataset.locationId;
                const displaySpan = document.getElementById(`location-display-${locationId}`);
                const editSpan = document.getElementById(`location-edit-${locationId}`);
                const inputField = document.getElementById(`location-input-${locationId}`);

                if (displaySpan && editSpan && inputField) {
                    inputField.value = inputField.dataset.originalValue || '';
                    displaySpan.style.display = 'flex';
                    editSpan.style.display = 'none';
                    console.log(`locations.js: Anulowano edycję dla ID: ${locationId}`);
                } else {
                    console.error(`locations.js: Nie znaleziono elementów edycji (anuluj) dla ID: ${locationId}`);
                }
                return;
            }

            // --- Obsługa kliknięcia "Zapisz" ---
            if (target.classList.contains('save-location-btn')) {
                console.log("locations.js: Kliknięto .save-location-btn");
                const locationId = target.dataset.locationId;
                const inputField = document.getElementById(`location-input-${locationId}`);
                const nameSpan = document.getElementById(`location-name-${locationId}`);
                const displaySpan = document.getElementById(`location-display-${locationId}`);
                const editSpan = document.getElementById(`location-edit-${locationId}`);

                if (!inputField || !nameSpan || !displaySpan || !editSpan) {
                    console.error(`locations.js: Brak elementów do zapisu dla ID: ${locationId}`);
                    showToast('Błąd wewnętrzny: brak elementów formularza.', 'error');
                    return;
                }

                const newName = inputField.value.trim();
                if (!newName) {
                    showToast('Nazwa lokalizacji nie może być pusta.', 'error');
                    inputField.focus();
                    return;
                }
                if (newName === inputField.dataset.originalValue) {
                     console.log("locations.js: Nazwa bez zmian, anuluję wysłanie do serwera.");
                     editSpan.style.display = 'none';
                     displaySpan.style.display = 'flex';
                     return;
                }

                console.log(`locations.js: Zapisywanie nowej nazwy dla ID: ${locationId}, Nazwa: "${newName}"`);
                try {
                    const apiUrl = `/location/${locationId}/edit`;
                    const csrfToken = getCsrfToken(); // Pobierz token
                    if (!csrfToken) {
                        showToast('Błąd bezpieczeństwa: Brak tokenu CSRF.', 'error');
                        return;
                    }
                    const response = await fetch(apiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken // <-- DODANY NAGŁÓWEK CSRF
                         },
                        body: JSON.stringify({ name: newName })
                    });

                    const responseData = await response.json();
                    console.log("locations.js: Otrzymano odpowiedź z serwera (zapis):", responseData);

                    if (!response.ok) {
                        throw new Error(responseData.message || `Błąd serwera: ${response.status}`);
                    }

                    showToast(responseData.message || 'Nazwa zaktualizowana!', 'success');
                    nameSpan.textContent = responseData.new_name;
                    inputField.value = responseData.new_name;
                    inputField.dataset.originalValue = responseData.new_name;
                    editSpan.style.display = 'none';
                    displaySpan.style.display = 'flex';

                } catch (error) {
                    console.error("locations.js: Błąd podczas zapisywania nazwy lokalizacji:", error);
                    showToast(`Wystąpił błąd zapisu: ${error.message}`, 'error');
                }
                return;
            }

        });
    }
});