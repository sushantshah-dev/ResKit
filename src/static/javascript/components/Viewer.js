import Chat from './Chat.js';
import Search from './Search.js';

export default {
    components: { Chat, Search },
    props: ['projects', 'user'],
    template: `
        <div class="main">
            <div class="views">
                <button :class="['view-option', { active: activeView === 'chat' }]" @click="setView('chat')">
                    <ion-icon name="chatbubbles-outline"></ion-icon>
                </button>
                <button :class="['view-option', { active: activeView === 'search' }]" @click="setView('search')">
                    <ion-icon name="search-outline"></ion-icon>
                </button>
            </div>
            <component :is="activeViewComponent" :project-id="projectId" :user="user"></component>
        </div>
    `,
    setup(props) {
        const { ref, computed, watch } = Vue;
        const activeView = ref('chat');
        const projectId = ref(null);

        function resolveProjectId(projects) {
            const urlParams = new URLSearchParams(window.location.search);
            let pid = urlParams.get('project_id');
            if (pid) return pid;
            if (projects && projects.length > 0) return projects[0].id;
            return null;
        }

        watch(() => props.projects, (projects) => {
            projectId.value = resolveProjectId(projects);
        }, { immediate: true });

        function setView(view) {
            activeView.value = view;
        }
        const activeViewComponent = computed(() => {
            if (activeView.value === 'chat') return 'Chat';
            if (activeView.value === 'search') return 'Search';
            return null;
        });
        return { activeView, setView, activeViewComponent, projectId, user: props.user };
    }
};