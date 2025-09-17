import RegisterComponent from './Register.js';
import LoginComponent from './Login.js';

export default {
    components: { RegisterComponent, LoginComponent },
    template: `
        <register-component v-if="showRegister" @switch-to-login="switchToLogin" />
        <login-component v-else @switch-to-register="switchToRegister" />
    `,
    setup() {
        const { ref } = Vue;

        const showRegister = ref(true);

        const switchToLogin = () => {
            showRegister.value = false;
        };

        const switchToRegister = () => {
            showRegister.value = true;
        };

        return { showRegister, switchToLogin, switchToRegister };
    }
};