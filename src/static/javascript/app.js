import App from './components/App.js';

window.prompt = (query) => {
    const overlay = document.createElement('div');
    overlay.classList.add('overlay');
    const box = document.createElement('div');
    box.classList.add('box');
    const message = document.createElement('p');
    message.textContent = query;
    const input = document.createElement('input');
    input.type = 'text';
    const buttons = document.createElement('div');

    const okButton = document.createElement('button');
    okButton.textContent = 'OK';
    const cancelButton = document.createElement('button');
    cancelButton.textContent = 'Cancel';
    buttons.appendChild(okButton);
    buttons.appendChild(cancelButton);
    box.appendChild(message);
    box.appendChild(input);
    box.appendChild(buttons);
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    return new Promise((resolve) => {
        okButton.onclick = () => {
            const value = input.value;
            document.body.removeChild(overlay);
            resolve(value);
        };
        cancelButton.onclick = () => {
            document.body.removeChild(overlay);
            resolve(null);
        };
    });
};

if (!localStorage.getItem('token')) {
    window.location.href = '/auth';
}

const { createApp } = Vue;
createApp(App).mount('#app');
