import { apiCall } from '../../utils/api.js';

export default {
    template: `
    <div class="auth-container">
        <h2>Register</h2>
        <form @submit.prevent="register">
            <input v-model="username" type="text" placeholder="Username" required />
            <input v-model="email" type="email" placeholder="Email" required />
            <input v-model="password" type="password" placeholder="Password" required />
            <button type="submit">Register</button>
            <span class="switcher">Already have an account? <a href="#" @click="$emit('switch-to-login')">Login here</a></span>
        </form>
        <p v-if="message">{{ message }}</p>
    </div>
    `,
    setup() {
        const { ref } = Vue;
        
        const username = ref('');
        const email = ref('');
        const password = ref('');
        const message = ref('');

        const register = async () => {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username.value,
                    email: email.value,
                    password: password.value
                })
            });
            const data = await response.json();
            if (data.token) {
                localStorage.setItem('token', data.token);
                window.location.href = '/app';
            } else {
                message.value = data.message;
            }
        };

        return { username, email, password, message, register };
    }
};