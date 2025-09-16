import { apiCall } from '../utils/api.js';

export default {
    props: ['projects', 'user'],
    template: `
        <div class="top">
            <button id="new-project" class="icon-button" title="New Project" @click="createNewProject">
                <span class="button-content">
                    <ion-icon name="add-circle-outline"></ion-icon>
                    <span style="margin-left: 8px;">New Project</span>
                </span>
            </button>
            <hr>
            <div class="project-list">
                <div v-for="project in projects" :key="project.id" class="project-item" @click="openProject(project.id)">
                    <span>{{ project.name }}</span>
                </div>
            </div>
        </div> 
        <div class="bottom">
            <button id="user-icon" class="icon-button" title="User" @click="goToAuth">
                <span class="button-content">
                    <ion-icon name="person-circle-outline"></ion-icon>
                    <span style="margin-left: 8px;">Account</span>
                </span>
            </button>
        </div>
    `,
    setup(props, { emit }) {
        function goToAuth() {
            window.location.href = '/auth';
        }

        async function createNewProject() {
            const name = await window.prompt('Enter project name:');
            if (!name) return;
            try {
                const data = await apiCall('/api/projects', 'POST', { name }, true);
                emit('project-created', data.project);
                window.location.href = `/app?project_id=${data.project.id}`;
            } catch (err) {
                console.error('Error creating project:', err);
            }
        }

        function openProject(projectId) {
            window.location.href = `/app?project_id=${projectId}`;
        }

        return { goToAuth, createNewProject, openProject };
    }
};