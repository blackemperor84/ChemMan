// Paginacja dla tabeli w lokalizacji i wszystkich substancjach
class TablePagination {
    /**
     * Konstruktor
     * @param {HTMLTableElement} table - Element tabeli
     * @param {Object} options - Opcje konfiguracyjne
     */
    constructor(table, options = {}) {
        // Elementy DOM
        this.table = table;
        this.tbody = table.querySelector('tbody');
        
        if (!this.tbody) {
            console.error("Nie znaleziono elementu tbody w tabeli!");
            return;
        }
        
        // Opcje
        this.options = {
            rowsPerPage: options.rowsPerPage || 10,
            containerSelector: options.containerSelector || null,
            pageSizes: options.pageSizes || [5, 10, 25, 50, 100],
            countText: options.countText || "Wyświetlanie {from} do {to} z {total} rekordów"
        };
        
        // Stan
        this.currentPage = 1;
        this.totalRows = this.tbody.rows.length;
        this.totalPages = Math.ceil(this.totalRows / this.options.rowsPerPage);
        this.visibleRows = [];
        
        // Inicjalizacja
        this.init();
    }
    
    /**
     * Inicjalizacja paginacji
     */
    init() {
        // Stwórz kontener kontrolek paginacji
        this.createControls();
        
        // Zastosuj początkową paginację
        this.goToPage(1);
        
        // Aktualizuj licznik stron
        this.updatePaginationInfo();
    }
    
    /**
     * Tworzy elementy kontrolne paginacji
     */
    createControls() {
        // Utwórz główny kontener dla kontrolek
        this.paginationContainer = document.createElement('div');
        this.paginationContainer.className = 'pagination-container';
        
        // Stylowanie kontenera
        this.paginationContainer.style.display = 'flex';
        this.paginationContainer.style.justifyContent = 'space-between';
        this.paginationContainer.style.alignItems = 'center';
        this.paginationContainer.style.margin = '15px 0';
        this.paginationContainer.style.padding = '10px';
        this.paginationContainer.style.backgroundColor = '#f8f9fa';
        this.paginationContainer.style.borderRadius = '5px';
        this.paginationContainer.style.border = '1px solid #ddd';
        
        // Lewy panel - wybór liczby rekordów na stronę
        const leftPanel = document.createElement('div');
        leftPanel.className = 'pagination-left';
        leftPanel.style.display = 'flex';
        leftPanel.style.alignItems = 'center';
        
        // Etykieta
        const rowsPerPageLabel = document.createElement('span');
        rowsPerPageLabel.textContent = 'Rekordów na stronę: ';
        rowsPerPageLabel.style.marginRight = '5px';
        
        // Selektor liczby rekordów na stronę
        this.rowsPerPageSelect = document.createElement('select');
        this.rowsPerPageSelect.className = 'rows-per-page-select';
        this.rowsPerPageSelect.style.padding = '5px';
        this.rowsPerPageSelect.style.borderRadius = '4px';
        this.rowsPerPageSelect.style.border = '1px solid #ccc';
        
        // Dodaj opcje
        this.options.pageSizes.forEach(size => {
            const option = document.createElement('option');
            option.value = size;
            option.textContent = size;
            if (size === this.options.rowsPerPage) {
                option.selected = true;
            }
            this.rowsPerPageSelect.appendChild(option);
        });
        
        // Dodaj event listener do zmiany liczby rekordów na stronę
        this.rowsPerPageSelect.addEventListener('change', () => {
            this.options.rowsPerPage = parseInt(this.rowsPerPageSelect.value, 10);
            this.totalPages = Math.ceil(this.totalRows / this.options.rowsPerPage);
            this.goToPage(1); // Po zmianie liczby rekordów, wróć do pierwszej strony
            this.updatePaginationInfo();
        });
        
        leftPanel.appendChild(rowsPerPageLabel);
        leftPanel.appendChild(this.rowsPerPageSelect);
        
        // Środkowy panel - informacje o paginacji
        this.paginationInfo = document.createElement('div');
        this.paginationInfo.className = 'pagination-info';
        this.paginationInfo.style.textAlign = 'center';
        
        // Prawy panel - nawigacja stron
        const rightPanel = document.createElement('div');
        rightPanel.className = 'pagination-controls';
        rightPanel.style.display = 'flex';
        rightPanel.style.alignItems = 'center';
        
        // Przyciski nawigacyjne
        const createNavButton = (text, action, title) => {
            const btn = document.createElement('button');
            btn.textContent = text;
            btn.title = title;
            btn.className = 'pagination-button';
            btn.style.margin = '0 5px';
            btn.style.padding = '5px 10px';
            btn.style.borderRadius = '4px';
            btn.style.backgroundColor = '#fff';
            btn.style.border = '1px solid #ddd';
            btn.style.cursor = 'pointer';
            
            btn.addEventListener('click', action);
            return btn;
        };
        
        // Przyciski nawigacji
        this.firstPageBtn = createNavButton('<<', () => this.goToPage(1), 'Pierwsza strona');
        this.prevPageBtn = createNavButton('<', () => this.goToPage(this.currentPage - 1), 'Poprzednia strona');
        
        this.pageInfo = document.createElement('span');
        this.pageInfo.className = 'page-info';
        this.pageInfo.style.margin = '0 10px';
        
        this.nextPageBtn = createNavButton('>', () => this.goToPage(this.currentPage + 1), 'Następna strona');
        this.lastPageBtn = createNavButton('>>', () => this.goToPage(this.totalPages), 'Ostatnia strona');
        
        rightPanel.appendChild(this.firstPageBtn);
        rightPanel.appendChild(this.prevPageBtn);
        rightPanel.appendChild(this.pageInfo);
        rightPanel.appendChild(this.nextPageBtn);
        rightPanel.appendChild(this.lastPageBtn);
        
        // Dodaj wszystkie panele do kontenera
        this.paginationContainer.appendChild(leftPanel);
        this.paginationContainer.appendChild(this.paginationInfo);
        this.paginationContainer.appendChild(rightPanel);
        
        // Umieść kontener po tabeli lub w określonym kontenerze
        if (this.options.containerSelector) {
            const customContainer = document.querySelector(this.options.containerSelector);
            if (customContainer) {
                customContainer.appendChild(this.paginationContainer);
            } else {
                this.table.parentNode.insertBefore(this.paginationContainer, this.table.nextSibling);
            }
        } else {
            this.table.parentNode.insertBefore(this.paginationContainer, this.table.nextSibling);
        }
    }
    
    /**
     * Przechodzi do określonej strony
     * @param {number} pageNum - Numer strony
     */
    goToPage(pageNum, visibleRowsOverride = null) {
        // Określ listę wierszy do paginowania
        // Jeśli podano nadpisanie (np. z refresh po filtrowaniu), użyj go.
        // W przeciwnym razie załóż, że wszystkie wiersze w tbody są potencjalnie widoczne (ładowanie początkowe).
        const rowsToPaginate = visibleRowsOverride !== null
            ? visibleRowsOverride
            : Array.from(this.tbody.rows);
    
        // Użyj długości listy paginowanej do obliczenia całkowitej liczby wierszy JEŚLI podano nadpisanie.
        // Zapewnia to poprawną liczbę stron po filtrowaniu.
        // W przeciwnym razie użyj całkowitej liczby wierszy w tbody (dla ładowania początkowego).
        const currentTotalRows = rowsToPaginate.length;
        // Przelicz całkowitą liczbę stron na podstawie wierszy, które aktualnie paginujemy
        this.totalPages = Math.ceil(currentTotalRows / this.options.rowsPerPage);
    
        // Zwaliduj numer strony względem potencjalnie nowej liczby stron
        if (pageNum < 1) pageNum = 1;
        // Upewnij się, że pageNum nie przekracza (ewentualnie zmniejszonej) liczby stron
        if (pageNum > this.totalPages) pageNum = this.totalPages;
        // Obsłuż przypadek braku wierszy/stron
        if (this.totalPages === 0) pageNum = 1;
    
        this.currentPage = pageNum;
    
        // Oblicz indeksy wycinka na podstawie listy, którą paginujemy
        const startIdx = (pageNum - 1) * this.options.rowsPerPage;
        const endIdx = Math.min(startIdx + this.options.rowsPerPage, currentTotalRows);
        const rowsToShowOnPage = rowsToPaginate.slice(startIdx, endIdx);
    
        // Najpierw ukryj WSZYSTKIE wiersze w tbody
        for (let i = 0; i < this.tbody.rows.length; i++) {
            this.tbody.rows[i].style.display = 'none';
        }
    
        // Pokaż tylko obliczony wycinek dla bieżącej strony
        rowsToShowOnPage.forEach(row => {
            row.style.display = ''; // Zresetuj styl display dla widocznych wierszy
        });
    
        // Zaktualizuj informacje o paginacji używając poprawnej liczby całkowitej do wyświetlenia
        this.updatePaginationInfo(currentTotalRows); // Przekaż poprawną liczbę
    
        // Zaktualizuj stan przycisków na podstawie bieżącej strony i liczby stron
        this.updateButtonsState();
    }
    
    /**
     * Aktualizuje informacje o paginacji
     */
    updatePaginationInfo(total = null) {
        const displayTotal = total !== null ? total : this.totalRows; // Użyj nadpisania, jeśli podano
    
        const startIdx = displayTotal === 0 ? 0 : (this.currentPage - 1) * this.options.rowsPerPage + 1;
        const endIdx = Math.min(startIdx + this.options.rowsPerPage - 1, displayTotal);
    
        // Zaktualizuj wyświetlanie numeru strony
        this.pageInfo.textContent = `${this.currentPage} / ${this.totalPages === 0 ? 1 : this.totalPages}`; // Pokaż 1/1 jeśli 0 stron
    
        // Zaktualizuj wyświetlanie liczby rekordów
        const infoText = this.options.countText
            .replace('{from}', startIdx)
            .replace('{to}', endIdx)
            .replace('{total}', displayTotal);
    
        this.paginationInfo.textContent = infoText;
    }
    
    /**
     * Aktualizuje stan przycisków nawigacyjnych
     */
    updateButtonsState() {
        // Dezaktywuj przyciski jeśli osiągnięto granice
        this.firstPageBtn.disabled = this.currentPage === 1;
        this.prevPageBtn.disabled = this.currentPage === 1;
        this.nextPageBtn.disabled = this.currentPage === this.totalPages || this.totalPages === 0;
        this.lastPageBtn.disabled = this.currentPage === this.totalPages || this.totalPages === 0;
        
        // Zmień styl dla dezaktywowanych przycisków
        [this.firstPageBtn, this.prevPageBtn, this.nextPageBtn, this.lastPageBtn].forEach(btn => {
            if (btn.disabled) {
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        });
    }
    
    /**
     * Odświeża paginację (np. po zmianie danych w tabeli)
     */

    refresh() {
        // Filtruj wiersze na podstawie aktualnego stylu 'display' ustawionego przez zewnętrzną funkcję filtra
        const visibleRows = Array.from(this.tbody.rows).filter(row => row.style.display !== 'none');
        this.totalRows = visibleRows.length; // Licz tylko widoczne wiersze
        this.totalPages = Math.ceil(this.totalRows / this.options.rowsPerPage);
    
        // Zawsze resetuj do strony 1 po filtrowaniu lub odświeżeniu danych zmieniających widoczność
        this.currentPage = 1;
    
        // Przejdź do strony (teraz strony 1) używając tylko widocznych wierszy
        this.goToPage(this.currentPage, visibleRows); // Przekaż widoczne wiersze
    
        console.log(`Paginacja odświeżona. Łączna liczba widocznych wierszy: ${this.totalRows}, Łączna liczba stron: ${this.totalPages}`);
    }
}

// Funkcja inicjalizująca paginację dla tabeli w location_detail.html
/*
function initLocationDetailPagination() {
    // Sprawdź czy tabela istnieje
    const substancesTable = document.getElementById('substances-table');
    if (substancesTable) {
        console.log("Inicjalizacja paginacji dla tabeli substancji w lokalizacji");
        // Utwórz instancję paginacji
        window.substancesPagination = new TablePagination(substancesTable, {
            rowsPerPage: 10,
            pageSizes: [5, 10, 25, 50, 100]
        });
    }
}*/

// Funkcja inicjalizująca paginację dla tabeli w all_substances.html
function initAllSubstancesPagination() {
    // Sprawdź czy tabela istnieje
    const allSubstancesTable = document.getElementById('all-substances-table');
    if (allSubstancesTable) {
        console.log("Inicjalizacja paginacji dla tabeli wszystkich substancji");
        // Utwórz instancję paginacji
        window.allSubstancesPagination = new TablePagination(allSubstancesTable, {
            rowsPerPage: 10,
            pageSizes: [5, 10, 25, 50, 100]
        });
    }
}
