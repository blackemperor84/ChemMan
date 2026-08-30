/**
 * Pobiera token CSRF z meta tagu w <head>.
 * @returns {string|null} Wartość tokenu CSRF lub null, jeśli meta tag nie został znaleziony.
 */
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) {
        return token.getAttribute('content');
    }
    console.error('CSRF token meta tag not found!');
    return null;
}

/**
 * Pomocnicza funkcja do wykonywania zapytań AJAX z tokenami CSRF
 * @param {string} url - URL do wykonania zapytania
 * @param {string} method - Metoda HTTP (GET, POST, PUT, DELETE)
 * @param {Object} data - Dane do wysłania (opcjonalne)
 * @returns {Promise} - Obiekt Promise, który:
 * - Rozwiązuje się z przetworzonym ciałem odpowiedzi (JSON lub tekst) w przypadku sukcesu (status 2xx).
 * - Odrzuca z obiektem błędu zawierającym status, statusText i przetworzone ciało (w polu `data`) w przypadku błędu HTTP.
 * - Odrzuca z prostym błędem w przypadku problemów sieciowych.
 */
function fetchWithCsrf(url, method = 'GET', data = null) {
    const headers = {
        'Content-Type': 'application/json'
        // Nie dodajemy Accept, fetch domyślnie akceptuje wszystko ('*/*')
    };

    // Dodaj token CSRF do nagłówków dla metod modyfikujących dane
    if (method.toUpperCase() !== 'GET') { // Użyj toUpperCase dla pewności
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        } else {
            // Zwróć odrzuconą obietnicę, aby można było użyć .catch()
            return Promise.reject(new Error('Brak tokenu CSRF. Odśwież stronę i spróbuj ponownie.'));
        }
    }

    const options = {
        method: method,
        headers: headers,
        credentials: 'same-origin'
    };

    if (data && method.toUpperCase() !== 'GET') {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options)
        .then(response => {
            const contentType = response.headers.get('Content-Type') || '';
            const isJson = contentType.includes('application/json');

            // Zwróć obietnicę, która przetwarza ciało odpowiedzi
            const bodyPromise = isJson ? response.json() : response.text();

            return bodyPromise.then(body => {
                if (!response.ok) {
                    // Stwórz i rzuć błąd zawierający status i przetworzone ciało
                    const error = new Error(isJson ? (body.message || `Błąd HTTP: ${response.status}`) : `Błąd HTTP: ${response.status}`);
                    error.status = response.status;
                    error.statusText = response.statusText;
                    error.data = body; // Dołącz przetworzone ciało (JSON lub tekst) do błędu
                    throw error;
                }
                // W przypadku sukcesu, zwróć przetworzone ciało
                return body; // Zwraca sparsowany JSON lub tekst
            });
        })
        .catch(networkError => {
            // Złap błędy sieciowe (np. brak połączenia, błąd DNS)
            console.error("Błąd sieci w fetchWithCsrf:", networkError);
            // Rzuć dalej standardowy błąd
            throw new Error(`Błąd sieci: ${networkError.message}`);
        });
}
// Upewnij się, że funkcja jest dostępna globalnie
window.fetchWithCsrf = fetchWithCsrf;


/**
         * Pokazuje customowy alert w stylu toast
         * @param {string} message - Treść wiadomości
         * @param {string} type - Typ wiadomości: 'success', 'error', 'warning', 'info'
         * @param {number} duration - Czas wyświetlania w ms (domyślnie 5000)
         */
function showToast(message, type = 'info', duration = 3000) {
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
    
    // Wypełnij treścią - textContent zamiast innerHTML (ochrona przed XSS)
    const content = document.createElement('div');
    content.className = 'toast-content';
    content.textContent = message;
    toast.appendChild(content);

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'toast-close-btn';
    closeButton.innerHTML = '&times;';
    toast.appendChild(closeButton);

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
}

// System automatycznych alertów dla flash messages
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.toast-message');
    const autoHideDelay = 10000; // 10 sekund

    // Dodaj klasę z timerem do wszystkich wiadomości
    flashMessages.forEach(message => {
        message.classList.add('with-timer');
        
        // Dodaj automatyczne znikanie
        setTimeout(() => {
            if (message && document.body.contains(message)) {
                message.classList.add('fade-out');
                setTimeout(() => {
                    message.remove();
                }, 500); // czas trwania animacji
            }
        }, autoHideDelay);
        
        // Obsługa przycisku zamknięcia
        const closeBtn = message.querySelector('.toast-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                message.classList.add('fade-out');
                setTimeout(() => {
                    message.remove();
                }, 500);
            });
        }
    });
});

if (typeof window.showToast !== 'function') {
    window.showToast = showToast;
}