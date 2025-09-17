import { apiCall } from '../utils/api.js';
const { onUnmounted } = Vue;

const PaperCard = {
    props: ['card'],
    template: `
        <div class="paper-card">
            <h3>{{ card.title }}</h3>
            <p class="authors"><strong>Authors:</strong> {{ card.authors.join(', ') }}</p>
            <p class="published">Published on {{ formatDate(card.published) }}</p>
            <p class="summary">{{ card.summary }}</p>
            <a v-if="card.pdf_link" :href="card.pdf_link" target="_blank">PDF</a>
        </div>
    `,
    methods: {
        formatDate(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            if (isNaN(date)) return dateStr;
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: '2-digit'
            });
        }
    }
};

const MessageComponent = {
    components: { PaperCard },
    props: ['message', 'noName', 'name'],
    template: `
        <div :class="['message', message.role === 'user' ? 'user' : 'ai']">
            <span v-if="!noName" :class="message.role === 'user' ? 'user-tag' : 'ai-tag'">
                {{ name }}
            </span>
            <span v-if="message.user_id === 'system' && message.content[0].text !== ''" :class="'ai-msg'" v-html="message.content[0].text"></span>
            <span v-else-if="user && message.user_id === user.id" :class="'user-msg'">
                {{ message.content[0].text }}
            </span>
            <PaperCard :card="message.content[0].text" v-else-if="message.user_id === 'card'" />
            <span v-else :class="'peer-msg'">
                {{ message.content[0].text }}
            </span>
        </div>
    `,
    setup(props) {
        return { user: null };
    }
};

export default {
    components: { MessageComponent },
    props: ['projectId', 'user'],
    template: `
        <div class="view">
            <div :class="['chat-box', messages.length === 0 ? 'empty' : '']">
                <div class="chat-attachments" id="chat-attachments"></div>
                <button class="attach-button" @click="addAttachments">
                    <ion-icon name="attach-outline"></ion-icon>
                </button>
                <input v-model="newMessage" type="text" class="chat-input" placeholder="Type your message..." @keyup.enter="sendMessage">
                <button class="send-button" @click="sendMessage">
                    <ion-icon name="send"></ion-icon>
                </button>
            </div>
            <div v-if="messages.length > 0" class="messages-list" ref="messagesList">
                <MessageComponent :message="msg" v-for="(msg, idx) in messages" :key="idx" :noName="idx > 0 && messages[idx - 1].user_id === msg.user_id" :name="msg.username"></MessageComponent>
            </div>
        </div>
    `,
    setup(props) {
        const { ref, onMounted, watch } = Vue;
        const messages = ref([]);
        const newMessage = ref('');
        const loading = ref(false);
        const messagesList = ref(null);
        const lastread = ref(null);
        const attachments = ref([]);
        const socket = ref(null);
        const connected = ref(false);

        async function addAttachments() {
            try {
                const handles = await window.showOpenFilePicker({
                    multiple: true,
                    types: [
                        {
                            description: 'PDF Files',
                            accept: { 'application/pdf': ['.pdf'] }
                        },
                        {
                            description: 'Image Files',
                            accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.gif'] }
                        },
                        {
                            description: 'Text Files',
                            accept: { 'text/plain': ['.txt'] }
                        }
                    ]
                });

                const files = await Promise.all(
                    handles.map(async (handle) => {
                        const file = await handle.getFile();
                        file.handle = handle;
                        return file;
                    })
                );
                await Promise.all(files.map(async (file) => {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('project_id', props.projectId);
                    try {
                        const data = await apiCall('/api/upload', 'POST', formData, true);
                        const file_id = data.filename;
                        const card = document.createElement('div');
                        attachments.value.push(file_id);
                        card.className = 'attachment-card';
                        if (file.type.startsWith('image/')) {
                            card.innerHTML = `<img src="${URL.createObjectURL(file)}" alt="${file.name}" class="attachment-image">`;
                        } else {
                            card.innerHTML = `<p>${file.name}</p>`;
                        }
                        const removeBtn = document.createElement('button');
                        removeBtn.className = 'remove-attachment';
                        removeBtn.onclick = () => {
                            card.remove();
                            attachments.value = attachments.value.filter(f => f !== file_id);
                        }
                        removeBtn.innerHTML = '&times;';
                        card.appendChild(removeBtn);
                        document.getElementById('chat-attachments').appendChild(card);
                    } catch (error) {
                        console.error('Upload error:', error);
                    }
                }));
            } catch (error) {
                console.error('Error selecting files:', error);
            }
        }

        async function sendMessage() {
            if (newMessage.value.trim() === '' || loading.value) return;
            const message = newMessage.value.trim();
            newMessage.value = '';
            const attachmentsList = attachments.value;
            attachments.value = [];
            document.querySelector("#chat-attachments").innerHTML = "";
            
            const bodyObj = {
                project_id: props.projectId,
                message: message,
                attachments: attachmentsList
            };
            apiCall('/api/send-message', 'POST', bodyObj, true).catch((err) => {
                console.error('Error sending message:', err);
            });
        }

        onMounted(() => {
            socket.value = io();
            socket.value.on('connect', () => {
                connected.value = true;
                console.log('Socket connected');
                if (props.projectId) {
                    socket.value.emit('join', { projectId: props.projectId });
                }
            });
            socket.value.on('disconnect', () => {
                connected.value = false;
                console.log('Socket disconnected');
            });
            socket.value.on('new_message', (data) => {
                console.log('New message received:', data);
                if (data.role === 'assistant' && data.content && data.content.length > 0 && data.content[0].type === 'text') {
                    data.content[0].text = marked.parse(data.content[0].text);
                }
                messages.value.push(data);
            });
            socket.value.on('new_card', (data) => {
                console.log('New cards received:', data);
            });

            watch(() => props.projectId, (newVal) => {
                if (newVal) {
                    messages.value = [];
                    lastread.value = null;
                    if (socket.value && connected.value) {
                        socket.value.emit('join', { projectId: newVal });
                    }
                    fetchInitialMessages(newVal);
                }
            }, { immediate: true });

            watch(messages, () => {
                if (messagesList.value) {
                    messagesList.value.scrollTop = messagesList.value.scrollHeight;
                }
            });
        });

        async function fetchInitialMessages(projectId) {
            await apiCall(`/api/read-messages/${projectId}`, 'GET', null, true).then((data) => {
                data.forEach(msg => {
                    if (msg.role === 'assistant' && msg.content && msg.content.length > 0 && msg.content[0].type === 'text') {
                        msg.content[0].text = marked.parse(msg.content[0].text);
                    }
                    messages.value.push(msg);
                });
                console.log('Initial messages loaded:', data);
                if (data.length > 0) {
                    lastread.value = new Date(data[data.length - 1].timestamp);
                }
            } catch (err) {
                console.error('Error fetching initial messages:', err);
            }
        }

        onUnmounted(() => {
            if (socket.value) {
                socket.value.emit('leave', { projectId: props.projectId });
                socket.value.disconnect();
            }
        });

        return { messages, newMessage, loading, sendMessage, addAttachments, messagesList, connected };
    }
};