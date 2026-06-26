const subcategoriesData = {
        'cleaning': ['Комплексная уборка', 'Уборка после ремонта', 'Мытье окон', 'Химчистка мебели', 'Уборка офисов'],
        'repair': ['Поклейка обоев', 'Укладка ламината', 'Установка дверей', 'Монтаж потолков', 'Сантехника', 'Электрика', 'Сборка мебели'],
        'delivery': ['Доставка продуктов', 'Доставка еды', 'Курьерская доставка', 'Грузоперевозки'],
        'construction': ['Отделка квартир', 'Перепланировка', 'Фасадные работы', 'Кровля'],
        'design': ['Дизайн интерьера', '3D визуализация', 'Ландшафтный дизайн', 'Веб-дизайн'],
        'photography': ['Свадебная съемка', 'Портретная съемка', 'Репортаж', 'Предметная съемка'],
        'it': ['Разработка сайтов', 'Мобильные приложения', 'Настройка серверов', 'IT-консалтинг'],
        'education': ['Репетиторство', 'Курсы', 'Изучение языков', 'Подготовка к экзаменам'],
        'beauty': ['Парикмахер', 'Маникюр', 'Косметология', 'Визаж', 'Массаж']
    };

    const categorySelect = document.getElementById('categorySelect');
    const subcategoryGroup = document.getElementById('subcategoryGroup');
    const subcategorySelect = document.getElementById('subcategorySelect');
    const performerSelect = document.getElementById('performerSelect');
    const servicesDiv = document.getElementById('performerServices');
    const priceHint = document.getElementById('priceHint');
    const hiddenCategory = document.getElementById('hiddenCategory');

    function loadSubcategories(category, servicesList = null) {
        let services = [];
        if (servicesList && servicesList.length > 0) {
            services = servicesList;
        } else if (category && subcategoriesData[category]) {
            services = subcategoriesData[category];
        }
        if (services.length > 0) {
            subcategorySelect.innerHTML = '<option value="">Выберите услугу</option>';
            services.forEach(service => {
                subcategorySelect.innerHTML += `<option value="${service}">${service}</option>`;
            });
            subcategoryGroup.style.display = 'block';
        } else {
            subcategoryGroup.style.display = 'none';
        }
    }

    function resetAllFields() {
        categorySelect.disabled = false;
        categorySelect.value = 'repair';
        subcategoryGroup.style.display = 'none';
        subcategorySelect.innerHTML = '<option value="">Выберите услугу</option>';
        if (servicesDiv) {
            servicesDiv.style.display = 'none';
            servicesDiv.innerHTML = '';
        }
        if (priceHint) {
            priceHint.innerHTML = '';
        }
        hiddenCategory.value = 'repair';
    }

    performerSelect.addEventListener('change', async function() {
        const performerId = this.value;
        if (!performerId) {
            resetAllFields();
            return;
        }
        try {
            const response = await fetch(`/api/performer/${performerId}/`);
            const data = await response.json();
            if (response.ok) {
                if (data.category) {
                    categorySelect.value = data.category;
                    categorySelect.disabled = true;
                    hiddenCategory.value = data.category;
                    if (data.services && data.services.length > 0) {
                        loadSubcategories(data.category, data.services);
                    } else if (subcategoriesData[data.category]) {
                        loadSubcategories(data.category, null);
                    } else {
                        subcategoryGroup.style.display = 'none';
                    }
                } else {
                    categorySelect.disabled = false;
                    categorySelect.value = 'repair';
                    subcategoryGroup.style.display = 'none';
                }
                if (data.price) {
                    priceHint.innerHTML = `<small style="color:#10b981;">💰 Рекомендуемый бюджет: от ${data.price} ₽/час</small>`;
                } else {
                    priceHint.innerHTML = '';
                }
                if (data.services && data.services.length > 0) {
                    servicesDiv.style.display = 'block';
                    servicesDiv.innerHTML = `
                        <label><i class="fas fa-list-check"></i> Услуги исполнителя</label>
                        <div style="background:#f3f4f6; padding:12px; border-radius:12px;">
                            <div style="display:flex; flex-wrap:wrap; gap:8px;">
                                ${data.services.map(s => `<span style="background:#e0e7ff; color:#4f46e5; padding:4px 12px; border-radius:20px; font-size:12px; cursor:pointer;" onclick="selectService('${s.replace(/'/g, "\\'")}')">${s}</span>`).join('')}
                            </div>
                            <small style="display:block; margin-top:8px; color:#6b7280;">👆 Нажмите на услугу, чтобы выбрать</small>
                        </div>
                    `;
                } else {
                    servicesDiv.style.display = 'none';
                    servicesDiv.innerHTML = '';
                }
                showNotification(`Выбран исполнитель: ${data.username}`, 'success');
            }
        } catch (error) {
            console.error('Ошибка:', error);
        }
    });

    categorySelect.addEventListener('change', function() {
        if (performerSelect.value) return;
        hiddenCategory.value = this.value;
        loadSubcategories(this.value, null);
    });

    function selectService(serviceName) {
        if (subcategorySelect) {
            let found = false;
            for (let i = 0; i < subcategorySelect.options.length; i++) {
                if (subcategorySelect.options[i].value === serviceName) {
                    subcategorySelect.selectedIndex = i;
                    found = true;
                    break;
                }
            }
            if (!found) {
                const option = document.createElement('option');
                option.value = serviceName;
                option.text = serviceName;
                subcategorySelect.appendChild(option);
                subcategorySelect.value = serviceName;
                subcategoryGroup.style.display = 'block';
            }
            showNotification(`Выбрана услуга: ${serviceName}`, 'success');
        }
    }

    function getCurrentLocation() {
        if (!navigator.geolocation) {
            showNotification('Геолокация не поддерживается', 'error');
            return;
        }
        showNotification('Определяем местоположение...', 'info');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                document.getElementById('latitudeInput').value = lat.toString().replace(',', '.');
                document.getElementById('longitudeInput').value = lng.toString().replace(',', '.');
                fetch(`/api/search/reverse_geocode/?lat=${lat}&lng=${lng}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.address) {
                            document.getElementById('addressInput').value = data.address;
                        }
                        showNotification('Местоположение определено!', 'success');
                    });
            },
            () => showNotification('Не удалось определить местоположение', 'error')
        );
    }

    function showNotification(message, type) {
        const notification = document.getElementById('notification');
        if (notification) {
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.style.display = 'block';
            setTimeout(() => notification.style.display = 'none', 3000);
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        const urlParams = new URLSearchParams(window.location.search);
        const performerId = urlParams.get('performer_id');
        if (performerId && performerSelect) {
            performerSelect.value = performerId;
            performerSelect.dispatchEvent(new Event('change'));
        }
        hiddenCategory.value = categorySelect.value;
    });