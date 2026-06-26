async function loadServicesCheckboxes() {
    const category = document.getElementById('performerCategory').value;
    const servicesGroup = document.getElementById('servicesGroup');
    const servicesCheckboxes = document.getElementById('servicesCheckboxes');
    const savedServices = document.getElementById('servicesInput').value;
    const savedServicesList = savedServices ? savedServices.split(',').map(s => s.trim()) : [];

    if (!category) {
        servicesGroup.style.display = 'none';
        return;
    }

    servicesGroup.style.display = 'block';

    try {
        const response = await fetch(`/api/categories/${category}/subcategories/`);
        const data = await response.json();

        if (data.subcategories && data.subcategories.length > 0) {
            const services = data.subcategories.map(s => s.name);
            servicesCheckboxes.innerHTML = services.map(service => `
                <label class="service-checkbox">
                    <input type="checkbox" value="${service}" ${savedServicesList.includes(service) ? 'checked' : ''}>
                    <span>${service}</span>
                </label>
            `).join('');

            const checkboxes = servicesCheckboxes.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.addEventListener('change', updateServicesInput);
            });
            updateServicesInput();
        } else {
            servicesCheckboxes.innerHTML = '<p style="color: #6b7280;">Нет доступных услуг для этой категории</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки услуг:', error);
        servicesCheckboxes.innerHTML = '<p style="color: #ef4444;">Ошибка загрузки услуг</p>';
    }
}

function updateServicesInput() {
    const servicesCheckboxes = document.getElementById('servicesCheckboxes');
    const selected = Array.from(servicesCheckboxes.querySelectorAll('input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    document.getElementById('servicesInput').value = selected.join(',');
}

document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('performerCategory');
    if (categorySelect) {
        categorySelect.addEventListener('change', loadServicesCheckboxes);
        loadServicesCheckboxes();
    }
});