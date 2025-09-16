import { apiCall } from '../utils/api.js';

export default {
    template: `
        <div class="search-view view">
            <div :class="['search-box', query.length === 0 ? 'empty' : '']">
                <div class="search-input-container">
                <input v-model="query" type="text" class="search-input" placeholder="Search for papers...">
                <div class="search-chips">
                    <button
                        v-for="cat in categories"
                        :key="cat.value"
                        :class="['chip', { active: category === cat.value }]"
                        type="button"
                        @click="category = cat.value"
                    >
                        {{ cat.label }}
                    </button>
                </div>
                </div>
                <button class="search-button" @click="performSearch">
                    <ion-icon name="search"></ion-icon>
                </button>
            </div>
            <div class="search-output">
                <div v-if="loading" class="search-loading">Searching...</div>
                <div v-if="error" class="search-error">{{ error }}</div>
                <div v-if="results.length > 0" class="search-results">
                    <div v-for="(paper, idx) in results" :key="idx" class="search-result">
                        <h3>{{ paper.title }}</h3>
                        <p><strong>Authors:</strong> {{ paper.authors.join(', ') }}</p>
                        <p><strong>Published:</strong> {{ paper.published }}</p>
                        <p>{{ paper.summary }}</p>
                        <a v-if="paper.pdf_link" :href="paper.pdf_link" target="_blank">PDF</a>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() {
        const { ref } = Vue;
        const query = ref('');
        const category = ref('all');
        const categories = [
            { label: 'All', value: 'all' },
            { label: 'Papers', value: 'papers' },
            { label: 'Authors', value: 'authors' },
            { label: 'Topics', value: 'topics' }
        ];
        const results = ref([]);
        const loading = ref(false);
        const error = ref('');
        async function performSearch() {
            if (!query.value.trim()) return;
            loading.value = true;
            error.value = '';
            try {
                const params = new URLSearchParams({
                    q: query.value,
                    category: category.value
                });
                const data = await apiCall(`/api/search?${params}`, 'GET', null, true);
                results.value = data.results || [];
            } catch (err) {
                error.value = 'Search failed: ' + err.message;
                results.value = [];
            } finally {
                loading.value = false;
            }
        }
        return { query, category, categories, results, loading, error, performSearch };
    }
};