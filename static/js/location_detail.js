/**
 * Pobiera token CSRF z meta tagu w <head>.
 * @returns {string|null} Wartość tokenu CSRF lub null, jeśli meta tag nie został znaleziony.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("location_detail.js: DOMContentLoaded - Skrypt załadowany.");

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

    // Zmienne dot. uprawnień użytkownika (odczytane z atrybutów #substances-list)
    const substancesList = document.getElementById('substances-list');
    const canAdd = substancesList ? substancesList.getAttribute('data-can-add') === 'true' : false;
    const canEdit = substancesList ? substancesList.getAttribute('data-can-edit') === 'true' : false;
    const canDelete = substancesList ? substancesList.getAttribute('data-can-delete') === 'true' : false;
    const canMove = substancesList ? substancesList.getAttribute('data-can-move') === 'true' : false;
    const canCopy = substancesList ? substancesList.getAttribute('data-can-copy') === 'true' : false;
    const canUploadSds = substancesList ? substancesList.getAttribute('data-can-upload-sds') === 'true' : false;
    const isAdmin = substancesList ? substancesList.getAttribute('data-is-admin') === 'true' : false;

    console.log("Uprawnienia:", { canAdd, canEdit, canDelete, canMove, canCopy, canUploadSds, isAdmin });

    // === SEKCJA WYSZUKIWANIA Z EXCELA ===
    const searchInput = document.getElementById('search-query');
    const searchButton = document.getElementById('search-button');
    const searchResultsDiv = document.getElementById('search-results');
    const searchSectionDiv = document.querySelector('.search-section[data-location-id]');
    console.log("Elementy wyszukiwania Excel:", { searchInput, searchButton, searchResultsDiv, searchSectionDiv });

    if (searchInput && searchButton && searchResultsDiv && searchSectionDiv) {
        function displayResults(results) {
            console.log("Wywołano displayResults(). Wyników:", results ? results.length : 0);
            console.log("Pełne wyniki z Excela:", results);
            searchResultsDiv.innerHTML = '';
            if (!results || results.length === 0) {
                searchResultsDiv.innerHTML = '<p>Nie znaleziono...</p>';
                return;
            }
            const ul = document.createElement('ul');
            results.forEach((item, index) => {
                console.log(`Przetwarzanie elementu ${index}:`, item);
                const li = document.createElement('li');
                const substanceInfo = document.createElement('span');
                substanceInfo.className = 'substance-info';
                const displayName = (item.name !== undefined && item.name !== null && item.name !== '') ? item.name : 'brak nazwy';
                substanceInfo.textContent = displayName;
                li.appendChild(substanceInfo);
                const addButton = document.createElement('button');
                addButton.textContent = '+ Dodaj';
                addButton.className = 'add-substance-btn';
                addButton.dataset.name = item.name || '';
                addButton.dataset.cas = item.cas || '';
                addButton.dataset.ecNumber = item.ec_number || '';
                addButton.dataset.classification = item.classification || '';
                addButton.dataset.hPhrases = item.h_phrases || '';
                addButton.dataset.sclMfactor = item.scl_mfactor || '';
                li.appendChild(addButton);
                ul.appendChild(li);
            });
            searchResultsDiv.appendChild(ul);
        }

        async function performSearch() {
            console.log("Wywołano performSearch()");
            const query = searchInput.value.trim();
            if (query.length < 2) {
                searchResultsDiv.innerHTML = '<p>Wpisz min. 2 znaki.</p>';
                return;
            }
            searchResultsDiv.innerHTML = '<p class="loading">Szukam...</p>';
            try {
                const apiUrl = `/search_substances?query=${encodeURIComponent(query)}`;
                console.log("Fetching search:", apiUrl);
                const response = await fetch(apiUrl); // GET - CSRF not needed here
                if (!response.ok) throw new Error(`Błąd serwera: ${response.status}`);
                const data = await response.json();
                console.log("Otrzymano wyniki:", data);
                displayResults(data);
            } catch (error) {
                console.error("Błąd wyszukiwania:", error);
                searchResultsDiv.innerHTML = `<p class="error">Błąd: ${error.message}</p>`;
            }
        }

        searchButton.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                performSearch();
            }
        });

        searchResultsDiv.addEventListener('click', async (event) => {
            if (event.target.classList.contains('add-substance-btn')) {
                console.log("Kliknięto .add-substance-btn (Excel)");
                const button = event.target;
                const physicalLocation = document.getElementById('search-physical-location').value;
                if (!physicalLocation) {
                    showToast('Proszę wybrać lokalizację fizyczną przed dodaniem substancji.', 'warning');
                    return;
                }
                const substanceData = {
                    name: button.dataset.name,
                    cas: button.dataset.cas,
                    ec_number: button.dataset.ecNumber || '',
                    classification: button.dataset.classification,
                    h_phrases: button.dataset.hPhrases,
                    scl_mfactor: button.dataset.sclMfactor,
                    physical_location: physicalLocation
                };
                const locationId = searchSectionDiv.dataset.locationId;
                if (!locationId) {
                    console.error("Brak locationId (add excel)");
                    showToast('Błąd wewnętrzny.', 'error');
                    return;
                }
        
                try {
                    const apiUrl = `/location/${locationId}/add_substance`;
                    // Wywołaj fetchWithCsrf i oczekuj na sparsowane dane lub błąd
                    const responseData = await fetchWithCsrf(apiUrl, 'POST', substanceData);
        
                    // Jeśli doszło tutaj, to znaczy, że status był OK (2xx)
                    console.log("Odpowiedź (add excel - sukces):", responseData);
                    showToast(responseData.message, 'success'); // Domyślnie sukces
                    setTimeout(() => { location.reload(); }, 1500);
        
                } catch (error) { // Złap błędy (w tym te rzucone przez fetchWithCsrf dla statusów non-OK)
                    console.error("Błąd dodawania (Excel):", error);
                    // Odczytaj wiadomość z obiektu błędu (jeśli istnieje)
                    const message = error.data?.message // Sprawdź czy błąd ma pole data i message
                                    || error.message   // Lub użyj ogólnej wiadomości błędu
                                    || 'Nieznany błąd'; // Lub domyślny tekst
                    // Użyj statusu z obiektu błędu, aby określić typ toastu
                    const statusType = (error.status === 409) ? 'warning' : 'error';
                    showToast(`Wystąpił błąd: ${message}`, statusType);
                }
            }
        });
    } else {
        console.error("Brak elementów sekcji wyszukiwania Excel.");
    }

    // === SEKCJA OBSŁUGI LISTY SUBSTANCJI ===
    const substancesTable = document.getElementById('substances-table');
    const substancesTableBody = substancesTable ? substancesTable.querySelector('tbody') : null;
    console.log("TBody tabeli substancji:", substancesTableBody);

    if (substancesTableBody) {
        substancesTableBody.addEventListener('click', async (event) => {
            console.log("Kliknięcie w tbody tabeli substancji.");
            const target = event.target;

            // Usuwanie substancji
            if (target.classList.contains('delete-substance-btn')) {
                console.log("Kliknięto .delete-substance-btn");
                const button = target;
                const substanceId = button.dataset.substanceId;
                const substanceRow = button.closest('tr');
                const substanceName = substanceRow ? substanceRow.cells[1].textContent.trim() : 'tej substancji';
                if (!substanceId) {
                    console.error("Brak subId (delete)");
                    showToast('Błąd wewnętrzny.', 'error');
                    return;
                }
                if (!confirm(`Czy usunąć "${substanceName}"?`)) return;
                console.log(`Deleting ID: ${substanceId}`);
                try {
                    const apiUrl = `/substance/${substanceId}`;
                    const csrfToken = getCsrfToken(); // Pobierz token
                    if (!csrfToken) {
                        showToast('Błąd bezpieczeństwa: Brak tokenu CSRF.', 'error');
                        return;
                    }
                    const response = await fetch(apiUrl, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': csrfToken // <-- DODANY NAGŁÓWEK CSRF
                        }
                     });
                    const responseData = await response.json();
                    console.log("Odpowiedź (delete):", responseData);
                    if (!response.ok) throw new Error(responseData.message || `Błąd: ${response.status}`);
                    showToast(responseData.message, responseData.status === 'success' ? 'success' : 'error', 2500);
                    if (responseData.status === 'success') {
                        setTimeout(() => { location.reload(); }, 1500);
                    }
                } catch (error) {
                    console.error("Błąd usuwania:", error);
                    showToast(`Wystąpił błąd: ${error.message}`, 'error');
                }
                return;
            }

            // Edycja komentarza - pokazanie formularza
            if (target.classList.contains('edit-comment-btn')) {
                console.log("Kliknięto .edit-comment-btn");
                const substanceId = event.target.dataset.substanceId;
                const displaySpan = document.getElementById(`comment-display-${substanceId}`);
                const editDiv = document.getElementById(`comment-edit-${substanceId}`);
                const inputArea = document.getElementById(`comment-input-${substanceId}`);
                if (displaySpan && editDiv && inputArea) {
                    displaySpan.style.display = 'none';
                    editDiv.style.display = 'block';
                    inputArea.value = displaySpan.textContent || '';
                    inputArea.focus();
                } else { console.error(`Err Edycja Kom ${substanceId}`); }
                return;
            }

            // Anulowanie edycji komentarza
            if (target.classList.contains('cancel-comment-btn')) {
                console.log("Kliknięto .cancel-comment-btn");
                const substanceId = event.target.dataset.substanceId;
                const displaySpan = document.getElementById(`comment-display-${substanceId}`);
                const editDiv = document.getElementById(`comment-edit-${substanceId}`);
                const inputArea = document.getElementById(`comment-input-${substanceId}`);
                if (displaySpan && editDiv && inputArea) {
                    inputArea.value = displaySpan.textContent || '';
                    displaySpan.style.display = 'inline';
                    editDiv.style.display = 'none';
                } else { console.error(`Err Anuluj Kom ${substanceId}`); }
                return;
            }

            // Zapisywanie komentarza
            if (target.classList.contains('save-comment-btn')) {
                console.log("Kliknięto .save-comment-btn");
                const substanceId = event.target.dataset.substanceId;
                const inputArea = document.getElementById(`comment-input-${substanceId}`);
                const displaySpan = document.getElementById(`comment-display-${substanceId}`);
                const editDiv = document.getElementById(`comment-edit-${substanceId}`);
                if (!inputArea || !displaySpan || !editDiv) {
                    showToast('Błąd wewnętrzny.', 'error');
                    return;
                }
                const newComment = inputArea.value.trim();
                console.log(`Zapisywanie komentarza ${substanceId}: "${newComment}"`);
                try {
                    const apiUrl = `/substance/${substanceId}/comment`;
                    const csrfToken = getCsrfToken(); // Pobierz token
                    if (!csrfToken) {
                        showToast('Błąd bezpieczeństwa: Brak tokenu CSRF.', 'error');
                        return;
                    }
                    const response = await fetch(apiUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json', // Potrzebne, bo wysyłamy JSON
                            'X-CSRFToken': csrfToken // <-- DODANY NAGŁÓWEK CSRF
                        },
                        body: JSON.stringify({ comment: newComment })
                    });
                    const responseData = await response.json();
                    console.log("Odpowiedź (save comment):", responseData);
                    if (!response.ok) throw new Error(responseData.message || `Błąd: ${response.status}`);
                    if (responseData.status === 'success') {
                        displaySpan.textContent = responseData.new_comment;
                        displaySpan.style.display = 'inline';
                        editDiv.style.display = 'none';
                        showToast('Komentarz zapisany.', 'success');
                    } else {
                         showToast(responseData.message || 'Nieznany błąd zapisu.', 'error');
                    }
                } catch (error) {
                    console.error("Błąd zapisu kom:", error);
                    showToast(`Wystąpił błąd: ${error.message}`, 'error');
                }
                return;
            }

            // --- Obsługa SDS UI (bez zmian, bo używa standardowych formularzy POST) ---
            if (target.classList.contains('show-replace-sds-form')) {
                console.log("Kliknięto .show-replace-sds-form");
                const substanceId = target.dataset.substanceId;
                const formToShow = document.getElementById(`sds-form-${substanceId}`);
                const displayDiv = target.closest('.sds-cell-content');
                if (formToShow && displayDiv) {
                    displayDiv.style.display = 'none';
                    formToShow.style.display = 'flex';
                    console.log(`Pokazano formularz SDS ID: ${substanceId}`);
                } else { console.error(`Nie znaleziono elementów SDS ID: ${substanceId}`); }
                return;
            }

            if (target.classList.contains('cancel-upload-btn')) {
                console.log("Kliknięto .cancel-upload-btn");
                const substanceId = target.dataset.substanceId;
                const formToHide = document.getElementById(`sds-form-${substanceId}`);
                const cellContent = target.closest('.sds-cell').querySelector('.sds-cell-content');
                const fileInput = formToHide ? formToHide.querySelector('input[type="file"]') : null;
                if (formToHide && cellContent) {
                    formToHide.style.display = 'none';
                    cellContent.style.display = 'block';
                    if (fileInput) fileInput.value = '';
                    console.log(`Anulowano upload SDS ID: ${substanceId}`);
                } else { console.error(`Nie znaleziono elementów SDS (anuluj) ID: ${substanceId}`); }
                return;
            }
        });
    } else {
        console.warn("Nie znaleziono tbody - listenery dla tabeli substancji nieaktywne.");
    }

    // === SEKCJA OBSŁUGI RĘCZNEGO DODAWANIA ===
    const showManualFormBtn = document.getElementById('show-manual-form-btn');
    const manualAddSection = document.getElementById('manual-add-section');
    const manualAddForm = document.getElementById('manual-add-form');
    const cancelManualFormBtn = document.getElementById('cancel-manual-form-btn');
    const manualAddContainer = document.getElementById('manual-add-container'); //

    console.log("Manual add elements found:", (showManualFormBtn && manualAddSection && manualAddForm && cancelManualFormBtn) ? "All OK" : "MISSING!");

    if (showManualFormBtn && manualAddSection && manualAddForm && cancelManualFormBtn) {
        showManualFormBtn.addEventListener('click', () => {
            console.log("Kliknięto #show-manual-form-btn");
            manualAddSection.style.display = 'block';
            manualAddContainer.style.display = 'none';
            showManualFormBtn.style.display = 'none';
            document.getElementById('manual-name').focus();
        });

        cancelManualFormBtn.addEventListener('click', () => {
            console.log("Kliknięto #cancel-manual-form-btn");
            manualAddSection.style.display = 'none';
            manualAddContainer.style.display = 'flex';
            showManualFormBtn.style.display = 'inline-block';
            manualAddForm.reset();
        });

        // Używamy eventu 'submit' na formularzu
        manualAddForm.addEventListener('submit', async (event) => {
            console.log("Wysłano #manual-add-form");
            event.preventDefault(); // Zapobiegaj domyślnemu wysłaniu

            const searchSectionDivForManual = document.querySelector('.search-section[data-location-id]');
            if (!searchSectionDivForManual) {
                 console.error("Brak searchSectionDiv (manual add)");
                 showToast('Błąd wewnętrzny aplikacji.', 'error');
                 return;
            }
            const locationId = searchSectionDivForManual.dataset.locationId;

            if (!locationId) {
                console.error("Brak locationId (manual add)");
                showToast('Błąd wewnętrzny.', 'error');
                return;
            }

            const nameField = document.getElementById('manual-name');
            const physicalLocationField = document.getElementById('manual-physical-location');
            if (!nameField.value.trim()) {
                showToast("Nazwa jest wymagana.", 'warning');
                nameField.focus();
                return;
            }
             if (!physicalLocationField.value) {
                showToast('Proszę wybrać lokalizację fizyczną.', 'warning');
                physicalLocationField.focus();
                return;
            }

            const substanceData = {
                name: nameField.value.trim(),
                cas: document.getElementById('manual-cas').value.trim(),
                ec_number: document.getElementById('manual-ec').value.trim(),
                classification: document.getElementById('manual-classification').value.trim(),
                h_phrases: document.getElementById('manual-hphrases').value.trim(),
                comment: document.getElementById('manual-comment').value.trim(),
                physical_location: physicalLocationField.value
            };

            console.log(`Próba ręcznego dodania (Loc ID: ${locationId}):`, substanceData);

            try {
                const apiUrl = `/location/${locationId}/add_manual`;
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
                    body: JSON.stringify(substanceData)
                });
                const responseData = await response.json();
                console.log("Odpowiedź (manual add):", responseData);
                if (!response.ok) throw new Error(responseData.message || `Błąd: ${response.status}`);
                showToast(responseData.message, responseData.status === 'success' ? 'success' : 'error', 2500);
                if (responseData.status === 'success') {
                    manualAddForm.reset();
                    manualAddSection.style.display = 'none';
                    showManualFormBtn.style.display = 'inline-block';
                    setTimeout(() => { location.reload(); }, 1500);
                }
            } catch (error) {
                console.error("Błąd ręcznego dodawania:", error);
                showToast(`Wystąpił błąd: ${error.message}`, 'error');
            }
        });
    }

    // === SEKCJA OBSŁUGI AKCJI MASOWYCH ===
    const selectAllChk = document.getElementById('select-all-chk');
    const substanceCheckboxes = document.querySelectorAll('.substance-checkbox');
    const bulkActionArea = document.getElementById('bulk-action-area');
    const selectionCounter = document.getElementById('selection-counter');
    const moveButton = document.getElementById('move-substances-btn');
    const copyButton = document.getElementById('copy-substances-btn');
    const targetLocationSelect = document.getElementById('target-location');
    let selectedSubstanceIds = new Set();

    console.log("Bulk action elements found:", (bulkActionArea && selectionCounter && targetLocationSelect && (moveButton || copyButton) && substanceCheckboxes.length > 0) ? "All OK" : "MISSING / checkboxes empty?");

    if (bulkActionArea && selectionCounter && targetLocationSelect) {
        function updateBulkActionArea() {
            console.log("Wywołano updateBulkActionArea()");
            const count = selectedSubstanceIds.size;
            selectionCounter.textContent = count;
            const targetSelected = targetLocationSelect.value !== '';
            bulkActionArea.style.display = count > 0 ? 'flex' : 'none';
            if (moveButton) moveButton.disabled = !(count > 0 && targetSelected);
            if (copyButton) copyButton.disabled = !(count > 0 && targetSelected);
        }

        substanceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (event) => {
                console.log("Zmiana checkboxa substancji.");
                const substanceId = parseInt(event.target.value, 10);
                if (event.target.checked) { selectedSubstanceIds.add(substanceId); }
                else { selectedSubstanceIds.delete(substanceId); }
                if (selectAllChk) { selectAllChk.checked = (selectedSubstanceIds.size === substanceCheckboxes.length && substanceCheckboxes.length > 0); }
                updateBulkActionArea();
            });
        });

        if (selectAllChk) {
            selectAllChk.addEventListener('change', (event) => {
                console.log("Zmiana select-all.");
                const isChecked = event.target.checked;
                selectedSubstanceIds.clear();
                substanceCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    if (isChecked) { selectedSubstanceIds.add(parseInt(checkbox.value, 10)); }
                });
                updateBulkActionArea();
            });
        }

        targetLocationSelect.addEventListener('change', () => {
            console.log("Zmiana lokalizacji docelowej.");
            updateBulkActionArea();
        });

        // Przenoszenie
        if (moveButton) {
            moveButton.addEventListener('click', async () => {
                console.log("Kliknięto #move-substances-btn");
                const targetLocId = targetLocationSelect.value;
                const idsToMove = Array.from(selectedSubstanceIds);
                if (!targetLocId || idsToMove.length === 0) {
                    showToast("Wybierz cel i substancje.", 'warning'); return;
                }
                console.log(`Przenoszenie ID: ${idsToMove} do Lok ID: ${targetLocId}`);
                try {
                    const apiUrl = '/substances/move';
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
                        body: JSON.stringify({ substance_ids: idsToMove, target_location_id: parseInt(targetLocId, 10) })
                    });
                    const responseData = await response.json();
                    console.log("Odpowiedź (move):", responseData);
                    if (!response.ok) throw new Error(responseData.message || `Błąd: ${response.status}`);
                    showToast(responseData.message, responseData.status === 'success' ? 'success' : 'error', 2500);
                    if (responseData.status === 'success') { setTimeout(() => { location.reload(); }, 1500); }
                } catch (error) {
                    console.error("Błąd przenoszenia:", error);
                    showToast(`Wystąpił błąd: ${error.message}`, 'error');
                }
            });
        }

        // Kopiowanie
        if (copyButton) {
            copyButton.addEventListener('click', async () => {
                console.log("Kliknięto #copy-substances-btn");
                const targetLocId = targetLocationSelect.value;
                const idsToCopy = Array.from(selectedSubstanceIds);
                if (!targetLocId || idsToCopy.length === 0) {
                    showToast("Wybierz cel i substancje.", 'warning'); return;
                }
                console.log(`Kopiowanie ID: ${idsToCopy} do Lok ID: ${targetLocId}`);
                try {
                    const apiUrl = '/substances/copy';
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
                        body: JSON.stringify({ substance_ids: idsToCopy, target_location_id: parseInt(targetLocId, 10) })
                    });
                    const responseData = await response.json();
                    console.log("Odpowiedź (copy):", responseData);
                    if (!response.ok) throw new Error(responseData.message || `Błąd: ${response.status}`);
                    showToast(responseData.message, responseData.status === 'success' ? 'success' : 'error', 2500);
                    if (responseData.status === 'success') {
                        substanceCheckboxes.forEach(cb => cb.checked = false);
                        if (selectAllChk) selectAllChk.checked = false;
                        selectedSubstanceIds.clear();
                        updateBulkActionArea();
                    }
                } catch (error) {
                    console.error("Błąd kopiowania:", error);
                    showToast(`Wystąpił błąd: ${error.message}`, 'error');
                }
            });
        }

        updateBulkActionArea(); // Inicjalne ustawienie widoczności
    } else {
        console.warn("Nie znaleziono wszystkich elementów dla akcji masowych lub brak substancji.");
    }
}); // Koniec DOMContentLoaded