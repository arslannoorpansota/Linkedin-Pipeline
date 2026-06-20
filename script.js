const yearElement = document.getElementById('year');
const contactForm = document.getElementById('contactForm');

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

if (contactForm) {
    contactForm.addEventListener('submit', event => {
        event.preventDefault();
        const name = document.getElementById('name').value.trim();
        alert(`Thanks, ${name}! Your message is ready to send. Please check your email client or reach out directly at faizan@example.com.`);
        contactForm.reset();
    });
}
