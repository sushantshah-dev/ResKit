import { apiCall } from '../../utils/api.js';

export default {
    template: `
    <div class="auth-container">
        <h2>Login</h2>
        <form @submit.prevent="login">
            <input v-model="email" type="email" placeholder="Email" required />
            <input v-model="password" type="password" placeholder="Password" required />
            <button type="submit">Login</button>
            <span class="switcher">Don't have an account? <a href="#" @click="$emit('switch-to-register')">Register here</a></span>
        </form>
        <p v-if="message">{{ message }}</p>
    </div>
    `,
    setup() {
        const { ref, onMounted } = Vue;
        
        const email = ref('');
        const password = ref('');
        const message = ref('');

        const login = async () => {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email.value,
                    password: password.value
                })
            });
            const data = await response.json();
            console.log(data);
            if (data.token) {
                localStorage.setItem('token', data.token);
                window.location.href = '/app';
            } else {
                message.value = data.message;
            }
        };

        return { email, password, message, login };
    }
};
