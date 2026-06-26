let watchPositionId = null;
let autoLocationEnabled = localStorage.getItem('autoLocation') === 'true';
let lastSavedLocation = null;

async function saveCurrentLocationToProfile() {
    let token = localStorage.getItem('authToken');

    if (!token) {
        const cookieMatch = document.cookie.match(/auth_token=([^;]+)/);
        if (cookieMatch) {
            token = cookieMatch[1];
            localStorage.setItem('authToken', token);
            console.log('Токен восстановлен из cookie');
        }
    }

    console.log('Токен для запроса:', token ? `${token.substring(0, 20)}...` : 'Нет токена');

    if (!token) {
        console.log('❌ Пользователь не авторизован');
        return { success: false, error: 'Not authorized' };
    }

    try {
        const checkResponse = await fetch('/api/profiles/me/', {
            headers: {
                'Authorization': `Token ${token}`
            }
        });

        if (!checkResponse.ok) {
            console.log('❌ Токен недействителен, нужно перелогиниться');
            localStorage.removeItem('authToken');
            showNotification('Сессия истекла. Войдите снова.', 'error');
            return { success: false, error: 'Invalid token' };
        }
    } catch (e) {
        console.log('Ошибка проверки токена');
    }

    if (!navigator.geolocation) {
        console.log('Геолокация не поддерживается');
        return;
    }

    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;

                if (lastSavedLocation &&
                    Math.abs(lastSavedLocation.lat - lat) < 0.0001 &&
                    Math.abs(lastSavedLocation.lng - lng) < 0.0001) {
                    console.log('Местоположение не изменилось, пропускаем');
                    resolve();
                    return;
                }

                console.log(`📍 Сохранение координат: ${lat}, ${lng} (точность: ${accuracy}м)`);

                try {
                    const response = await fetch('/api/profiles/update_location/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Token ${token}`
                        },
                        body: JSON.stringify({
                            latitude: lat,
                            longitude: lng,
                            address: `Автоопределение (${new Date().toLocaleTimeString()})`
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        lastSavedLocation = { lat, lng };
                        console.log('✅ Координаты сохранены в профиль');
                        showNotification('📍 Местоположение обновлено', 'success', 2000);
                        resolve();
                    } else {
                        console.error('Ошибка сохранения:', data);
                        reject(data);
                    }
                } catch (error) {
                    console.error('Ошибка при сохранении:', error);
                    reject(error);
                }
            },
            (error) => {
                console.error('Ошибка геолокации:', error.message);
                reject(error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    });
}

function startAutoLocation() {
if (!navigator.geolocation) {
    console.log('Геолокация не поддерживается');
    return;
}

if (watchPositionId !== null) {
    stopAutoLocation();
}

saveCurrentLocationToProfile();

watchPositionId = setInterval(() => {
    saveCurrentLocationToProfile();
}, 30000);

console.log('🟢 Автоматическое определение местоположения запущено (интервал 30 сек)');
}

function stopAutoLocation() {
if (watchPositionId !== null) {
    clearInterval(watchPositionId);
    watchPositionId = null;
    console.log('🔴 Автоматическое определение местоположения остановлено');
}
}

function toggleAutoLocation() {
autoLocationEnabled = !autoLocationEnabled;
localStorage.setItem('autoLocation', autoLocationEnabled);

if (autoLocationEnabled) {
    startAutoLocation();
    showNotification('Автоопределение местоположения включено (каждые 30 сек)', 'success');
} else {
    stopAutoLocation();
    showNotification('Автоопределение местоположения выключено', 'info');
}

updateAutoLocationButton();
}

function updateAutoLocationButton() {
const btn = document.getElementById('autoLocationBtn');
if (btn) {
    if (autoLocationEnabled) {
        btn.innerHTML = '<i class="fas fa-satellite-dish"></i><span>Вкл</span>';
        btn.classList.add('active');
        btn.title = 'Автоопределение включено';
    } else {
        btn.innerHTML = '<i class="fas fa-satellite"></i><span>Выкл</span>';
        btn.classList.remove('active');
        btn.title = 'Автоопределение выключено';
    }
}
}

async function saveLocationOnce() {
showNotification('Определяем местоположение...', 'info');
try {
    await saveCurrentLocationToProfile();
    showNotification('✅ Местоположение сохранено!', 'success');
} catch (error) {
    showNotification('❌ Не удалось определить местоположение', 'error');
}
}

function initAutoLocation() {
const savedState = localStorage.getItem('autoLocation');
if (savedState === null) {
    autoLocationEnabled = true;
    localStorage.setItem('autoLocation', 'true');
} else {
    autoLocationEnabled = savedState === 'true';
}

if (autoLocationEnabled) {
    setTimeout(() => {
        startAutoLocation();
    }, 5000);
}

updateAutoLocationButton();
}

function showNotification(message, type) {
const notification = document.getElementById('notification');
notification.textContent = message;
notification.className = `notification ${type}`;
notification.style.display = 'block';
setTimeout(() => notification.style.display = 'none', 3000);
}

function logout() {
document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
localStorage.removeItem('authToken');
localStorage.removeItem('username');
localStorage.removeItem('userId');
localStorage.removeItem('userRole');
showNotification('Вы вышли из системы', 'info');
setTimeout(function() {
    window.location.href = '/';
}, 500);
}

function showAuthModal() {
const modal = document.getElementById('authModal');
if (modal) modal.style.display = 'flex';
}

function showRegisterModal() {
const modal = document.getElementById('registerModal');
if (modal) modal.style.display = 'flex';
}

function setCookie(name, value, days) {
if (days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "; expires=" + date.toUTCString();
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
} else {
    document.cookie = name + "=" + (value || "") + "; path=/";
}
}

function getCookie(name) {
const nameEQ = name + "=";
const ca = document.cookie.split(';');
for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
}
return null;
}

function deleteCookie(name) {
document.cookie = name + '=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
}

function acceptCookies() {
setCookie('cookie_consent', 'all', 365);
setCookie('cookie_functional', 'true', 365);
setCookie('cookie_analytics', 'true', 365);
document.getElementById('cookieConsent').style.display = 'none';
showNotification('Спасибо! Настройки cookies сохранены.', 'success');
setTimeout(() => location.reload(), 1000);
}

function declineCookies() {
setCookie('cookie_consent', 'necessary', 365);
setCookie('cookie_functional', 'false', 365);
setCookie('cookie_analytics', 'false', 365);

deleteCookie('auth_token');
deleteCookie('sessionid');
deleteCookie('csrftoken');

if (!getCookie('cookie_functional') || getCookie('cookie_functional') !== 'true') {
    localStorage.clear();
}

document.getElementById('cookieConsent').style.display = 'none';
showNotification('Cookies отклонены. Некоторые функции могут не работать.', 'info');
setTimeout(() => location.reload(), 1000);
}

function customizeCookies() {
document.getElementById('cookieSettings').style.display = 'flex';
}

function closeCookieSettings() {
document.getElementById('cookieSettings').style.display = 'none';
}

function saveCookieSettings() {
const functional = document.getElementById('cookieFunctional').checked;
const analytics = document.getElementById('cookieAnalytics').checked;

setCookie('cookie_consent', 'custom', 365);
setCookie('cookie_functional', functional ? 'true' : 'false', 365);
setCookie('cookie_analytics', analytics ? 'true' : 'false', 365);

if (!functional) {
    deleteCookie('auth_token');
    localStorage.clear();
}

if (!analytics) {
    deleteCookie('_ga');
    deleteCookie('_gid');
}

document.getElementById('cookieSettings').style.display = 'none';
document.getElementById('cookieConsent').style.display = 'none';
showNotification('Настройки cookies сохранены!', 'success');
setTimeout(() => location.reload(), 1000);
}

function acceptAllCookies() {
document.getElementById('cookieFunctional').checked = true;
document.getElementById('cookieAnalytics').checked = true;
saveCookieSettings();
}

function checkCookieConsent() {
const consent = getCookie('cookie_consent');

if (!consent) {
    setTimeout(() => {
        document.getElementById('cookieConsent').style.display = 'block';
    }, 1000);
} else {
    const functional = getCookie('cookie_functional') === 'true';
    const analytics = getCookie('cookie_analytics') === 'true';

    if (!functional) {
        localStorage.clear();
        deleteCookie('auth_token');
    }

    if (!analytics) {
        window['ga-disable-UA-XXXXX-X'] = true;
    }
}
}

function resetCookiesConsent() {
if (confirm('Вы уверены, что хотите сбросить настройки cookies?\n\nПосле этого потребуется повторное согласие на использование cookies.')) {
    deleteCookie('cookie_consent');
    deleteCookie('cookie_functional');
    deleteCookie('cookie_analytics');

    localStorage.clear();

    showNotification('Настройки cookies сброшены. Страница перезагрузится.', 'info');

    setTimeout(() => {
        location.reload();
    }, 1000);
}
}

document.addEventListener('DOMContentLoaded', function() {
checkCookieConsent();
initAutoLocation();
});

let notificationsCheckInterval = null;

async function loadNotifications() {
const token = localStorage.getItem('authToken');
if (!token) return;

try {
    const response = await fetch('/api/notifications/', {
        headers: { 'Authorization': `Token ${token}` }
    });
    const data = await response.json();
    displayNotifications(data);

    const unreadCount = data.filter(n => !n.is_read).length;
    const badge = document.getElementById('notificationCount');
    if (unreadCount > 0) {
        badge.textContent = unreadCount;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
} catch (error) {
    console.error('Ошибка загрузки уведомлений:', error);
}
}

function displayNotifications(notifications) {
const list = document.getElementById('notificationsList');
if (!list) return;

if (notifications.length === 0) {
    list.innerHTML = '<div class="notification-item">Нет уведомлений</div>';
    return;
}

list.innerHTML = notifications.map(n => `
    <div class="notification-item ${n.is_read ? '' : 'unread'}" onclick="openNotification(${n.id}, ${n.order || 0})">
        <div class="notification-title">${n.title}</div>
        <div class="notification-message">${n.message}</div>
        <div class="notification-time">${new Date(n.created_at).toLocaleString()}</div>
    </div>
`).join('');
}

async function openNotification(notificationId, orderId) {
const token = localStorage.getItem('authToken');

await fetch('/api/notifications/mark_as_read/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
    },
    body: JSON.stringify({ notification_id: notificationId })
});

if (orderId) {
    window.location.href = `/my-orders/`;
}

toggleNotifications();
}

async function markAllNotificationsRead() {
const token = localStorage.getItem('authToken');
await fetch('/api/notifications/mark_all_read/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
    }
});
loadNotifications();
}

function toggleNotifications() {
const panel = document.getElementById('notificationsPanel');
if (panel.style.display === 'none') {
    panel.style.display = 'block';
    loadNotifications();
} else {
    panel.style.display = 'none';
}
}

function startNotificationPolling() {
if (notificationsCheckInterval) {
    clearInterval(notificationsCheckInterval);
}

loadNotifications();

notificationsCheckInterval = setInterval(() => {
    loadNotifications();
}, 5000);
}

document.addEventListener('click', function(event) {
const panel = document.getElementById('notificationsPanel');
const bell = document.querySelector('.notification-bell');

if (panel && bell && !panel.contains(event.target) && !bell.contains(event.target)) {
    panel.style.display = 'none';
}
});

if (localStorage.getItem('authToken')) {
startNotificationPolling();
}
