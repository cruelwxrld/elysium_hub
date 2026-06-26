function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showCancelReasonModal(orderId) {
    document.getElementById('cancelOrderId').value = orderId;
    document.getElementById('cancelReasonModal').style.display = 'flex';
    document.getElementById('cancelReasonForm').action = `/cancel-order/${orderId}/`;
}

function closeCancelReasonModal() {
    document.getElementById('cancelReasonModal').style.display = 'none';
    document.getElementById('cancelReasonForm').reset();
}

document.getElementById('cancelReasonForm')?.addEventListener('submit', function(e) {
    const reason = document.querySelector('#cancelReasonForm textarea[name="reason"]').value;
    if (!reason) {
        showNotification('Укажите причину отмены', 'error');
        e.preventDefault();
    }
});

let currentOrderId = null;

function openReviewModal(orderId, performerName) {
    currentOrderId = orderId;
    document.getElementById('reviewOrderId').value = orderId;
    document.getElementById('reviewPerformerName').textContent = performerName;
    document.getElementById('reviewModal').style.display = 'flex';
    resetRatingStars();
}

function closeReviewModal() {
    document.getElementById('reviewModal').style.display = 'none';
    document.getElementById('reviewForm').reset();
    currentOrderId = null;
}

let currentRating = 0;

function setRating(rating) {
    currentRating = rating;
    document.getElementById('ratingValue').value = rating;

    const stars = document.querySelectorAll('.rating-stars i');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.remove('far');
            star.classList.add('fas');
            star.classList.add('active');
        } else {
            star.classList.remove('fas');
            star.classList.add('far');
            star.classList.remove('active');
        }
    });
}

function resetRatingStars() {
    currentRating = 0;
    document.getElementById('ratingValue').value = '';
    const stars = document.querySelectorAll('.rating-stars i');
    stars.forEach(star => {
        star.classList.remove('fas');
        star.classList.remove('active');
        star.classList.add('far');
    });
}

document.getElementById('reviewForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const orderId = document.getElementById('reviewOrderId').value;
    const rating = document.getElementById('ratingValue').value;
    const comment = document.querySelector('[name="comment"]').value;

    if (!rating) {
        showNotification('Пожалуйста, поставьте оценку', 'error');
        return;
    }

    try {
        const token = localStorage.getItem('authToken');
        const csrftoken = getCookie('csrftoken');

        const response = await fetch('/api/reviews/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`,
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                order: parseInt(orderId),
                rating: parseInt(rating),
                comment: comment
            })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Спасибо за вашу оценку!', 'success');
            closeReviewModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification(data.error || 'Ошибка при отправке оценки', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('Ошибка соединения', 'error');
    }
});

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        setTimeout(() => notification.style.display = 'none', 3000);
    }
}