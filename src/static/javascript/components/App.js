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
        const { ref } = Vue;
        const user = ref(null);
        const projects = ref([]);

        async function fetchProfile() {
            await apiCall('/auth/profile', 'GET', null, true).then((data) => {
                user.value = data;
            }).catch((err) => {
                console.error('Error fetching profile:', err);
                window.location.href = '/auth';
            });
        }

        async function fetchProjects() {
            await apiCall('/api/projects', 'GET', null, true).then((data) => {
                projects.value = data || [];
            }).catch((err) => {
                console.error('Error fetching projects:', err);
            });
        }

        function handleProjectCreated(newProject) {
            projects.value.push(newProject);
        }

        return { user, projects, handleProjectCreated, fetchProfile, fetchProjects };
    },
    created() {
        this.fetchProfile();
        this.fetchProjects();
    }
};