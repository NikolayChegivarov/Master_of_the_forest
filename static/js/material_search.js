/**
 * Универсальная функция поиска материала с выпадающим списком
 *
 * Использование:
 * initMaterialSearch({
 *     inputId: 'material-search',           // ID поля ввода
 *     selectId: 'id_material',              // ID скрытого select
 *     dropdownId: 'material-dropdown',      // ID контейнера выпадающего списка
 *     onSelect: function(selectedValue) {}  // Колбэк при выборе (опционально)
 * });
 */

function initMaterialSearch(options) {
    const {
        inputId,
        selectId,
        dropdownId,
        onSelect = null
    } = options;

    const searchInput = document.getElementById(inputId);
    const hiddenSelect = document.getElementById(selectId);
    const dropdown = document.getElementById(dropdownId);

    if (!searchInput || !hiddenSelect || !dropdown) {
        console.warn(`Material search: не найдены элементы для ${inputId}`);
        return;
    }

    // Получаем все опции из скрытого select
    let options_list = Array.from(hiddenSelect.options).filter(opt => opt.value !== '');

    // Функция обновления опций (например, при фильтрации по типу)
    function updateOptions() {
        options_list = Array.from(hiddenSelect.options).filter(opt => opt.value !== '');
    }

    // Функция показа выпадающего списка
    function showDropdown(filteredOptions) {
        if (filteredOptions.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = '';
        filteredOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'material-dropdown-item';
            item.textContent = opt.textContent;
            item.setAttribute('data-value', opt.value);
            item.addEventListener('click', function() {
                searchInput.value = this.textContent;
                hiddenSelect.value = this.getAttribute('data-value');
                dropdown.style.display = 'none';

                // Триггерим событие change
                const changeEvent = new Event('change', { bubbles: true });
                hiddenSelect.dispatchEvent(changeEvent);

                // Вызываем колбэк если есть
                if (typeof onSelect === 'function') {
                    onSelect(hiddenSelect.value);
                }
            });
            dropdown.appendChild(item);
        });
        dropdown.style.display = 'block';
    }

    // Фильтрация материалов
    function filterMaterials() {
        const searchText = searchInput.value.toLowerCase();
        const filtered = options_list.filter(opt =>
            opt.textContent.toLowerCase().includes(searchText)
        );
        showDropdown(filtered);
    }

    // Обработчики событий
    searchInput.addEventListener('input', filterMaterials);
    searchInput.addEventListener('focus', filterMaterials);
    searchInput.addEventListener('click', function(e) {
        e.stopPropagation();
        filterMaterials();
    });

    // Закрываем выпадающий список при клике вне
    document.addEventListener('click', function(e) {
        if (e.target !== searchInput && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Инициализация: если есть выбранное значение
    if (hiddenSelect.value) {
        const selected = options_list.find(opt => opt.value === hiddenSelect.value);
        if (selected) {
            searchInput.value = selected.textContent;
        }
    }

    // При изменении скрытого select обновляем поле ввода
    hiddenSelect.addEventListener('change', function() {
        const selectedOpt = options_list.find(opt => opt.value === hiddenSelect.value);
        if (selectedOpt) {
            searchInput.value = selectedOpt.textContent;
        }
    });

    // Возвращаем API для управления извне
    return {
        updateOptions: updateOptions,
        setOptions: function(newOptions) {
            options_list = newOptions;
        }
    };
}

/**
 * Универсальная функция поиска места хранения (склад, ТС, бригада, контрагент)
 */
function initLocationSearch(options) {
    const {
        inputId,
        selectId,
        dropdownId,
        onSelect = null
    } = options;

    const searchInput = document.getElementById(inputId);
    const hiddenSelect = document.getElementById(selectId);
    const dropdown = document.getElementById(dropdownId);

    if (!searchInput || !hiddenSelect || !dropdown) {
        console.warn(`Location search: не найдены элементы для ${inputId}`);
        return;
    }

    let options_list = Array.from(hiddenSelect.options).filter(opt => opt.value !== '');

    function updateOptions() {
        options_list = Array.from(hiddenSelect.options).filter(opt => opt.value !== '');
    }

    function showDropdown(filteredOptions) {
        if (filteredOptions.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = '';
        filteredOptions.forEach(opt => {
            const item = document.createElement('div');
            item.className = 'filter-dropdown-item';
            item.textContent = opt.textContent;
            item.setAttribute('data-value', opt.value);
            item.addEventListener('click', function() {
                searchInput.value = this.textContent;
                hiddenSelect.value = this.getAttribute('data-value');
                dropdown.style.display = 'none';

                const changeEvent = new Event('change', { bubbles: true });
                hiddenSelect.dispatchEvent(changeEvent);

                if (typeof onSelect === 'function') {
                    onSelect(hiddenSelect.value);
                }
            });
            dropdown.appendChild(item);
        });
        dropdown.style.display = 'block';
    }

    function filterLocations() {
        const searchText = searchInput.value.toLowerCase();
        const filtered = options_list.filter(opt =>
            opt.textContent.toLowerCase().includes(searchText)
        );
        showDropdown(filtered);
    }

    searchInput.addEventListener('input', filterLocations);
    searchInput.addEventListener('focus', filterLocations);
    searchInput.addEventListener('click', function(e) {
        e.stopPropagation();
        filterLocations();
    });

    document.addEventListener('click', function(e) {
        if (e.target !== searchInput && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    if (hiddenSelect.value) {
        const selected = options_list.find(opt => opt.value === hiddenSelect.value);
        if (selected) {
            searchInput.value = selected.textContent;
        }
    }

    hiddenSelect.addEventListener('change', function() {
        const selectedOpt = options_list.find(opt => opt.value === hiddenSelect.value);
        if (selectedOpt) {
            searchInput.value = selectedOpt.textContent;
        }
    });

    return {
        updateOptions: updateOptions,
        setOptions: function(newOptions) {
            options_list = newOptions;
        }
    };
}