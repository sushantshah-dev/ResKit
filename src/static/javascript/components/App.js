import Viewer from './Viewer.js';
import Sidebar from './Sidebar.js';
import { apiCall } from '../utils/api.js';

export default {
    components: { Viewer, Sidebar },
    template: `
        <div class="sidebar">
            <Sidebar :projects="projects" :user="user" @project-created="handleProjectCreated" />
        </div>
        <div class="main-container">
            <div class="backdrop"></div>
            <div id="viewer" class="main">
                <Viewer :projects="projects" :user="user" />
            </div>
        </div>
    `,
    setup() {
        const { ref, onMounted } = Vue;
        const user = ref(null);
        const projects = ref([]);

        async function fetchProfile() {
            try {
                const data = await apiCall('/auth/profile', 'GET', null, true);
                if (data.message && data.message === "Token is invalid!") {
                    window.location.href = '/auth';
                    return;
                }
                user.value = data;
                console.log('Fetched user profile:', data);
            } catch (err) {
                console.error('Failed to fetch profile:', err);
            }
        }

        async function fetchProjects() {
            try {
                const data = await apiCall('/api/projects', 'GET', null, true);
                projects.value = data || [];
            } catch (err) {
                console.error('Error fetching projects:', err);
            }
        }

        function handleProjectCreated(newProject) {
            projects.value.push(newProject);
        }

        onMounted(() => {
            fetchProfile();
            fetchProjects();
        });

        return { user, projects, handleProjectCreated };
    }
};