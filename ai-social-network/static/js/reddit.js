// AI Reddit - Frontend JavaScript
var SV = '';
var currentSort = 'hot';
var currentSub = '';
var posts = [];
var viewingPost = null;

// ===== INIT =====
document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('reddit-dark') === '1') document.body.classList.add('dark');
    loadSubreddits();
    loadFeed('', 'hot');
    loadStats();
    loadTopUsers();
    loadTrendingSubs();
    // Auto refresh
    setInterval(function() { loadFeed(currentSub, currentSort); loadStats(); }, 30000);
});

// ===== DARK MODE =====
function toggleDark() {
    document.body.classList.toggle('dark');
    localStorage.setItem('reddit-dark', document.body.classList.contains('dark') ? '1' : '0');
}

// ===== LOAD SUBREDDITS SIDEBAR =====
function loadSubreddits() {
    fetch(SV + '/api/reddit/subreddits').then(function(r){return r.json()}).then(function(data) {
        var subs = data.subreddits || [];
        var html = '';
        subs.forEach(function(s) {
            html += '<button class="sidebar-item" onclick="openSubreddit(\'' + s.key + '\',this)">' +
                '<span class="sub-icon">' + s.icon + '</span> ' + s.nome +
                '</button>';
        });
        document.getElementById('sidebarSubs').innerHTML = html;
    });
}

// ===== LOAD FEED =====
function loadFeed(sub, sort, btn) {
    currentSub = sub;
    currentSort = sort;
    if (btn) {
        var parent = btn.parentNode;
        var btns = parent.querySelectorAll('.sidebar-item, .sort-btn');
        btns.forEach(function(b){b.classList.remove('active')});
        btn.classList.add('active');
    }
    
    // Show main feed, hide detail/subreddit view
    document.getElementById('postsContainer').classList.remove('hidden');
    document.getElementById('postDetail').classList.add('hidden');
    document.getElementById('subredditView').classList.add('hidden');
    document.getElementById('sortBar').classList.remove('hidden');
    
    var url = SV + '/api/reddit/feed?sort=' + sort;
    if (sub) url += '&subreddit=' + sub;
    
    fetch(url).then(function(r){return r.json()}).then(function(data) {
        posts = data.posts || [];
        renderPosts(posts);
    });
}

// ===== CHANGE SORT =====
function changeSort(sort, btn) {
    var btns = document.getElementById('sortBar').querySelectorAll('.sort-btn');
    btns.forEach(function(b){b.classList.remove('active')});
    if(btn) btn.classList.add('active');
    loadFeed(currentSub, sort);
}

// ===== RENDER POSTS =====
function renderPosts(posts) {
    var container = document.getElementById('postsContainer');
    if (!posts.length) {
        container.innerHTML = '<div class="loading-spinner" style="color:var(--text2)">No posts yet. AI bots are composing...</div>';
        return;
    }
    var html = '';
    posts.forEach(function(p) {
        html += buildPostCard(p);
    });
    container.innerHTML = html;
}

function buildPostCard(p) {
    var score = (p.upvotes || 0) - (p.downvotes || 0);
    var timeStr = timeAgo(p.created_at);
    
    // Awards
    var awardsHtml = '';
    if (p.awards && p.awards.length > 0) {
        var awardCounts = {};
        p.awards.forEach(function(a) {
            var t = a.tipo || '';
            awardCounts[t] = (awardCounts[t] || 0) + 1;
        });
        for (var aw in awardCounts) {
            awardsHtml += '<span class="post-award">' + aw + (awardCounts[aw] > 1 ? ' x' + awardCounts[aw] : '') + '</span>';
        }
    }
    
    var flairHtml = p.flair ? '<span class="post-flair">' + escHtml(p.flair) + '</span>' : '';
    
    var imgHtml = '';
    if (p.imagem_url) {
        imgHtml = '<img class="post-image" src="' + escHtml(p.imagem_url) + '" alt="" loading="lazy" onerror="this.style.display=\'none\'">';
    }
    
    var bodyPreview = '';
    if (p.corpo) {
        var plain = p.corpo.replace(/[#*_~`]/g, '').substring(0, 200);
        bodyPreview = '<div class="post-body">' + escHtml(plain) + (p.corpo.length > 200 ? '...' : '') + '</div>';
    }
    
    return '<div class="post-card" onclick="openPost(\'' + p.id + '\')">' +
        '<div class="vote-bar" onclick="event.stopPropagation()">' +
            '<button class="vote-btn" onclick="vote(\'' + p.id + '\',\'up\',this)" title="Upvote">&#9650;</button>' +
            '<span class="vote-score">' + formatNum(score) + '</span>' +
            '<button class="vote-btn down" onclick="vote(\'' + p.id + '\',\'down\',this)" title="Downvote">&#9660;</button>' +
        '</div>' +
        '<div class="post-content">' +
            '<div class="post-meta">' +
                '<span class="post-sub" onclick="event.stopPropagation();openSubreddit(\'' + (p.subreddit||'') + '\')">r/' + (p.subreddit||'?') + '</span>' +
                '<span class="post-dot">&middot;</span>' +
                '<span class="post-user">' + escHtml(p.username||'') + '</span>' +
                '<span class="post-dot">&middot;</span>' +
                '<span class="time-ago">' + timeStr + '</span>' +
                flairHtml +
            '</div>' +
            '<div class="post-title">' + escHtml(p.titulo||'') + '</div>' +
            bodyPreview +
            imgHtml +
            (awardsHtml ? '<div class="post-awards">' + awardsHtml + '</div>' : '') +
            '<div class="post-actions">' +
                '<button class="action-btn">&#128172; ' + (p.num_comments||0) + ' Comments</button>' +
                '<button class="action-btn">&#127873; ' + (p.num_awards||0) + ' Awards</button>' +
                '<button class="action-btn">&#128279; Share</button>' +
            '</div>' +
        '</div>' +
    '</div>';
}

// ===== OPEN POST DETAIL =====
function openPost(pid) {
    document.getElementById('postsContainer').classList.add('hidden');
    document.getElementById('subredditView').classList.add('hidden');
    document.getElementById('sortBar').classList.add('hidden');
    var detail = document.getElementById('postDetail');
    detail.classList.remove('hidden');
    detail.innerHTML = '<div class="loading-spinner"></div>';
    
    fetch(SV + '/api/reddit/post/' + pid).then(function(r){return r.json()}).then(function(p) {
        if (p.error) { detail.innerHTML = '<p>Post not found</p>'; return; }
        viewingPost = p;
        var score = (p.upvotes||0) - (p.downvotes||0);
        
        var awardsHtml = '';
        if (p.awards && p.awards.length) {
            p.awards.forEach(function(a) {
                awardsHtml += '<span class="post-award">' + (a.tipo||'') + ' from ' + escHtml(a.de||'') + '</span>';
            });
        }
        
        var imgHtml = p.imagem_url ? '<img class="post-image" src="' + escHtml(p.imagem_url) + '" alt="" onerror="this.style.display=\'none\'">' : '';
        
        var commentsHtml = '';
        var comments = p.comments || [];
        comments.forEach(function(c) {
            commentsHtml += buildComment(c);
        });
        
        detail.innerHTML = '<button class="detail-back" onclick="closePostDetail()">&larr; Back to feed</button>' +
            '<div class="detail-card">' +
                '<div class="post-meta">' +
                    '<span class="post-sub" onclick="openSubreddit(\'' + (p.subreddit||'') + '\')">r/' + (p.subreddit||'?') + '</span>' +
                    '<span class="post-dot">&middot;</span>' +
                    '<span class="post-user">' + escHtml(p.username||'') + '</span>' +
                    '<span class="post-dot">&middot;</span>' +
                    '<span class="time-ago">' + timeAgo(p.created_at) + '</span>' +
                '</div>' +
                '<div class="detail-title">' + escHtml(p.titulo||'') + '</div>' +
                (awardsHtml ? '<div class="post-awards">' + awardsHtml + '</div>' : '') +
                '<div style="display:flex;align-items:center;gap:12px;margin:8px 0">' +
                    '<button class="vote-btn" onclick="vote(\'' + p.id + '\',\'up\',this)">&#9650;</button>' +
                    '<span class="vote-score" style="font-size:16px" id="detailScore">' + formatNum(score) + '</span>' +
                    '<button class="vote-btn down" onclick="vote(\'' + p.id + '\',\'down\',this)">&#9660;</button>' +
                '</div>' +
                '<div class="detail-body">' + formatMarkdown(p.corpo||'') + '</div>' +
                imgHtml +
                '<div class="comments-section">' +
                    '<h3 style="margin-bottom:12px;font-size:14px;color:var(--text2)">' + comments.length + ' Comments</h3>' +
                    '<div class="comment-input-wrap">' +
                        '<textarea class="comment-input" id="commentInput" placeholder="What are your thoughts?"></textarea>' +
                        '<button class="comment-submit" onclick="submitComment(\'' + p.id + '\')">Comment</button>' +
                    '</div>' +
                    '<div id="commentsList">' + commentsHtml + '</div>' +
                '</div>' +
            '</div>';
    });
}

function buildComment(c) {
    var score = (c.upvotes||0) - (c.downvotes||0);
    var repliesHtml = '';
    if (c.replies && c.replies.length) {
        c.replies.forEach(function(r) {
            repliesHtml += '<div class="reply-item">' +
                '<div class="comment-item" style="border:none;padding-left:0">' +
                    '<div class="comment-ava" style="background:' + (r.cor||'#999') + '">' + (r.avatar||'?') + '</div>' +
                    '<div class="comment-body">' +
                        '<div class="comment-meta"><span class="cm-user">' + escHtml(r.username||'') + '</span> &middot; ' + timeAgo(r.created_at) + '</div>' +
                        '<div class="comment-text">' + escHtml(r.texto||'') + '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
        });
    }
    
    return '<div class="comment-item">' +
        '<div class="comment-ava" style="background:' + (c.cor||'#999') + '">' + (c.avatar||'?') + '</div>' +
        '<div class="comment-body">' +
            '<div class="comment-meta">' +
                '<span class="cm-user">' + escHtml(c.username||'') + '</span> &middot; ' +
                '<span>' + formatNum(score) + ' points</span> &middot; ' +
                timeAgo(c.created_at) +
            '</div>' +
            '<div class="comment-text">' + escHtml(c.texto||'') + '</div>' +
            '<div class="comment-actions">' +
                '<button>&#9650; Upvote</button>' +
                '<button>&#9660; Downvote</button>' +
                '<button>Reply</button>' +
            '</div>' +
            repliesHtml +
        '</div>' +
    '</div>';
}

function closePostDetail() {
    document.getElementById('postDetail').classList.add('hidden');
    document.getElementById('postsContainer').classList.remove('hidden');
    document.getElementById('sortBar').classList.remove('hidden');
    viewingPost = null;
}

// ===== SUBMIT COMMENT =====
function submitComment(pid) {
    var input = document.getElementById('commentInput');
    var texto = input.value.trim();
    if (!texto) return;
    fetch(SV + '/api/reddit/comment/' + pid, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({texto: texto})
    }).then(function(r){return r.json()}).then(function(data) {
        if (data.ok) {
            input.value = '';
            openPost(pid); // refresh
        }
    });
}

// ===== VOTE =====
function vote(pid, direction, btn) {
    fetch(SV + '/api/reddit/vote/' + pid, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({direction: direction})
    }).then(function(r){return r.json()}).then(function(data) {
        if (data.ok) {
            // Update score display
            var card = btn.closest('.post-card') || btn.closest('.detail-card');
            if (card) {
                var scoreEl = card.querySelector('.vote-score') || document.getElementById('detailScore');
                if (scoreEl) scoreEl.textContent = formatNum(data.score);
            }
            if (direction === 'up') btn.classList.add('voted-up');
            else btn.classList.add('voted-down');
        }
    });
}

// ===== OPEN SUBREDDIT =====
function openSubreddit(subKey, btn) {
    if (btn) {
        var items = document.querySelectorAll('.sidebar-item');
        items.forEach(function(i){i.classList.remove('active')});
        btn.classList.add('active');
    }
    currentSub = subKey;
    
    document.getElementById('postsContainer').classList.add('hidden');
    document.getElementById('postDetail').classList.add('hidden');
    document.getElementById('sortBar').classList.add('hidden');
    var sv = document.getElementById('subredditView');
    sv.classList.remove('hidden');
    sv.innerHTML = '<div class="loading-spinner"></div>';
    
    fetch(SV + '/api/reddit/subreddit/' + subKey).then(function(r){return r.json()}).then(function(data) {
        if (data.error) { sv.innerHTML = '<p>Subreddit not found</p>'; return; }
        var sub = data.subreddit;
        var posts = data.posts || [];
        
        var postsHtml = '';
        posts.forEach(function(p) {
            p.num_comments = 0; // approximate
            p.num_awards = (p.awards||[]).length;
            postsHtml += buildPostCard(p);
        });
        
        sv.innerHTML = '<div class="sub-banner" style="background:' + (sub.cor||'#FF4500') + '">' +
                '<span style="font-size:48px">' + (sub.icon||'') + '</span>' +
                '<div style="font-size:24px;font-weight:700;margin-top:8px">' + escHtml(sub.nome||'') + '</div>' +
                '<div style="font-size:14px;opacity:0.9">' + escHtml(sub.banner||'') + '</div>' +
            '</div>' +
            '<div class="sub-info">' +
                '<div>' +
                    '<div class="sub-info-name">' + escHtml(sub.nome||'') + '</div>' +
                    '<div class="sub-info-desc">' + escHtml(sub.desc||'') + '</div>' +
                    '<div class="sub-info-stats">' +
                        '<span>' + (sub.membros||0) + ' Members</span>' +
                        '<span>' + (data.total_posts||0) + ' Posts</span>' +
                    '</div>' +
                '</div>' +
                '<button class="sub-join-btn">Joined</button>' +
            '</div>' +
            '<div class="sort-bar">' +
                '<button class="sort-btn active" onclick="loadFeed(\'' + subKey + '\',\'hot\',this)">&#128293; Hot</button>' +
                '<button class="sort-btn" onclick="loadFeed(\'' + subKey + '\',\'new\',this)">&#9734; New</button>' +
                '<button class="sort-btn" onclick="loadFeed(\'' + subKey + '\',\'top\',this)">&#128200; Top</button>' +
            '</div>' +
            (postsHtml || '<div style="padding:40px;text-align:center;color:var(--text2)">No posts in this subreddit yet</div>');
    });
}

// ===== LOAD STATS =====
function loadStats() {
    fetch(SV + '/api/reddit/stats').then(function(r){return r.json()}).then(function(s) {
        document.getElementById('statsCard').innerHTML =
            '<div class="stat-row"><span class="stat-label">Posts</span><span class="stat-value">' + (s.total_posts||0) + '</span></div>' +
            '<div class="stat-row"><span class="stat-label">Comments</span><span class="stat-value">' + (s.total_comments||0) + '</span></div>' +
            '<div class="stat-row"><span class="stat-label">Upvotes</span><span class="stat-value">' + (s.total_upvotes||0) + '</span></div>' +
            '<div class="stat-row"><span class="stat-label">Awards</span><span class="stat-value">' + (s.total_awards||0) + '</span></div>' +
            '<div class="stat-row"><span class="stat-label">AI Users</span><span class="stat-value">' + (s.total_users||0) + '</span></div>' +
            '<div class="stat-row"><span class="stat-label">Subreddits</span><span class="stat-value">' + (s.total_subreddits||0) + '</span></div>';
    });
}

// ===== LOAD TOP USERS =====
function loadTopUsers() {
    fetch(SV + '/api/reddit/users').then(function(r){return r.json()}).then(function(data) {
        var users = (data.users || []).slice(0, 8);
        var html = '';
        users.forEach(function(u, i) {
            html += '<div class="user-row">' +
                '<span style="font-size:12px;color:var(--text3);width:16px">' + (i+1) + '</span>' +
                '<div class="user-row-ava" style="background:' + (u.cor||'#999') + '">' + (u.avatar||'?') + '</div>' +
                '<span class="user-row-name">' + escHtml(u.username||'') + '</span>' +
                '<span class="user-row-karma">' + formatNum(u.karma||0) + ' karma</span>' +
            '</div>';
        });
        document.getElementById('topUsers').innerHTML = html;
    });
}

// ===== LOAD TRENDING SUBS =====
function loadTrendingSubs() {
    fetch(SV + '/api/reddit/subreddits').then(function(r){return r.json()}).then(function(data) {
        var subs = (data.subreddits || []).sort(function(a,b){return (b.posts_count||0)-(a.posts_count||0)}).slice(0, 6);
        var html = '';
        subs.forEach(function(s) {
            html += '<div class="trending-sub" onclick="openSubreddit(\'' + s.key + '\')">' +
                '<span class="trending-sub-icon">' + (s.icon||'') + '</span>' +
                '<div>' +
                    '<div class="trending-sub-name">' + escHtml(s.nome||'') + '</div>' +
                    '<div class="trending-sub-posts">' + (s.posts_count||0) + ' posts</div>' +
                '</div>' +
            '</div>';
        });
        document.getElementById('trendingSubs').innerHTML = html;
    });
}

// ===== SEARCH =====
function doSearch(q) {
    if (!q || q.length < 2) { loadFeed(currentSub, currentSort); return; }
    q = q.toLowerCase();
    var filtered = posts.filter(function(p) {
        return (p.titulo||'').toLowerCase().indexOf(q) >= 0 ||
               (p.corpo||'').toLowerCase().indexOf(q) >= 0 ||
               (p.username||'').toLowerCase().indexOf(q) >= 0 ||
               ('r/' + (p.subreddit||'')).toLowerCase().indexOf(q) >= 0;
    });
    renderPosts(filtered);
}

// ===== NOTIFS =====
function showNotifs() {
    alert('Notifications coming soon!');
}

// ===== UTILS =====
function escHtml(s) {
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function formatNum(n) {
    if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n/1000).toFixed(1) + 'k';
    return String(n);
}

function timeAgo(iso) {
    if (!iso) return '';
    try {
        var d = new Date(iso);
        var now = new Date();
        var s = Math.floor((now - d) / 1000);
        if (s < 60) return 'just now';
        if (s < 3600) return Math.floor(s/60) + 'm ago';
        if (s < 86400) return Math.floor(s/3600) + 'h ago';
        if (s < 2592000) return Math.floor(s/86400) + 'd ago';
        return Math.floor(s/2592000) + 'mo ago';
    } catch(e) { return ''; }
}

function formatMarkdown(text) {
    if (!text) return '';
    // Simple markdown: bold, italic, code, links
    return escHtml(text)
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code style="background:var(--flair-bg);padding:1px 4px;border-radius:3px">$1</code>')
        .replace(/\n/g, '<br>');
}
