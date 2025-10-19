document.addEventListener('DOMContentLoaded', () => {
    console.log("all_substances.html: DOMContentLoaded - Skrypt załadowany.");
    const filterInput = document.getElementById('filter-input');
    const filterButton = document.getElementById('filter-button');
    // Usuwamy referencję do tabeli i tbody dla filtrowania po stronie klienta
    // const table = document.getElementById('all-substances-table');
    // const tableBody = table ? table.querySelector('tbody') : null;
    
    const toggleAdvancedBtn = document.getElementById('toggle-advanced-btn');
    const advancedFilters = document.getElementById('advanced-filters');
    const resetFiltersBtn = document.getElementById('reset-filters-btn');
    const physicalLocationFilter = document.getElementById('physical-location-filter');
    const userLocationFilter = document.getElementById('user-location-filter');
    const cmrFilter = document.getElementById('cmr-filter');
    const svhcFilter = document.getElementById('svhc-filter');
    const sdsFilter = document.getElementById('sds-filter');
    
    console.log("all_substances.html: Elementy filtrowania:", { filterInput, filterButton, advancedFilters });
    
    // Toggle zaawansowanych filtrów
    if (toggleAdvancedBtn && advancedFilters && resetFiltersBtn) {
        // Zachowujemy stan widoczności filtrów po przeładowaniu strony
        const advancedVisible = localStorage.getItem('advancedFiltersVisible') === 'true';
        if (advancedVisible) {
             advancedFilters.style.display = 'grid';
             toggleAdvancedBtn.textContent = 'Ukryj zaawansowane filtry';
             resetFiltersBtn.style.display = 'block';
        } else {
             advancedFilters.style.display = 'none';
             toggleAdvancedBtn.textContent = 'Pokaż zaawansowane filtry';
             resetFiltersBtn.style.display = 'none';
        }


        toggleAdvancedBtn.addEventListener('click', () => {
            const isVisible = advancedFilters.style.display !== 'none';
            advancedFilters.style.display = isVisible ? 'none' : 'grid';
            toggleAdvancedBtn.textContent = isVisible ? 'Pokaż zaawansowane filtry' : 'Ukryj zaawansowane filtry';
            resetFiltersBtn.style.display = isVisible ? 'none' : 'block';
            // Zapisujemy stan w localStorage
            localStorage.setItem('advancedFiltersVisible', !isVisible);
        });
        
        // Reset filtrów
        resetFiltersBtn.addEventListener('click', () => {
            filterInput.value = '';
            physicalLocationFilter.value = '';
            userLocationFilter.value = '';
            cmrFilter.value = '';
            svhcFilter.value = '';
            sdsFilter.value = '';
            localStorage.removeItem('advancedFiltersVisible'); // Resetuj stan ukrycia
            applyFilters(); // Zastosuj reset (przeładuj stronę)
        });
    }
    
    // NOWA Funkcja do stosowania filtrów poprzez przeładowanie strony
    function applyFilters() {
        console.log("all_substances.js: Uruchomiono applyFilters (przeładowanie strony z filtrami).");
        const filterText = filterInput.value.trim();
        const physicalLocation = physicalLocationFilter ? physicalLocationFilter.value : '';
        const userLocation = userLocationFilter ? userLocationFilter.value : '';
        const cmrValue = cmrFilter ? cmrFilter.value : '';
        const svhcValue = svhcFilter ? svhcFilter.value : '';
        const sdsValue = sdsFilter ? sdsFilter.value : '';

        const params = new URLSearchParams();

        if (filterText) {
            params.append('filter', filterText);
        }
        if (physicalLocation) {
            params.append('physical_location', physicalLocation);
        }
        if (userLocation) {
            params.append('user_location', userLocation);
        }
        if (cmrValue) {
             params.append('is_cmr', cmrValue);
        }
        if (svhcValue) {
            params.append('is_svhc', svhcValue);
        }
        if (sdsValue) {
            params.append('has_sds', sdsValue);
        }
        
        // Zachowaj parametr 'per_page' jeśli istnieje w obecnym URL
        const currentUrlParams = new URLSearchParams(window.location.search);
        const perPage = currentUrlParams.get('per_page');
        if (perPage) {
            params.append('per_page', perPage);
        }


        const baseUrl = window.location.pathname; // Pobierz tylko ścieżkę (np. /substances/all)
        const newUrl = baseUrl + (params.toString() ? '?' + params.toString() : '');
        
        console.log("all_substances.js: Przekierowuję do:", newUrl);
        window.location.href = newUrl; // Przeładuj stronę z nowym URL
    }

    // Powiązanie funkcji applyFilters z elementami UI
    if (filterInput && filterButton) { // Sprawdzamy tylko podstawowe elementy filtra, bo advanced są opcjonalne
        // Obsługa przycisku filtrowania
        filterButton.addEventListener('click', applyFilters);
        
        // Obsługa klawisza Enter w polu filtrowania
        filterInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                applyFilters();
            }
        });
        
        // Obsługa zaawansowanych filtrów - wywołaj applyFilters przy każdej zmianie
        if (physicalLocationFilter) {
            physicalLocationFilter.addEventListener('change', applyFilters);
        }
        if (userLocationFilter) {
            userLocationFilter.addEventListener('change', applyFilters);
        }
         if (cmrFilter) {
            cmrFilter.addEventListener('change', applyFilters);
        }
        if (svhcFilter) {
            svhcFilter.addEventListener('change', applyFilters);
        }
        if (sdsFilter) {
            sdsFilter.addEventListener('change', applyFilters);
        }

        // NIE usuwamy listenera 'input' całkowicie, ale zmieniamy jego działanie
        // filterInput.addEventListener('input', () => {
        //     // Usunięto opóźnione filtrowanie po stronie klienta
        // });

    } else { 
        console.error("all_substances.js: Brak podstawowych elementów filtra."); 
    }

    const exportButton = document.getElementById('export-all-button');
    console.log("all_substances.js: Przycisk eksportu:", exportButton);
    
    if (exportButton && filterInput) { // Sprawdzamy ponownie podstawowe elementy
        exportButton.addEventListener('click', (e) => {
            e.preventDefault(); // Zapobiegaj domyślnej akcji kliknięcia
            console.log("all_substances.js: Kliknięto #export-all-button");
            
            // Zbierz wszystkie parametry filtrów TAK JAK SĄ USTAWIONE W POLACH (to jest poprawne)
            const params = new URLSearchParams();
            
            const filterText = filterInput.value.trim();
            if (filterText) {
                params.append('filter', filterText);
            }
            
            // Zaawansowane filtry - upewnij się, że czytasz ich aktualne wartości
            if (physicalLocationFilter && physicalLocationFilter.value) {
                params.append('physical_location', physicalLocationFilter.value);
            }
            
            if (userLocationFilter && userLocationFilter.value) {
                params.append('user_location', userLocationFilter.value);
            }

            if (svhcFilter && svhcFilter.value) {
                params.append('is_svhc', svhcFilter.value);
            }
            
            if (cmrFilter && cmrFilter.value) {
                params.append('is_cmr', cmrFilter.value);
            }
            
            if (sdsFilter && sdsFilter.value) {
                params.append('has_sds', sdsFilter.value);
            }
            
            // Utwórz URL eksportu z parametrami
            let exportUrl = "/export/all/csv";  // Use absolute path
            const queryString = params.toString();
            if (queryString) {
                exportUrl += `?${queryString}`;
            }
            
            console.log("all_substances.js: Eksportuję do:", exportUrl);
            window.location.href = exportUrl; // Wywołaj pobieranie pliku
        });
    } else {
         // Ten błąd może się pojawić, jeśli na stronie nie ma przycisku eksportu lub pola filtra
        console.warn("all_substances.js: Brak przycisku eksportu (#export-all-button) lub podstawowego pola filtra (#filter-input).");
        // Uwaga: Komunikat błędu "Brak elementów filtra lub tabeli (tbody)."
        // na konsoli deweloperskiej, który był zgłoszony przez użytkownika
        // prawdopodobnie pochodził z innego miejsca w oryginalnym kodzie lub
        // był wynikiem innego błędu, który teraz został naprawiony
        // poprzez usunięcie client-side pagination/filtering logic.
        // Jeśli ten konkretny komunikat "Brak elementów filtra lub tabeli (tbody)."
        // pojawiał się w momencie kliknięcia "Exportuj", a nie przy ładowaniu strony,
        // to mogło to sugerować problem z cyklem życia DOM lub re-renderowaniem,
        // co jest mniej prawdopodobne po usunięciu złożonej logiki JS.
        // Nowa wersja JS powinna być prostsza i mniej podatna na takie błędy DOM.
    }

    // ===== LOGIKA ZACHOWANIA FILTRÓW W URL I POLACH =====
    // Przy ładowaniu strony, odczytaj parametry z URL i ustaw wartości pól
    const urlParams = new URLSearchParams(window.location.search);

    if (filterInput) {
        filterInput.value = urlParams.get('filter') || '';
    }
    if (physicalLocationFilter) {
        physicalLocationFilter.value = urlParams.get('physical_location') || '';
    }
    if (userLocationFilter) {
        userLocationFilter.value = urlParams.get('user_location') || '';
    }
    if (cmrFilter) {
        cmrFilter.value = urlParams.get('is_cmr') || '';
    }
     if (svhcFilter) {
        svhcFilter.value = urlParams.get('is_svhc') || '';
    }
     if (sdsFilter) {
        sdsFilter.value = urlParams.get('has_sds') || '';
    }
    // ===== KONIEC LOGIKI ZACHOWANIA FILTRÓW =====


    // ===== LOGIKA ZMIANY PER_PAGE =====
    const perPageSelect = document.querySelector('.per-page-selector select');
    if (perPageSelect) {
        const currentUrlParams = new URLSearchParams(window.location.search);
        const currentPerPage = currentUrlParams.get('per_page');

        // Ustaw bieżącą wartość selecta na podstawie URL
        if (currentPerPage) {
            perPageSelect.value = currentPerPage;
        }

        perPageSelect.addEventListener('change', (event) => {
            const newPerPage = event.target.value;
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.set('per_page', newPerPage);
            urlParams.set('page', 1); // Resetuj do pierwszej strony przy zmianie per_page
            const baseUrl = window.location.pathname;
            window.location.href = baseUrl + '?' + urlParams.toString();
        });
    } else {
        console.warn("all_substances.js: Nie znaleziono selektora per-page.");
    }
    // ===== KONIEC LOGIKI ZMIANY PER_PAGE =====

}); // Koniec DOMContentLoaded