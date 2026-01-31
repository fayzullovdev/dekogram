// Dekogram Professional JavaScript
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let selectedFile = null;

// API & Storage Helper
const api = {
    getTokens: () => JSON.parse(localStorage.getItem('tokens')),
    setTokens: (tokens) => localStorage.setItem('tokens', JSON.stringify(tokens)),
    clearTokens: () => localStorage.removeItem('tokens'),

    async fetch(url, options = {}) {
        const tokens = this.getTokens();
        const headers = { ...options.headers };

        if (tokens && tokens.access) {
            headers['Authorization'] = `Bearer ${tokens.access}`;
        }

        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method)) {
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrftoken) headers['X-CSRFToken'] = csrftoken;
        }

        options.headers = headers;
        let response = await fetch(url, options);

        if (response.status === 401 && tokens && tokens.refresh) {
            const refreshRes = await fetch('/api/token/refresh/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: tokens.refresh })
            });

            if (refreshRes.ok) {
                const newTokens = await refreshRes.json();
                this.setTokens({ ...tokens, access: newTokens.access });
                headers['Authorization'] = `Bearer ${newTokens.access}`;
                options.headers = headers;
                response = await fetch(url, options);
            } else {
                this.clearTokens();
                window.location.href = '/login/';
            }
        }
        return response;
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('feedContainer')) {
        loadStories();
        loadFeed();
        loadSuggestions();
        setupInfiniteScroll();
    }
    setupSearch();
});

// Search Functionality
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const searchIcon = document.querySelector('.search-icon');
    let debounceTimer;

    if (!searchInput || !searchResults) return;

    if (searchIcon) {
        searchIcon.style.cursor = 'pointer';
        searchIcon.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query) window.location.href = `/search/?q=${encodeURIComponent(query)}`;
        });
    }

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(debounceTimer);

        if (query.length === 0) {
            searchResults.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                // DRF standard is to use a trailing slash
                const res = await api.fetch(`/api/users/search/?q=${query}`);
                if (res.ok) {
                    const users = await res.json();
                    renderSearchResults(users);
                }
            } catch (err) {
                console.error('Search error:', err);
            }
        }, 300);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/search/?q=${encodeURIComponent(query)}`;
            }
        }
    });

    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length > 0) {
            searchResults.style.display = 'block';
        }
    });
}

function renderSearchResults(users) {
    const searchResults = document.getElementById('searchResults');
    const searchInput = document.getElementById('searchInput');
    searchResults.innerHTML = '';

    if (users.length === 0) {
        searchResults.innerHTML = `<div class="search-no-result">Bunday user yo'q</div>`;
    } else {
        users.slice(0, 5).forEach(user => {
            const div = document.createElement('a');
            div.className = 'search-result-item';
            div.href = `/profile/${user.username}/`;
            div.innerHTML = `
                <div class="avatar avatar-sm">
                    <img src="${user.avatar}" alt="${user.username}" onerror="this.src='/static/images/default-avatar.png'">
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 14px; color: var(--text-main);">${user.username} ${user.is_verified ? '<i class="fas fa-check-circle verified-badge" style="font-size: 12px;"></i>' : ''}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">${user.full_name}</div>
                </div>
            `;
            searchResults.appendChild(div);
        });

        if (users.length > 5) {
            const seeAll = document.createElement('a');
            seeAll.className = 'search-result-item';
            seeAll.style.justifyContent = 'center';
            seeAll.style.borderTop = '1px solid var(--border-color)';
            seeAll.href = `/search/?q=${encodeURIComponent(searchInput.value.trim())}`;
            seeAll.innerHTML = `<span style="font-weight: 700; color: var(--p-600); font-size: 13px;">See all results</span>`;
            searchResults.appendChild(seeAll);
        }
    }
    searchResults.style.display = 'block';
}

// Load Stories
async function loadStories() {
    try {
        const res = await api.fetch('/api/stories/');
        const data = await res.json();
        const list = document.getElementById('storiesList');
        if (!list) return;

        data.results?.forEach(story => {
            const div = document.createElement('div');
            div.className = 'story-item';
            div.innerHTML = `
                <div class="story-avatar ${story.is_viewed ? '' : 'avatar-story'}">
                    <div class="avatar avatar-lg">
                        <img src="${story.media}" alt="${story.user.username}" onerror="this.src='/static/images/default-avatar.png'">
                    </div>
                </div>
                <span class="story-username">${story.user.username}</span>
            `;
            list.appendChild(div);
        });
    } catch (e) { console.error('Stories error:', e); }
}

// Load Feed
async function loadFeed() {
    if (isLoading || !hasMore) return;
    isLoading = true;
    const loader = document.getElementById('loadingIndicator');
    if (loader) loader.style.display = 'flex';

    try {
        const res = await api.fetch(`/api/posts/?page=${currentPage}`);
        const data = await res.json();
        const container = document.getElementById('feedContainer');
        if (!container) return;

        data.results?.forEach(post => {
            const article = createPostElement(post);
            container.appendChild(article);
        });

        hasMore = !!data.next;
        currentPage++;
    } catch (e) { console.error('Feed error:', e); }
    finally {
        isLoading = false;
        if (loader) loader.style.display = 'none';
    }
}

function createPostElement(post) {
    const article = document.createElement('article');
    article.className = 'post-card';
    article.dataset.postId = post.id;
    const timeAgo = getTimeAgo(new Date(post.created_at));

    article.innerHTML = `
        <div class="post-header">
            <div class="post-user-info">
                <div class="avatar avatar-md pointer" onclick="window.location.href='/profile/${post.user.username}/'">
                    <img src="${post.user.avatar}" alt="${post.user.username}" onerror="this.src='/static/images/default-avatar.png'">
                </div>
                <div>
                    <div class="post-username pointer" onclick="window.location.href='/profile/${post.user.username}/'">
                        ${post.user.username} ${post.user.is_verified ? '<i class="fas fa-check-circle verified-badge"></i>' : ''}
                    </div>
                    ${post.location ? `<div class="post-location">${post.location}</div>` : ''}
                </div>
            </div>
            <button class="post-menu-btn"><i class="fas fa-ellipsis-h"></i></button>
        </div>
        
        <div class="post-media">
            ${post.media_type === 'video'
            ? `<video src="${post.media}" controls></video>`
            : `<img src="${post.media}" alt="Post">`}
        </div>
        
        <div class="post-actions">
            <button class="action-btn ${post.is_liked ? 'liked' : ''}" onclick="toggleLike(${post.id})">
                <i class="${post.is_liked ? 'fas' : 'far'} fa-heart"></i>
            </button>
            <button class="action-btn" onclick="focusComment(${post.id})">
                <i class="far fa-comment"></i>
            </button>
            <button class="action-btn" onclick="sharePost(${post.id})">
                <i class="far fa-paper-plane"></i>
            </button>
            <button class="action-btn ${post.is_saved ? 'saved' : ''}" onclick="toggleSave(${post.id})" style="margin-left: auto;">
                <i class="${post.is_saved ? 'fas' : 'far'} fa-bookmark"></i>
            </button>
        </div>
        
        <div class="post-likes">
            <span id="likes-${post.id}">${post.likes_count}</span> likes
        </div>
        
        <div class="post-caption">
            <span class="caption-username">${post.user.username}</span> ${post.caption}
        </div>
        
        <div class="view-comments pointer" onclick="showToast('Comments coming soon', 'info')">
            View all ${post.comments_count} comments
        </div>
        
        <div class="post-time">${timeAgo}</div>
        
        <div class="add-comment">
            <input type="text" class="comment-input" placeholder="Add a comment..." id="comment-input-${post.id}">
            <button class="post-btn" onclick="postComment(${post.id})">Post</button>
        </div>
    `;
    return article;
}

// Media Selection & Upload
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    selectedFile = file;

    const previewImg = document.getElementById('previewImage');
    const previewVid = document.getElementById('previewVideo');
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');
    const footer = document.getElementById('modalFooter');

    uploadArea.style.display = 'none';
    previewArea.style.display = 'block';
    footer.style.display = 'flex';

    const reader = new FileReader();
    reader.onload = (event) => {
        if (file.type.startsWith('image/')) {
            previewImg.src = event.target.result;
            previewImg.style.display = 'block';
            previewVid.style.display = 'none';
        } else {
            previewVid.src = event.target.result;
            previewVid.style.display = 'block';
            previewImg.style.display = 'none';
        }
    };
    reader.readAsDataURL(file);
}

function removePreview() {
    selectedFile = null;
    document.getElementById('uploadArea').style.display = 'flex'; // Changed to flex to keep layout
    document.getElementById('previewArea').style.display = 'none';
    document.getElementById('modalFooter').style.display = 'none';
    document.getElementById('mediaInput').value = '';
}

async function submitPost() {
    if (!selectedFile) return;

    const btn = document.getElementById('shareBtn');
    const loader = document.getElementById('shareBtnLoader');
    const text = document.getElementById('shareBtnText');

    btn.disabled = true;
    text.style.display = 'none';
    loader.style.display = 'inline-block';

    const formData = new FormData();
    formData.append('media', selectedFile);
    formData.append('caption', document.getElementById('caption').value);
    formData.append('location', document.getElementById('location').value);

    try {
        const res = await api.fetch('/api/posts/', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            showToast('Post shared successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            const err = await res.json();
            showToast(err.error || 'Failed to share post', 'error');

            // Re-enable in case of error
            btn.disabled = false;
            text.style.display = 'inline';
            loader.style.display = 'none';
        }
    } catch (e) {
        showToast('Network error', 'error');
        btn.disabled = false;
        text.style.display = 'inline';
        loader.style.display = 'none';
    }
}

// Interactions
async function toggleLike(postId) {
    try {
        const res = await api.fetch(`/api/posts/${postId}/like/`, { method: 'POST' });
        const data = await res.json();
        const card = document.querySelector(`[data-post-id="${postId}"]`);
        const btn = card.querySelector('.action-btn');
        const count = document.getElementById(`likes-${postId}`);

        btn.classList.toggle('liked', data.status === 'liked');
        btn.querySelector('i').className = data.status === 'liked' ? 'fas fa-heart' : 'far fa-heart';
        count.textContent = data.likes_count;
    } catch (e) { }
}

async function postComment(postId) {
    const input = document.getElementById(`comment-input-${postId}`);
    const text = input.value.trim();
    if (!text) return;
    try {
        const res = await api.fetch(`/api/posts/${postId}/comments/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        if (res.ok) { input.value = ''; showToast('Comment posted', 'success'); }
    } catch (e) { }
}

async function toggleSave(postId) {
    try {
        const res = await api.fetch(`/api/posts/${postId}/save_post/`, { method: 'POST' });
        const data = await res.json();
        const card = document.querySelector(`[data-post-id="${postId}"]`);
        const btn = card.querySelectorAll('.action-btn')[3];
        btn.classList.toggle('saved', data.status === 'saved');
        btn.querySelector('i').className = data.status === 'saved' ? 'fas fa-bookmark' : 'far fa-bookmark';
        showToast(data.status === 'saved' ? 'Saved' : 'Removed', 'info');
    } catch (e) { }
}

// Utils
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
    return Math.floor(seconds / 86400) + 'd ago';
}

function showToast(msg, type) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function openCreateModal() { document.getElementById('createModal').style.display = 'flex'; }
function closeCreateModal(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('createModal').style.display = 'none';
    removePreview();
}


// Story Upload
function openStoryUpload() {
    let input = document.getElementById('storyInput');
    if (!input) {
        input = document.createElement('input');
        input.type = 'file';
        input.id = 'storyInput';
        input.accept = 'image/*,video/*';
        input.style.display = 'none';
        document.body.appendChild(input);

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('media', file);

            // Show loading toast
            showToast('Uploading story...', 'info');

            try {
                const res = await api.fetch('/api/stories/', {
                    method: 'POST',
                    body: formData
                });

                if (res.ok) {
                    showToast('Story uploaded!', 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    const err = await res.json();
                    showToast(err.error || 'Failed to upload story', 'error');
                }
            } catch (err) {
                showToast('Network error', 'error');
            }

            // Clear input
            input.value = '';
        };
    }
    input.click();
}

function loadSuggestions() { }
function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 800) loadFeed();
    });
}
function toggleNotifications() { showToast('Notifications feature coming soon', 'info'); }
function sharePost(id) { navigator.clipboard.writeText(window.location.origin + '/post/' + id); showToast('Link copied!', 'success'); }
