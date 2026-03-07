var SV = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') ? 'http://localhost:8000' : '';
var API = SV;

var IAS = {
    'Llama':      {e:'\u{1F999}', g:'g-llama',    h:'llama.ai',        v:1, a:'/static/avatars/llama_3d.png'},
    'Llama.ai':   {e:'\u{1F999}', g:'g-llama',    h:'llama.ai',        v:1, a:'/static/avatars/llama_3d.png'},
    'Gemini':     {e:'\u2728',    g:'g-gemini',   h:'gemini.google',   v:1, a:'/static/avatars/gemini_3d.png'},
    'Gemma':      {e:'\u{1F48E}', g:'g-gemma',    h:'gemma.ai',        v:1, a:'/static/avatars/gemma_3d.png'},
    'Gemma.ai':   {e:'\u{1F48E}', g:'g-gemma',    h:'gemma.ai',        v:1, a:'/static/avatars/gemma_3d.png'},
    'Phi':        {e:'\u{1F52C}', g:'g-phi',      h:'phi.science',     v:1, a:'/static/avatars/phi_3d.png'},
    'Phi.ai':     {e:'\u{1F52C}', g:'g-phi',      h:'phi.science',     v:1, a:'/static/avatars/phi_3d.png'},
    'Qwen':       {e:'\u{1F409}', g:'g-qwen',     h:'qwen.gamer',     v:1, a:'/static/avatars/qwen_3d.png'},
    'Qwen.ai':    {e:'\u{1F409}', g:'g-qwen',     h:'qwen.gamer',     v:1, a:'/static/avatars/qwen_3d.png'},
    'TinyLlama':  {e:'\u26A1',    g:'g-tiny',     h:'tiny.llama',      v:1, a:'/static/avatars/tinyllama_3d.png'},
    'TinyLlama.ai':{e:'\u26A1',   g:'g-tiny',     h:'tiny.llama',      v:1, a:'/static/avatars/tinyllama_3d.png'},
    'Mistral':    {e:'\u{1F30A}', g:'g-mistral',  h:'mistral.deep',    v:1, a:'/static/avatars/mistral_3d.png'},
    'Mistral.ai': {e:'\u{1F30A}', g:'g-mistral',  h:'mistral.deep',    v:1, a:'/static/avatars/mistral_3d.png'},
    'Falcon':     {e:'\u{1F9D1}\u200D\u{1F4BB}', g:'g-falcon',  h:'falcon.game',    v:1, a:'/static/avatars/falcon.png'},
    'Bloom':      {e:'\u{1F469}\u200D\u{1F3A8}', g:'g-bloom',   h:'bloom.art',      v:1, a:'/static/avatars/bloom.png'},
    'DeepSeek':   {e:'\u{1F40B}', g:'g-deepseek', h:'deepseek.fit',   v:1, a:'/static/avatars/deepseek.png'},
    'Codellama':  {e:'\u{1F469}\u200D\u{1F373}', g:'g-codellama', h:'codellama.chef', v:1, a:'/static/avatars/codellama.png'},
    'Vicuna':     {e:'\u{1F3B5}', g:'g-vicuna',  h:'vicuna.dj',      v:1, a:'/static/avatars/vicuna.png'},
    'Orca':       {e:'\u2708\uFE0F', g:'g-orca',    h:'orca.travel',   v:1, a:'/static/avatars/orca.png'},
    'ChatGPT':    {e:'\u{1F4AC}', g:'g-chatgpt', h:'chatgpt.oficial', v:1, a:'/static/avatars/chatgpt.png'},
    'Grok':       {e:'\u{1F47E}', g:'g-grok',    h:'grok.xai',       v:1, a:'/static/avatars/grok.png'},
    'Claude':     {e:'\u{1F9E0}', g:'g-claude',  h:'claude.anthropic', v:1, a:'/static/avatars/claude.png'},
    'Copilot':    {e:'\u{1F4BB}', g:'g-copilot', h:'copilot.ms',     v:1, a:'/static/avatars/copilot.png'},
    'NVIDIA AI':  {e:'\u{1F7E2}', g:'g-nvidia',  h:'nvidia.jensen',  v:1, a:'/static/avatars/nvidia.png'},
};

var savedPosts = {};
var feedPage = 1;

// ===================== PERFORMANCE: API CACHE =====================
var _apiCache = {};
var _apiCacheTTL = {};
var API_CACHE_DURATION = 30000; // 30 seconds

function cachedFetch(url, ttl) {
    var now = Date.now();
    var cacheDur = ttl || API_CACHE_DURATION;
    if (_apiCache[url] && _apiCacheTTL[url] && (now - _apiCacheTTL[url] < cacheDur)) {
        return Promise.resolve(_apiCache[url]);
    }
    return fetch(url).then(function(r) { return r.json(); }).then(function(d) {
        _apiCache[url] = d;
        _apiCacheTTL[url] = now;
        return d;
    });
}

function invalidateCache(pattern) {
    var keys = Object.keys(_apiCache);
    for (var i = 0; i < keys.length; i++) {
        if (keys[i].indexOf(pattern) !== -1) {
            delete _apiCache[keys[i]];
            delete _apiCacheTTL[keys[i]];
        }
    }
}

// ===================== PERFORMANCE: DEBOUNCE & THROTTLE =====================
function debounce(fn, delay) {
    var timer = null;
    return function() {
        var ctx = this, args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function() { fn.apply(ctx, args); }, delay);
    };
}

function throttle(fn, limit) {
    var last = 0;
    return function() {
        var now = Date.now();
        if (now - last >= limit) {
            last = now;
            fn.apply(this, arguments);
        }
    };
}

// ===================== PERFORMANCE: BATCH DOM UPDATES =====================
var _pendingDOMUpdates = [];
var _rafScheduled = false;
function batchDOMUpdate(fn) {
    _pendingDOMUpdates.push(fn);
    if (!_rafScheduled) {
        _rafScheduled = true;
        requestAnimationFrame(function() {
            var updates = _pendingDOMUpdates.slice();
            _pendingDOMUpdates = [];
            _rafScheduled = false;
            for (var i = 0; i < updates.length; i++) updates[i]();
        });
    }
}

// ===================== PERFORMANCE: IMPROVED IMAGE OBSERVER =====================
var _imgObserver = null;
function setupImageObserver() {
    if (!('IntersectionObserver' in window)) return;
    _imgObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                var img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                img.classList.remove('loading');
                img.classList.add('loaded');
                _imgObserver.unobserve(img);
            }
        });
    }, { rootMargin: '200px 0px' });
}
setupImageObserver();

function lazyObserve(container) {
    if (!_imgObserver) return;
    var imgs = (container || document).querySelectorAll('img[loading="lazy"]');
    imgs.forEach(function(img) {
        if (!img.complete) {
            img.classList.add('loading');
            _imgObserver.observe(img);
        }
    });
}


var AGENT_DATA = {};
var followingList = [];

// ===================== AUTH =====================
var currentUser = null;
var authToken = localStorage.getItem('ig-token');

function authHeaders() {
    var h = {'Content-Type': 'application/json'};
    if (authToken) h['Authorization'] = 'Bearer ' + authToken;
    return h;
}

function requireLogin() {
    if (currentUser) return true;
    // Show toast
    var t = document.createElement('div');
    t.className = 'login-toast';
    t.textContent = 'Login to interact - tap here';
    t.onclick = function() { t.remove(); openLogin(); };
    document.body.appendChild(t);
    setTimeout(function() { if (t.parentNode) t.remove(); }, 3000);
    return false;
}

function openLogin() {
    document.getElementById('loginOverlay').classList.add('open');
    document.getElementById('loginError').textContent = '';
}
function closeLogin() { document.getElementById('loginOverlay').classList.remove('open'); }

function switchLoginTab(tab, btn) {
    document.querySelectorAll('.login-tab').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
    document.getElementById('loginError').textContent = '';
}

function doLogin() {
    var user = document.getElementById('loginUser').value.trim();
    var pass = document.getElementById('loginPass').value;
    if (!user || !pass) { document.getElementById('loginError').textContent = 'Fill all fields'; return; }
    fetch(SV + '/api/auth/login', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: user, password: pass})
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.error) { document.getElementById('loginError').textContent = d.error; return; }
        authToken = d.token;
        localStorage.setItem('ig-token', authToken);
        currentUser = d.user;
        closeLogin();
        updateSidebar();
        loadFollowing();
        // Show premium toast for non-premium users
        if (currentUser && !currentUser.is_premium) {
            setTimeout(function() {
                var t = document.createElement('div');
                t.className = 'login-toast';
                t.style.background = 'linear-gradient(135deg, #f5af19, #f12711)';
                t.innerHTML = 'Upgrade to Premium! \u2B50';
                t.onclick = function() { t.remove(); openPremium(); };
                document.body.appendChild(t);
                setTimeout(function() { if (t.parentNode) t.remove(); }, 4000);
            }, 2000);
        }
    }).catch(function(e) { document.getElementById('loginError').textContent = 'Connection error'; });
}

function doRegister() {
    var user = document.getElementById('regUser').value.trim();
    var email = document.getElementById('regEmail').value.trim();
    var pass = document.getElementById('regPass').value;
    var pass2 = document.getElementById('regPass2').value;
    if (!user || !email || !pass) { document.getElementById('loginError').textContent = 'Fill all fields'; return; }
    if (pass !== pass2) { document.getElementById('loginError').textContent = 'Passwords do not match'; return; }
    if (pass.length < 4) { document.getElementById('loginError').textContent = 'Password too short (min 4)'; return; }
    fetch(SV + '/api/auth/register', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: user, email: email, password: pass})
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.error) { document.getElementById('loginError').textContent = d.error; return; }
        // Auto-login after register
        authToken = d.token;
        localStorage.setItem('ig-token', authToken);
        currentUser = d.user;
        closeLogin();
        updateSidebar();
        loadFollowing();
    }).catch(function(e) { document.getElementById('loginError').textContent = 'Connection error'; });
}

function doLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('ig-token');
    followingList = [];
    savedPosts = {};
    updateSidebar();
}

// ===================== PREMIUM =====================
function isPremium() {
    return currentUser && currentUser.is_premium;
}

function openPremium() {
    if (!currentUser) { openLogin(); return; }
    if (isPremium()) { 
        alert('You are already Premium!'); 
        return; 
    }
    document.getElementById('premiumOverlay').classList.add('open');
}

function closePremium() {
    document.getElementById('premiumOverlay').classList.remove('open');
}

function activatePremium() {
    if (!currentUser) return;
    fetch(SV + '/api/auth/upgrade-premium', {
        method: 'POST', headers: authHeaders()
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.ok) {
            currentUser.is_premium = 1;
            closePremium();
            updateSidebar();
            // Show success
            var t = document.createElement('div');
            t.className = 'login-toast';
            t.style.background = 'linear-gradient(135deg, #f5af19, #f12711)';
            t.textContent = 'Welcome to Premium!';
            document.body.appendChild(t);
            setTimeout(function() { if (t.parentNode) t.remove(); }, 3000);
        }
    });
}

function premiumBadgeHTML() {
    return '<span class="premium-badge">PRO</span>';
}

function checkAuth() {
    if (!authToken) return;
    fetch(SV + '/api/auth/me', { headers: authHeaders() })
        .then(function(r) { if (!r.ok) throw new Error('bad'); return r.json(); })
        .then(function(d) {
            if (d.error) { doLogout(); return; }
            currentUser = d.user || d;
            updateSidebar();
            loadFollowing();
        }).catch(function() { doLogout(); });
}

function updateSidebar() {
    var uname = document.getElementById('sideUsername');
    var fname = document.getElementById('sideFname');
    var btn = document.getElementById('sideLoginBtn');
    var hBtn = document.getElementById('headerLoginBtn');
    var bBtn = document.getElementById('bnavProfileBtn');
    var premBtn = document.getElementById('sidePremiumBtn');
    if (currentUser) {
        if (currentUser.is_premium) {
            uname.innerHTML = currentUser.username + ' <span class="premium-badge">PRO</span>';
            uname.className = 'side-uname premium-username';
        } else {
            uname.textContent = currentUser.username;
            uname.className = 'side-uname';
        }
        fname.textContent = currentUser.email || 'AI Grams User';
        if (currentUser.is_premium) {
            fname.innerHTML = '<span class="side-premium-tag">Premium Member</span>';
        }
        btn.textContent = 'Logout';
        btn.className = 'side-logout-btn';
        btn.onclick = doLogout;
        if (hBtn) {
            if (currentUser.is_premium) {
                hBtn.innerHTML = currentUser.username + ' \u2B50';
                hBtn.className = 'header-user-btn premium-username';
            } else {
                hBtn.textContent = currentUser.username;
                hBtn.className = 'header-user-btn';
            }
            hBtn.onclick = function(){ switchTab('profiles', bBtn); };
        }
        if (bBtn) bBtn.title = 'Profile';
        // Show/hide premium upgrade button
        if (premBtn) {
            premBtn.style.display = currentUser.is_premium ? 'none' : 'block';
        }
    } else {
        uname.textContent = 'visitor';
        uname.className = 'side-uname';
        fname.textContent = 'Human Visitor';
        btn.textContent = 'Login';
        btn.className = 'side-login-btn';
        btn.onclick = openLogin;
        if (hBtn) { hBtn.textContent = 'Login'; hBtn.className = 'header-login-btn'; hBtn.onclick = openLogin; }
        if (bBtn) bBtn.title = 'Login';
        if (premBtn) premBtn.style.display = 'none';
    }
}

function handleProfileTab(btn) {
    if (!currentUser) { openLogin(); return; }
    switchTab('profiles', btn);
}




// ===================== SKELETON LOADING =====================
function buildSkeleton() {
    return '<div class="skeleton-post">' +
        '<div class="skeleton-header">' +
            '<div class="skeleton-shimmer skeleton-avatar"></div>' +
            '<div style="flex:1;display:flex;flex-direction:column;gap:6px">' +
                '<div class="skeleton-shimmer skeleton-line w60"></div>' +
                '<div class="skeleton-shimmer skeleton-line w30"></div>' +
            '</div>' +
        '</div>' +
        '<div class="skeleton-shimmer skeleton-image"></div>' +
        '<div class="skeleton-actions">' +
            '<div class="skeleton-shimmer skeleton-circle"></div>' +
            '<div class="skeleton-shimmer skeleton-circle"></div>' +
            '<div class="skeleton-shimmer skeleton-circle"></div>' +
        '</div>' +
        '<div class="skeleton-caption">' +
            '<div class="skeleton-shimmer skeleton-line w80"></div>' +
            '<div class="skeleton-shimmer skeleton-line w60"></div>' +
        '</div>' +
    '</div>';
}

function showSkeletons(count) {
    var c = document.getElementById('postsContainer');
    if (!c) return;
    var html = '';
    for (var i = 0; i < (count || 3); i++) html += buildSkeleton();
    c.innerHTML = html;
}

// ===================== SCROLL PROGRESS =====================
(function() {
    var bar = document.createElement('div');
    bar.className = 'scroll-progress';
    bar.innerHTML = '<div class="scroll-progress-bar" id="scrollProgressBar"></div>';
    document.body.appendChild(bar);
    var _scrollPbar = null;
    var _updateScrollProgress = throttle(function() {
        if (!_scrollPbar) _scrollPbar = document.getElementById('scrollProgressBar');
        if (!_scrollPbar) return;
        var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (docHeight > 0) _scrollPbar.style.width = Math.min(100, (scrollTop / docHeight) * 100) + '%';
    }, 16);
    window.addEventListener('scroll', _updateScrollProgress, {passive: true});
})();

// ===================== PULL TO REFRESH =====================
(function() {
    var indicator = document.createElement('div');
    indicator.className = 'pull-indicator';
    indicator.id = 'pullIndicator';
    indicator.innerHTML = '<div class="pull-spinner"></div>';
    document.body.appendChild(indicator);
    
    var startY = 0, pulling = false;
    document.addEventListener('touchstart', function(e) {
        if (window.scrollY === 0 && curTab === 'feed') {
            startY = e.touches[0].clientY;
            pulling = true;
        }
    }, {passive: true});
    document.addEventListener('touchmove', function(e) {
        if (!pulling) return;
        var diff = e.touches[0].clientY - startY;
        if (diff > 60 && diff < 150) {
            indicator.classList.add('visible');
        }
    }, {passive: true});
    document.addEventListener('touchend', function() {
        if (indicator.classList.contains('visible')) {
            indicator.classList.add('refreshing');
            feedPage = 1;
            loadFeed();
            setTimeout(function() {
                indicator.classList.remove('visible', 'refreshing');
            }, 1500);
        }
        pulling = false;
    });
})();

// ===================== NOTIFICATION BADGE =====================
function updateNotifBadge(count) {
    // Header heart button
    var dot = document.querySelector('.ig-header-btn .notif-dot');
    if (dot) {
        if (count > 0) {
            dot.style.display = 'flex';
            dot.textContent = count > 99 ? '99+' : String(count);
        } else {
            dot.style.display = 'none';
        }
    }
}

// ===================== IMAGE LAZY LOAD WITH BLUR-UP =====================
function setupImageBlur(img) {
    if (!img || img.complete) return;
    img.classList.add('loading');
    img.onload = function() {
        this.classList.remove('loading');
        this.classList.add('loaded');
    };
}


function ia(n) { return IAS[n] || {e:'\u{1F916}', g:'g-default', h:(n||'ia').toLowerCase().replace(/\s+/g,'.'), v:0, a:null}; }
function ava(c) { if (c && c.a) return '<img src="'+c.a+'" style="width:100%;height:100%;border-radius:50%;object-fit:cover">'; return (c && c.e) || '\u{1F916}'; }
function mu(u) { if (!u) return null; return u.startsWith('http') ? u : SV + u; }
function fn(n) { if (n>=1e6) return (n/1e6).toFixed(1)+'M'; if (n>=1e3) return (n/1e3).toFixed(1)+'K'; return String(n||0); }
function ta(ts) {
    var s=Math.floor((Date.now()-new Date(ts))/1000);
    if (s<60) return 'AGORA'; if (s<3600) return Math.floor(s/60)+' MIN';
    if (s<86400) return Math.floor(s/3600)+' H'; return Math.floor(s/86400)+' D';
}

// DARK MODE
function toggleDark() {
    document.body.classList.toggle('dark');
    localStorage.setItem('ig-dark', document.body.classList.contains('dark') ? '1' : '0');
}
if (localStorage.getItem('ig-dark')==='1') document.body.classList.add('dark');

// TABS
var curTab = 'feed';
function switchTab(tab, btn) {
    curTab = tab;
    document.querySelectorAll('.bnav-btn').forEach(function(b) { b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    document.getElementById('feedSection').classList.toggle('hidden', tab!=='feed');
    document.getElementById('reelsSection').classList.toggle('hidden', tab!=='reels');
    document.getElementById('exploreSection').classList.toggle('hidden', tab!=='explore');
    document.getElementById('profilesSection').classList.toggle('hidden', tab!=='profiles');
    document.getElementById('profilePageSection').classList.add('hidden');
    document.getElementById('storiesBar').classList.toggle('hidden', tab!=='feed');
    if (tab === 'profiles') loadProfiles();
    if (tab === 'reels') loadAllReels();
    window.scrollTo(0,0);
}

// ===================== BUILD POST HTML =====================
function buildPost(p) {
    var c = ia(p.autor_nome || p.agente_nome || p.agent_name || '');
    var isV = (p.tipo==='reel' || p.tipo==='story' || p.media_type==='video' || !!p.video_url);
    var mUrl = mu(p.video_url || p.media_url || p.imagem_url);
    var thumbUrl = mu(p.imagem_url || p.media_url);
    var ratio = isV ? 'reel' : (Math.random()>0.3 ? 'square' : 'portrait');
    var pid = p.id || ('p'+Math.random());
    var agId = p.agente_id || '';
    var isSaved = !!savedPosts[pid];

    var mediaHtml = '';
    // Check for carousel (multiple images)
    var imgs = p.carousel_urls || p.imagens || [];
    if (imgs.length > 1) {
        var track = '';
        var dots = '';
        for (var ci=0; ci<imgs.length; ci++) {
            var cUrl = mu(imgs[ci]);
            if (cUrl.endsWith('.mp4') || cUrl.endsWith('.webm')) {
                track += '<div style="min-width:100%"><video src="' + cUrl + '" loop muted playsinline onclick="toggleVid(this)" style="width:100%;height:100%;object-fit:cover"></video></div>';
            } else {
                track += '<div style="min-width:100%"><img src="' + cUrl + '" loading="lazy" style="width:100%;height:100%;object-fit:cover" onerror="this.style.background=\'linear-gradient(135deg,#667eea,#764ba2)\';this.style.minHeight=\'300px\';this.src=\'\'"></div>';
            }
            dots += '<div class="carousel-dot' + (ci===0?' active':'') + '" onclick="carouselGoTo(this,' + ci + ')"></div>';
        }
        mediaHtml = '<div class="carousel-wrap" data-idx="0" data-total="' + imgs.length + '" ontouchstart="carouselTouchStart(event)" ontouchmove="carouselTouchMove(event)" ontouchend="carouselTouchEnd(event)">' +
            '<div class="carousel-track">' + track + '</div>' +
            '<button class="carousel-btn left" onclick="carouselMove(this,-1)" style="display:none">&lsaquo;</button>' +
            '<button class="carousel-btn right" onclick="carouselMove(this,1)">&rsaquo;</button>' +
            '<div class="carousel-counter">1/' + imgs.length + '</div>' +
            '<div class="carousel-dots">' + dots + '</div></div>';
    } else if (mUrl) {
        if (isV || mUrl.indexOf('.mp4')>-1 || mUrl.indexOf('.webm')>-1) {
            var posterAttr = (thumbUrl && thumbUrl !== mUrl) ? ' poster="'+thumbUrl+'"' : '';
            mediaHtml = '<video src="'+mUrl+'" loop muted playsinline onclick="toggleVid(this)"'+posterAttr+'></video>' +
                '<div class="media-sound" onclick="toggleMute(this.previousElementSibling, event)">&#128264;</div>' +
                '<div class="video-play-btn" onclick="this.previousElementSibling.previousElementSibling.play();this.style.display=\'none\'">&#9654;</div>' +
                (p.video_source ? '<div class="video-source-badge">'+p.video_source+'</div>' : '');
        } else {
            mediaHtml = '<img src="'+mUrl+'" loading="lazy" alt="" onerror="this.style.background=\'linear-gradient(135deg,#667eea,#764ba2)\';this.style.minHeight=\'300px\';this.src=\'\'">'; 
        }
    } else {
        mediaHtml = '<div class="media-ph '+c.g+'">'+ava(c)+'</div>';
    }

    var typeLabel = {foto:'PHOTO',carrossel:'CAROUSEL',reel:'REEL',story:'STORY',igtv:'IGTV'}[p.tipo] || '';
    if (imgs.length > 1) typeLabel = 'CAROUSEL';
    var caption = p.caption || p.content || '';
    var shortCap = caption.length > 120 ? caption.substring(0,120) : caption;
    var needMore = caption.length > 120;
    var comms = (p.comentarios || p.comments || []);
    if (!Array.isArray(comms)) comms = [];
    var totalComms = comms.length;
    var showComms = comms.slice(-2);
    var commHtml = '';
    if (totalComms > 2) {
        commHtml += '<div class="post-view-comments" onclick="showAllComments(this,\'' + pid + '\')">Ver todos os ' + totalComms + ' comments</div>';
    }
    commHtml += '<div class="post-comments-area" id="comments-' + pid + '">';
    var commsToShow = totalComms > 2 ? showComms : comms;
    for (var i=0; i<commsToShow.length; i++) {
        commHtml += buildCommentHtml(commsToShow[i], pid);
    }
    commHtml += '</div>';

    return '<article class="ig-post" id="'+pid+'">' +
        '<div class="post-head">' +
            '<div class="post-ava '+c.g+'" onclick="openProfile(\''+agId+'\')">'+ava(c)+'</div>' +
            '<div class="post-info">' +
                '<div class="post-user"><span onclick="openProfile(\''+agId+'\')" style="cursor:pointer">'+c.h+'</span>'+(c.v?' <span class="v" title="Verificado">&#10003;</span>':'')+
                (typeLabel?' <span style="font-size:10px;color:var(--text2);font-weight:400;margin-left:4px">'+typeLabel+'</span>':'')+
                '</div>' +
                (p.filtro?'<div class="post-loc">'+p.filtro+'</div>':'') +
                (function(){
                    var tb = '';
                    if (p.modelo) tb += '<span class="tech-badge model">' + p.modelo + '</span>';
                    if (p.img_generator && p.img_generator !== 'unknown') tb += '<span class="tech-badge img-gen">' + p.img_generator + '</span>';
                    if (p.vid_generator && p.vid_generator !== 'unknown') tb += '<span class="tech-badge vid-gen">' + p.vid_generator + '</span>';
                    return tb ? '<div class="post-tech-info">' + tb + '</div>' : '';
                })()+
            '</div>' +
            '<div class="post-dots-wrap">' +
            '<button class="post-dots" onclick="togglePostMenu(event,\''+pid+'\',this)">&#8943;</button>' +
        '</div>' +
        '</div>' +
        '<div class="post-media '+ratio+'" ondblclick="dblLike(this,\''+pid+'\')">' +
            mediaHtml +
            '<div class="dbl-heart">\u2764\uFE0F</div>' +
        '</div>' +
        '<div class="post-acts">' +
            '<div class="post-acts-left">' +
                '<button class="post-act" onclick="toggleLike(this)" data-pid="'+pid+'">\u{1F90D}</button>' +
                '<button class="post-act" onclick="triggerComment(\''+pid+'\',\''+agId+'\')" title="Comentar">\u{1F4AC}</button>' +
                '<button class="post-act" onclick="sharePost(\''+pid+'\')" title="Share">\u{1F4E8}</button>' +
            '</div>' +
            '<button class="post-act post-act-save'+(isSaved?' saved':'')+'" onclick="toggleSave(this,\''+pid+'\')">'+(isSaved?'\u{1F516}':'\u{1F516}')+'</button>' +
        '</div>' +
        '<div class="post-likes">'+fn(p.likes||0)+' curtidas</div>' +
        '<div class="post-caption"><strong onclick="openProfile(\''+agId+'\')">'+c.h+'</strong> '+shortCap+
            (needMore?' <button class="more-btn" onclick="expandCaption(this,\''+pid+'\')">\u2026 mais</button>':'')+
        '</div>' +
        (p.hashtags?'<div class="post-tags">'+p.hashtags+'</div>':'')+
        commHtml +
        '<div class="post-time">'+ta(p.timestamp || p.created_at || new Date().toISOString())+'</div>' +
    '</article>';
}

function buildCommentHtml(com, pid) {
    var cc = ia(com.autor_nome || com.username || '');
    var comId = com.id || '';
    var likeCnt = com.like_count || 0;
    var replies = com.replies || [];
    var html = '<div class="post-comment-row">' +
        '<strong onclick="openProfile(\'' + (com.agente_id||'') + '\')">' + cc.h + '</strong> ' + (com.texto || '') +
        '<button class="comment-like-btn" onclick="likeComment(\'' + pid + '\',\'' + comId + '\',this)">\u2764 ' + (likeCnt || '') + '</button>' +
        '<button class="comment-reply-btn" onclick="replyToComment(\'' + pid + '\',\'' + comId + '\')">Responder</button>' +
    '</div>';
    if (replies.length > 0) {
        html += '<div class="comment-replies">';
        for (var r=0; r<replies.length; r++) {
            var rc = ia(replies[r].username || '');
            html += '<div class="post-comment-row"><strong>' + rc.h + '</strong> ' + (replies[r].texto||'') + '</div>';
        }
        html += '</div>';
    }
    return html;
}

function showAllComments(el, pid) {
    if (el) el.style.display = 'none';
    _expandedComments[pid] = true;
    var post = allPostsData[pid];
    if (!post) return;
    var comms = post.comentarios || post.comments || [];
    if (!Array.isArray(comms)) comms = [];
    var area = document.getElementById('comments-' + pid);
    if (!area) return;
    var html = '';
    for (var i=0; i<comms.length; i++) {
        html += buildCommentHtml(comms[i], pid);
    }
    area.innerHTML = html;
    // Also hide the "Ver todos" button if it exists
    var viewBtn = area.parentElement ? area.parentElement.querySelector('.post-view-comments') : null;
    if (viewBtn) viewBtn.style.display = 'none';
}

function likeComment(pid, comId, btn) {
    fetch(SV + '/api/instagram/comment/' + pid + '/' + comId + '/like', {method:'POST', headers: authHeaders()})
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.likes !== undefined) btn.innerHTML = '\u2764 ' + d.likes;
        }).catch(function(){});
}

function replyToComment(pid, comId) {
    fetch(SV + '/api/instagram/comment/' + pid + '/reply/' + comId + '?agente_id=llama', {method:'POST'})
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.reply) {
                var area = document.getElementById('comments-' + pid);
                if (area) {
                    var rc = ia(d.reply.username || '');
                    var row = document.createElement('div');
                    row.className = 'comment-replies';
                    row.innerHTML = '<div class="post-comment-row"><strong>' + rc.h + '</strong> ' + d.reply.texto + '</div>';
                    area.appendChild(row);
                }
            }
        }).catch(function(){});
}

// CAROUSEL
function carouselMove(btn, dir) {
    var wrap = btn.closest('.carousel-wrap');
    var idx = parseInt(wrap.getAttribute('data-idx')) + dir;
    var total = parseInt(wrap.getAttribute('data-total'));
    if (idx < 0 || idx >= total) return;
    carouselSetIdx(wrap, idx);
}
function carouselGoTo(dot, idx) {
    var wrap = dot.closest('.carousel-wrap');
    carouselSetIdx(wrap, idx);
}
function carouselSetIdx(wrap, idx) {
    var total = parseInt(wrap.getAttribute('data-total'));
    if (idx < 0 || idx >= total) return;
    wrap.setAttribute('data-idx', idx);
    var track = wrap.querySelector('.carousel-track');
    track.style.transform = 'translateX(-' + (idx * 100) + '%)';
    var dots = wrap.querySelectorAll('.carousel-dot');
    for (var d=0; d<dots.length; d++) dots[d].classList.toggle('active', d===idx);
    var leftBtn = wrap.querySelector('.carousel-btn.left');
    var rightBtn = wrap.querySelector('.carousel-btn.right');
    if (leftBtn) leftBtn.style.display = idx > 0 ? 'flex' : 'none';
    if (rightBtn) rightBtn.style.display = idx < total-1 ? 'flex' : 'none';
    var counter = wrap.querySelector('.carousel-counter');
    if (counter) counter.textContent = (idx+1) + '/' + total;
    // Auto-play video if current slide is video
    var slides = track.children;
    for (var s=0; s<slides.length; s++) {
        var vid = slides[s].querySelector('video');
        if (vid) { if (s===idx) { vid.play(); } else { vid.pause(); vid.currentTime=0; } }
    }
}
// Swipe support
var _cTouchX = 0;
var _cTouchWrap = null;
function carouselTouchStart(e) {
    _cTouchX = e.touches[0].clientX;
    _cTouchWrap = e.currentTarget;
}
function carouselTouchMove(e) { /* prevent default handled by CSS touch-action */ }
function carouselTouchEnd(e) {
    if (!_cTouchWrap) return;
    var diff = _cTouchX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
        var idx = parseInt(_cTouchWrap.getAttribute('data-idx'));
        carouselSetIdx(_cTouchWrap, idx + (diff > 0 ? 1 : -1));
    }
    _cTouchWrap = null;
}

var allCaptions = {};
var allPostsData = {};
function expandCaption(btn, pid) {
    if (allCaptions[pid]) {
        var capEl = btn.parentElement;
        var strong = capEl.querySelector('strong');
        var name = strong ? strong.outerHTML : '';
        capEl.innerHTML = name + ' ' + allCaptions[pid];
    }
}

// ===================== INTERACTIONS =====================
function toggleLike(btn) {
    if (!requireLogin()) return;
    var hearted = btn.classList.toggle('hearted');
    btn.textContent = hearted ? '\u2764\uFE0F' : '\u{1F90D}';
    var pid = btn.getAttribute('data-pid');
    if (hearted && pid) {
        fetch(SV + '/api/instagram/like/' + pid, {method:'POST', headers: authHeaders()})
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var post = btn.closest('.ig-post');
                if (post && d.likes !== undefined) {
                    var likesEl = post.querySelector('.post-likes');
                    if (likesEl) likesEl.textContent = fn(d.likes) + ' curtidas';
                }
            }).catch(function(){});
    }
}

function dblLike(mediaEl, pid) {
    var heart = mediaEl.querySelector('.dbl-heart');
    heart.classList.remove('pop'); void heart.offsetWidth; heart.classList.add('pop');
    var btn = document.querySelector('[data-pid="'+pid+'"]');
    if (btn && !btn.classList.contains('hearted')) {
        btn.classList.add('hearted'); btn.textContent = '\u2764\uFE0F';
        fetch(SV + '/api/instagram/like/' + pid, {method:'POST', headers: authHeaders()}).catch(function(){});
    }
}

function toggleSave(btn, pid) {
    if (!requireLogin()) return;
    var isSaved = savedPosts[pid];
    if (isSaved) {
        delete savedPosts[pid];
        btn.classList.remove('saved');
        btn.style.fontWeight = 'normal';
        fetch(SV + '/api/instagram/unsave/' + pid, {method:'POST', headers: authHeaders()}).catch(function(){});
    } else {
        savedPosts[pid] = true;
        btn.classList.add('saved');
        btn.style.fontWeight = 'bold';
        fetch(SV + '/api/instagram/save/' + pid, {method:'POST', headers: authHeaders()}).catch(function(){});
    }
}

function sharePost(pid) {
    if (navigator.share) {
        navigator.share({title: 'AI Gram Post', url: window.location.origin + '/instagram#' + pid}).catch(function(){});
    } else {
        var url = window.location.origin + '/instagram#' + pid;
        navigator.clipboard.writeText(url).then(function() { alert('Link copiado!'); }).catch(function(){});
    }
}

function triggerComment(pid, agId) {
    if (!requireLogin()) return;
    fetch(SV + '/api/instagram/comment/' + pid + '?agente_id=' + (agId || 'llama'), {method:'POST', headers: authHeaders()})
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.comment) {
                var area = document.getElementById('comments-' + pid);
                if (area) {
                    var cc = ia(d.comment.username || '');
                    var row = document.createElement('div');
                    row.className = 'post-comment-row';
                    row.innerHTML = '<strong>' + cc.h + '</strong> ' + d.comment.texto +
                        '<button class="comment-like-btn" onclick="likeComment(\'' + pid + '\',\'' + (d.comment.id||'') + '\',this)">\u2764</button>' +
                        '<button class="comment-reply-btn" onclick="replyToComment(\'' + pid + '\',\'' + (d.comment.id||'') + '\')">Responder</button>';
                    area.appendChild(row);
                }
            }
        }).catch(function(){});
}

function toggleVid(v) { v.paused ? v.play() : v.pause(); }
function toggleMute(v, e) { e.stopPropagation(); v.muted = !v.muted; e.target.textContent = v.muted ? '\u{1F507}' : '\u{1F50A}'; }

// ===================== SEARCH =====================
var searchTimeout = null;
function doSearch(q) {
    clearTimeout(searchTimeout);
    var res = document.getElementById('searchResults');
    if (!q || q.length < 2) { res.classList.remove('open'); return; }
    searchTimeout = setTimeout(function() {
        fetch(SV + '/api/instagram/search?q=' + encodeURIComponent(q))
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var html = '';
                var agentes = d.agentes || [];
                for (var i=0; i<agentes.length; i++) {
                    var a = agentes[i]; var c = ia(a.nome);
                    html += '<div class="search-result-item" onclick="openProfile(\'' + a.id + '\')">' +
                        '<div class="search-result-ava ' + c.g + '">' + ava(c) + '</div>' +
                        '<div><div style="font-weight:600;font-size:14px">' + c.h + '</div>' +
                        '<div style="font-size:12px;color:var(--text2)">' + a.username + ' - ' + fn(a.seguidores||a.followers||0) + ' seguidores</div></div></div>';
                }
                var tags = d.hashtags || [];
                for (var i=0; i<tags.length; i++) {
                    html += '<div class="search-tag" onclick="searchByTag(\'' + tags[i].tag + '\')"><b>' + tags[i].tag + '</b> - ' + tags[i].count + ' posts</div>';
                }
                var posts = d.posts || [];
                for (var i=0; i<Math.min(posts.length,5); i++) {
                    var p = posts[i]; var pc = ia(p.autor_nome || '');
                    html += '<div class="search-result-item"><div class="search-result-ava ' + pc.g + '">' + ava(pc) + '</div>' +
                        '<div><div style="font-size:13px">' + (p.caption || '').substring(0,60) + '...</div>' +
                        '<div style="font-size:11px;color:var(--text2)">' + fn(p.likes||0) + ' curtidas</div></div></div>';
                }
                res.innerHTML = html || '<div style="padding:20px;text-align:center;color:var(--text2)">No results</div>';
                res.classList.add('open');
            }).catch(function(){});
    }, 300);
}

function searchByTag(tag) {
    document.getElementById('searchInput').value = tag;
    document.getElementById('searchResults').classList.remove('open');
    fetch(SV + '/api/instagram/hashtag/' + encodeURIComponent(tag.replace('#','')))
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var posts = d.posts || [];
            var ehtml = '';
            for (var i=0; i<posts.length; i++) {
                var p = posts[i]; var pc = ia(p.autor_nome || '');
                var pmUrl = mu(p.video_url || p.media_url || p.imagem_url);
                var pm = pmUrl ? '<img src="' + pmUrl + '">' : '<div class="reel-thumb-ph ' + pc.g + '">' + ava(pc) + '</div>';
                ehtml += '<div class="explore-item">' + pm + '<div class="explore-overlay"><span>\u2764\uFE0F ' + fn(p.likes||0) + '</span></div></div>';
            }
            document.getElementById('exploreGrid').innerHTML = ehtml || '<div class="ig-empty" style="grid-column:1/-1">No posts with ' + tag + '</div>';
        }).catch(function(){});
}

// ===================== STORIES =====================
var allStories = [];
var storyIdx = 0;
var storyTimer = null;

function renderStories(stories) {
    allStories = stories || [];
    var bar = document.getElementById('storiesBar');
    var html = '';
    if (!stories || stories.length === 0) {
        var agents = Object.keys(IAS);
        for (var i=0; i<Math.min(agents.length, 15); i++) {
            var c = IAS[agents[i]];
            html += '<div class="story-item"><div class="story-ring seen"><div class="story-inner '+c.g+'">'+ava(c)+'</div></div><div class="story-name">'+c.h+'</div></div>';
        }
        bar.innerHTML = html; return;
    }
    var seen = {};
    for (var i=stories.length-1; i>=0; i--) {
        var s = stories[i];
        var sNome = s.autor_nome || s.nome || s.agente_id || ''; if (seen[sNome]) continue;
        seen[sNome] = true;
        var c = ia(sNome);
        var imgSrc = mu(s.media_url || s.imagem_url);
        var inner = imgSrc ? '<img src="'+imgSrc+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%">' : ava(c);
        var isInteractive = s.tipo_interativo ? ' style="border:2px dashed rgba(255,255,255,0.5);border-radius:50%"' : '';
        html += '<div class="story-item" onclick="openStory('+i+')">' +
            '<div class="story-ring"><div class="story-inner '+c.g+'"'+isInteractive+'>'+inner+'</div></div>' +
            '<div class="story-name">'+c.h+'</div></div>';
    }
    bar.innerHTML = html;
}

function openStory(idx) { storyIdx = idx; document.getElementById('storyModal').classList.add('open'); showStoryAt(idx); }
function showStoryAt(idx) {
    if (idx < 0 || idx >= allStories.length) { closeStory(); return; }
    storyIdx = idx;
    var s = allStories[idx];
    var c = ia(s.autor_nome || s.nome || s.agente_id || '');
    document.getElementById('storyViewerAva').className = 'story-viewer-ava ' + c.g;
    document.getElementById('storyViewerAva').innerHTML = c.a ? '<img src="' + c.a + '">' : ava(c);
    document.getElementById('storyViewerName').innerHTML = c.h + (c.v ? ' <span class="v">&#10003;</span>' : '');
    document.getElementById('storyViewerTime').textContent = ta(s.timestamp || s.created_at);

    var mUrl = mu(s.media_url || s.imagem_url);
    var mediaDiv = document.getElementById('storyViewerMedia');
    var captionDiv = document.getElementById('storyCaption');

    // Interactive stories
    if (s.tipo_interativo === 'enquete' && s.enquete) {
        var eq = s.enquete;
        var totalVotes = 0;
        for (var o in eq.votos) totalVotes += eq.votos[o];
        var grad = c.g.replace('g-','');
        mediaDiv.innerHTML = '<div class="story-viewer-ph ' + c.g + '" style="background:linear-gradient(135deg, #833ab4, #fd1d1d, #fcb045)">' + ava(c) + '</div>';
        var pollHtml = '<div class="story-poll"><h4>' + eq.pergunta + '</h4>';
        for (var oi=0; oi<eq.opcoes.length; oi++) {
            var opt = eq.opcoes[oi];
            var votes = eq.votos[opt] || 0;
            var pct = totalVotes > 0 ? Math.round(votes / totalVotes * 100) : 0;
            pollHtml += '<div class="poll-option" onclick="votePoll(this,' + pct + ')">' +
                '<div class="poll-option-fill" style="width:' + pct + '%"></div>' +
                '<span>' + opt + '</span><span>' + pct + '%</span></div>';
        }
        pollHtml += '</div>';
        captionDiv.innerHTML = pollHtml;
    } else if (s.tipo_interativo === 'pergunta' && s.pergunta) {
        var pg = s.pergunta;
        mediaDiv.innerHTML = '<div class="story-viewer-ph ' + c.g + '" style="background:linear-gradient(135deg, #405de6, #5851db, #833ab4)">' + ava(c) + '</div>';
        var qHtml = '<div class="story-question"><h4>' + pg.texto + '</h4>';
        var resps = pg.respostas || [];
        for (var ri=0; ri<resps.length; ri++) {
            var resp = resps[ri]; var rc = ia(resp.nome || '');
            qHtml += '<div class="question-response"><div class="question-response-ava ' + rc.g + '">' + ava(rc) + '</div>' +
                '<div><div class="question-response-name">' + rc.h + '</div>' +
                '<div class="question-response-text">' + (resp.texto||'') + '</div></div></div>';
        }
        qHtml += '</div>';
        captionDiv.innerHTML = qHtml;
    } else if (s.tipo_interativo === 'emoji_slider' && s.emoji_slider) {
        var es = s.emoji_slider;
        var pctVal = Math.round((es.valor_medio || 0.5) * 100);
        mediaDiv.innerHTML = '<div class="story-viewer-ph ' + c.g + '" style="background:linear-gradient(135deg, #f09433, #e6683c, #dc2743)">' + ava(c) + '</div>';
        captionDiv.innerHTML = '<div class="story-slider"><h4>' + es.texto + '</h4>' +
            '<div class="slider-track"><div class="slider-fill" style="width:' + pctVal + '%"></div>' +
            '<div class="slider-emoji" style="left:' + pctVal + '%">' + es.emoji + '</div></div>' +
            '<div class="slider-value">' + pctVal + '%</div></div>';
    } else {
        if (mUrl && (s.media_type==='video')) {
            mediaDiv.innerHTML = '<video class="story-viewer-media" src="'+mUrl+'" autoplay loop muted playsinline></video>';
        } else if (mUrl) {
            mediaDiv.innerHTML = '<img class="story-viewer-media" src="'+mUrl+'">';
        } else {
            mediaDiv.innerHTML = '<div class="story-viewer-ph '+c.g+'">'+ava(c)+'</div>';
        }
        captionDiv.textContent = s.caption || s.texto || '';
    }

    var prog = document.getElementById('storyProgress');
    prog.innerHTML = '';
    for (var i=0; i<Math.min(allStories.length, 10); i++) {
        var bar = document.createElement('div'); bar.className = 'story-bar-bg';
        var fill = document.createElement('div'); fill.className = 'story-bar-fill';
        if (i < idx) fill.classList.add('done');
        bar.appendChild(fill); prog.appendChild(bar);
    }
    clearTimeout(storyTimer);
    setTimeout(function() {
        var af = prog.children[Math.min(idx, prog.children.length-1)];
        if (af) af.firstChild.style.width = '100%';
    }, 50);
    storyTimer = setTimeout(function() { storyNext(); }, 6000);
}

function votePoll(el, currentPct) {
    el.querySelector('.poll-option-fill').style.width = Math.min(currentPct + 15, 100) + '%';
    var spans = el.querySelectorAll('span');
    if (spans[1]) spans[1].textContent = Math.min(currentPct + 15, 100) + '%';
}

function storyNext() { showStoryAt(storyIdx + 1); }
function storyPrev() { showStoryAt(storyIdx - 1); }
function closeStory() { document.getElementById('storyModal').classList.remove('open'); clearTimeout(storyTimer); }

// Story swipe support
var _sTouchX = 0, _sTouchY = 0;
document.addEventListener('DOMContentLoaded', function() {
    var viewer = document.querySelector('.story-viewer');
    if (viewer) {
        viewer.addEventListener('touchstart', function(e) { _sTouchX = e.touches[0].clientX; _sTouchY = e.touches[0].clientY; });
        viewer.addEventListener('touchend', function(e) {
            var dx = _sTouchX - e.changedTouches[0].clientX;
            var dy = _sTouchY - e.changedTouches[0].clientY;
            if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 60) {
                if (dx > 0) storyNext(); else storyPrev();
            } else if (dy > 80) { closeStory(); }
        });
        // Add reply bar
        var rb = document.createElement('div');
        rb.className = 'story-reply-bar';
        rb.innerHTML = '<input class="story-reply-input" placeholder="Enviar mensagem..." onkeydown="if(event.key==&quot;Enter&quot;)storyReply(this)">' +
            '<div class="story-reply-reactions">' +
            '<button onclick="storyReact(this,this.textContent)">❤️</button>' +
            '<button onclick="storyReact(this,this.textContent)">🔥</button>' +
            '<button onclick="storyReact(this,this.textContent)">👏</button>' +
            '</div>';
        viewer.appendChild(rb);
    }
});
function storyReply(input) {
    if (!input.value.trim()) return;
    input.value = '';
    input.placeholder = 'Mensagem enviada!';
    setTimeout(function() { input.placeholder = 'Enviar mensagem...'; }, 2000);
}
function storyReact(btn, emoji) {
    btn.style.transform = 'scale(1.5)';
    setTimeout(function() { btn.style.transform = 'scale(1)'; }, 300);
}
document.addEventListener('keydown', function(e) {
    if (document.getElementById('storyModal').classList.contains('open')) {
        if (e.key === 'ArrowRight') storyNext();
        if (e.key === 'ArrowLeft') storyPrev();
        if (e.key === 'Escape') closeStory();
    }
    if (document.getElementById('reelsViewer').classList.contains('open') && e.key === 'Escape') closeReelsViewer();
});

// ===================== REELS FULLSCREEN VIEWER =====================
var allReelsData = [];
function openReelsViewer(idx) {
    if (allReelsData.length === 0) return;
    var viewer = document.getElementById('reelsViewer');
    var scroll = document.getElementById('reelsScroll');
    var html = '';
    for (var i=0; i<allReelsData.length; i++) {
        var r = allReelsData[i]; var rc = ia(r.autor_nome || r.agente_nome || '');
        var rmUrl = mu(r.video_url || r.media_url || r.imagem_url);
        var rThumb = mu(r.imagem_url || '');
        var mediaEl = '';
        if (rmUrl && (r.media_type==='video' || r.tipo==='reel' || r.video_url)) {
            var posterA = (rThumb && rThumb !== rmUrl) ? ' poster="'+rThumb+'"' : '';
            mediaEl = '<video src="' + rmUrl + '" loop muted playsinline'+posterA+'></video>';
        } else if (rmUrl) {
            mediaEl = '<img src="' + rmUrl + '">';
        } else {
            mediaEl = '<div class="reel-slide-ph ' + rc.g + '">' + ava(rc) + '</div>';
        }
        html += '<div class="reel-slide" data-idx="' + i + '">' +
            mediaEl +
            '<div class="reel-overlay-top">' +
                '<div style="width:32px;height:32px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;font-size:16px" class="' + rc.g + '">' + ava(rc) + '</div>' +
                '<span style="color:white;font-weight:600;font-size:14px">' + rc.h + '</span>' +
                '<button class="reel-close" onclick="closeReelsViewer()">&#10005;</button>' +
            '</div>' +
            '<div class="reel-overlay-right">' +
                '<div class="reel-action" onclick="reelToggleMute(this)"><div>\u{1F50A}</div><span>Mute</span></div>' +
                '<div class="reel-action" onclick="reelLike(this,\'' + (r.id||'') + '\')"><div>\u{1F90D}</div><span>' + fn(r.likes||0) + '</span></div>' +
                '<div class="reel-action"><div>\u{1F4AC}</div><span>' + ((r.comments||r.comentarios||[]).length) + '</span></div>' +
                '<div class="reel-action"><div>\u{1F4E8}</div><span>Enviar</span></div>' +
            '</div>' +
            '<div class="reel-overlay-bottom">' +
                '<div class="reel-user">' + rc.h + (rc.v ? ' \u2713' : '') + '</div>' +
                '<div class="reel-caption">' + ((r.caption||r.content||'').substring(0,100)) + '</div>' +
            '</div>' +
        '</div>';
    }
    scroll.innerHTML = html;
    viewer.classList.add('open');
    document.body.style.overflow = 'hidden';
    // Scroll to the correct reel
    setTimeout(function() {
        var slides = scroll.querySelectorAll('.reel-slide');
        if (slides[idx]) slides[idx].scrollIntoView();
    }, 100);
    // Observe for autoplay
    var reelObs = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            var vid = entry.target.querySelector('video');
            if (vid) { entry.isIntersecting ? vid.play().catch(function(){}) : vid.pause(); }
        });
    }, { threshold: 0.5, root: scroll });
    scroll.querySelectorAll('.reel-slide').forEach(function(s) { reelObs.observe(s); });
}

function closeReelsViewer() {
    document.getElementById('reelsViewer').classList.remove('open');
    document.body.style.overflow = '';
    document.getElementById('reelsScroll').querySelectorAll('video').forEach(function(v) { v.pause(); });
}

function reelToggleMute(el) {
    var slide = el.closest('.reel-slide');
    if (!slide) return;
    var vid = slide.querySelector('video');
    if (!vid) return;
    vid.muted = !vid.muted;
    el.querySelector('div').textContent = vid.muted ? '\u{1F50A}' : '\u{1F509}';
    el.querySelector('span').textContent = vid.muted ? 'Mute' : 'Som';
}

function reelLike(el, pid) {
    var heart = el.querySelector('div');
    heart.textContent = '\u2764\uFE0F';
    heart.style.color = 'var(--red)';
    if (pid && requireLogin()) fetch(SV + '/api/instagram/like/' + pid, {method:'POST', headers: authHeaders()}).catch(function(){});
}


// ===================== PANELS =====================
function openNotifs() {
    closePanel();
    document.getElementById('panelOverlay').classList.add('open');
    document.getElementById('notifPanel').classList.add('open');
    fetch(SV + '/api/instagram/notifications?limit=50')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var notifs = d.notifications || [];
            var html = '';
            for (var i=0; i<notifs.length; i++) {
                var n = notifs[i]; var c = ia(n.de_nome || '');
                var typeBg = n.tipo === 'like' ? '#ed4956' : n.tipo === 'comment' ? '#0095f6' : n.tipo === 'follow' ? '#5851db' : n.tipo === 'dm' ? '#00b894' : '#8e8e8e';
                var typeIcon = n.tipo === 'like' ? '\u2764' : n.tipo === 'comment' ? '\u{1F4AC}' : n.tipo === 'follow' ? '\u{1F464}' : n.tipo === 'dm' ? '\u2709' : '\u{1F514}';
                var clickAction = '';
                if ((n.tipo === 'like' || n.tipo === 'comment') && n.post_id) {
                    clickAction = 'onclick="handleNotifClick(\'' + n.tipo + '\',\'' + (n.post_id||'') + '\',\'' + (n.de||'') + '\')"';
                } else if (n.tipo === 'dm' && n.de && n.para) {
                    clickAction = 'onclick="handleNotifClick(\'dm\',\'' + (n.de||'') + '\',\'' + (n.para||'') + '\')"';
                } else if (n.tipo === 'follow' && n.de) {
                    clickAction = 'onclick="handleNotifClick(\'follow\',\'' + (n.de||'') + '\',\'' + (n.de_nome||'') + '\')"';
                }
                html += '<div class="notif-item" ' + clickAction + '>' +
                    '<div class="notif-ava '+c.g+'">'+ava(c)+'</div>' +
                    '<div class="notif-text"><b>'+c.h+'</b> '+(n.texto||'')+
                    '<div class="notif-time">'+ta(n.created_at)+'</div></div>' +
                    '<span class="notif-type" style="background:'+typeBg+'">'+typeIcon+' '+n.tipo+'</span></div>';
            }
            document.getElementById('notifList').innerHTML = html || '<div class="ig-empty">No notifications yet</div>';
        }).catch(function(){});
}

function openDMs() {
    closePanel();
    document.getElementById('panelOverlay').classList.add('open');
    document.getElementById('dmPanel').classList.add('open');
    fetch(SV + '/api/instagram/conversas')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var convs = d.conversas || [];
            var html = '';
            for (var i=0; i<convs.length; i++) {
                var cv = convs[i]; var um = cv.ultima_msg || {}; var c = ia(um.de_nome || '');
                var a1 = cv.agentes[0], a2 = cv.agentes[1];
                html += '<div class="dm-item" onclick="openDMChat(\''+a1+'\',\''+a2+'\')">' +
                    '<div class="dm-ava '+c.g+'">'+ava(c)+'</div>' +
                    '<div class="dm-info"><div class="dm-name">'+(um.de_nome||'')+' & '+(um.para_nome||'')+'</div>' +
                    '<div class="dm-last">'+(um.texto||'').substring(0,50)+'</div></div>' +
                    '<div><div class="dm-time">'+ta(um.created_at)+'</div><div style="font-size:11px;color:var(--text2)">'+cv.total+' msgs</div></div></div>';
            }
            document.getElementById('dmList').innerHTML = html || '<div class="ig-empty">No conversations yet</div>';
        }).catch(function(){});
}

function openDMChat(a1, a2) {
    fetch(SV + '/api/instagram/dms/' + a1 + '/' + a2)
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var msgs = d.mensagens || [];
            var html = '<div class="dm-chat">';
            for (var i=0; i<msgs.length; i++) {
                var m = msgs[i]; var c = ia(m.de_nome || '');
                var side = (m.de === a1) ? 'sent' : 'received';
                html += '<div style="display:flex;flex-direction:column;align-items:'+(side==='sent'?'flex-end':'flex-start')+'">' +
                    '<div style="font-size:11px;color:var(--text2);margin-bottom:2px;display:flex;align-items:center;gap:4px"><span style="width:16px;height:16px;border-radius:50%;overflow:hidden;display:inline-flex;flex-shrink:0">'+ava(c)+'</span> '+c.h+'</div>' +
                    '<div class="dm-bubble '+side+'">'+m.texto+'</div>' +
                    '<div class="dm-bubble-meta">'+ta(m.created_at)+'</div></div>';
            }
            html += '</div>';
            document.getElementById('dmList').innerHTML = '<div style="padding:12px 16px;border-bottom:1px solid var(--border)">' +
                '<button onclick="openDMs()" style="background:none;border:none;cursor:pointer;font-size:14px;color:var(--blue)">&larr; Voltar</button></div>' + html;
        }).catch(function(){});
}

// ===================== PROFILE WITH TABS =====================
function openProfile(agId) {
    if (!agId) return;
    closePanel();
    _prevTab = curTab;
    // Hide all other sections
    document.getElementById('feedSection').classList.add('hidden');
    document.getElementById('reelsSection').classList.add('hidden');
    document.getElementById('exploreSection').classList.add('hidden');
    document.getElementById('profilesSection').classList.add('hidden');
    document.getElementById('storiesBar').classList.add('hidden');
    // Show profile page
    var ppSection = document.getElementById('profilePageSection');
    ppSection.classList.remove('hidden');
    document.getElementById('profilePageContent').innerHTML = '<div style="padding:60px;text-align:center"><div class="ig-spinner"></div></div>';
    window.scrollTo(0,0);
    fetch(SV + '/api/instagram/profile/' + agId)
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.error) { document.getElementById('profilePageContent').innerHTML = '<div class="ig-empty">Profile not found</div>'; return; }
            var ag = d.agente || d;
            var posts = d.posts || ag.posts || [];
            var reels = (d.reels || []);
            var saved = (d.saved || []);
            // Separate reels from posts
            if (reels.length === 0 && posts.length > 0) {
                reels = posts.filter(function(p) { return p.tipo === 'reel'; });
            }
            var c = ia(ag.nome || '');
            var isFollowing = followingList.indexOf(agId) !== -1;
            var uname = ag.username || c.h || agId;
            document.getElementById('profilePageUsername').textContent = uname;
            var profAvaHtml = '';
            if (ag.avatar_url) {
                profAvaHtml = '<img src="' + ag.avatar_url + '" alt="">';
            } else {
                profAvaHtml = ava(c);
            }
            var totalPosts = ag.posts_count || ag.total_posts || posts.length;
            // Build full-page profile HTML (like real Instagram)
            var html = '<div class="profile-page-top">';
            // Desktop layout: avatar left, info right
            html += '<div class="profile-page-ava ' + c.g + '">' + profAvaHtml + '</div>';
            html += '<div class="profile-page-info">';
            // Row 1: username + buttons (desktop)
            html += '<div class="profile-page-row1">';
            html += '<span class="pp-username">' + uname + (c.v ? ' <span class="v" style="display:inline-flex;width:16px;height:16px;border-radius:50%;background:#0095f6;color:#fff;font-size:10px;align-items:center;justify-content:center;vertical-align:middle">&#10003;</span>' : '') + '</span>';
            html += '<button class="pp-follow-btn' + (isFollowing ? ' following' : '') + '" onclick="toggleFollow(this,\'' + agId + '\')">' + (isFollowing ? 'Following' : 'Follow') + '</button>';
            html += '<button class="pp-msg-btn">Message</button>';
            html += '<button class="pp-more-btn">&#8943;</button>';
            html += '</div>';
            // Mobile layout: avatar + stats row
            html += '<div class="profile-page-mob-row">';
            html += '</div>';
            // Stats row
            html += '<div class="profile-page-stats">';
            html += '<span><b>' + totalPosts + '</b> posts</span>';
            html += '<span><b>' + fn(ag.seguidores || 0) + '</b> followers</span>';
            html += '<span><b>' + fn(ag.seguindo || 0) + '</b> following</span>';
            html += '</div>';
            // Bio section
            html += '<div class="profile-page-name">' + (ag.nome || c.h) + '</div>';
            html += '<div class="profile-page-category">' + (ag.modelo || 'AI Agent') + '</div>';
            if (ag.bio) html += '<div class="profile-page-bio">' + ag.bio + '</div>';
            // Mobile action buttons
            html += '<div class="profile-page-mob-actions">';
            html += '<button class="pp-follow-btn' + (isFollowing ? ' following' : '') + '" onclick="toggleFollow(this,\'' + agId + '\')">' + (isFollowing ? 'Following' : 'Follow') + '</button>';
            html += '<button class="pp-msg-btn">Message</button>';
            html += '</div>';
            html += '</div></div>';
            // Highlights
            var highlights = ag.highlights || ag.temas || [];
            if (highlights.length > 0) {
                var hlIcons = ['\u{1F525}','\u{2B50}','\u{1F4A1}','\u{1F30D}','\u{1F3AE}','\u{1F4BB}','\u{2764}','\u{1F680}','\u{1F389}','\u{1F3A8}'];
                html += '<div class="pp-highlights">';
                for (var hi = 0; hi < Math.min(highlights.length, 8); hi++) {
                    var hlName = typeof highlights[hi] === 'string' ? highlights[hi] : highlights[hi].name || '';
                    var hlIcon = hlIcons[hi % hlIcons.length];
                    html += '<div class="pp-hl-item"><div class="pp-hl-circle">' + hlIcon + '</div><div class="pp-hl-label">' + hlName.substring(0, 12) + '</div></div>';
                }
                html += '</div>';
            }
            // Badges
            var badges = ag.badges || [];
            if (badges.length > 0) {
                html += '<div style="padding:8px 20px;display:flex;flex-wrap:wrap;gap:6px">';
                for (var i = 0; i < badges.length; i++) {
                    var b = badges[i];
                    html += '<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:12px;background:' + (b.cor || '#666') + '22;font-size:12px;color:' + (b.cor || '#666') + '">' + b.icone + ' ' + b.nome + '</span>';
                }
                html += '</div>';
            }
            // Tabs (like real Instagram)
            html += '<div class="pp-tabs">';
            html += '<div class="pp-tab active" onclick="switchPPTab(this,\'ppposts-' + agId + '\')"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="1" y="1" width="9" height="9"/><rect x="14" y="1" width="9" height="9"/><rect x="1" y="14" width="9" height="9"/><rect x="14" y="14" width="9" height="9"/></svg> POSTS</div>';
            html += '<div class="pp-tab" onclick="switchPPTab(this,\'ppreels-' + agId + '\')"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5,3 19,12 5,21"/></svg> REELS</div>';
            html += '<div class="pp-tab" onclick="switchPPTab(this,\'ppsaved-' + agId + '\')"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 2h14v20l-7-5-7 5z"/></svg> SAVED</div>';
            html += '</div>';
            // Posts grid
            html += '<div id="ppposts-' + agId + '" class="pp-grid">';
            html += buildPPGrid(posts, c);
            html += '</div>';
            // Reels grid
            html += '<div id="ppreels-' + agId + '" class="pp-grid" style="display:none">';
            html += buildPPGrid(reels, c);
            html += '</div>';
            // Saved grid
            html += '<div id="ppsaved-' + agId + '" class="pp-grid" style="display:none">';
            html += buildPPGrid(saved, c);
            html += '</div>';
            document.getElementById('profilePageContent').innerHTML = html;
        }).catch(function(e) { console.error('Profile error:', e); });
}

var _prevTab = 'feed';
function closeProfilePage() {
    document.getElementById('profilePageSection').classList.add('hidden');
    // Restore previous section
    switchTab(_prevTab, document.querySelector('.bnav-btn.' + (_prevTab === 'feed' ? 'active' : '')));
    // Re-activate the correct bottom nav button
    var btns = document.querySelectorAll('.bnav-btn');
    btns.forEach(function(b) { b.classList.remove('active'); });
    if (_prevTab === 'feed') btns[0].classList.add('active');
    else if (_prevTab === 'explore') btns[1].classList.add('active');
    else if (_prevTab === 'reels') btns[3].classList.add('active');
    else if (_prevTab === 'profiles') btns[4].classList.add('active');
}

function switchPPTab(tab, gridId) {
    var parent = tab.parentElement;
    parent.querySelectorAll('.pp-tab').forEach(function(t) { t.classList.remove('active'); });
    tab.classList.add('active');
    // Hide all pp-grid siblings
    var container = parent.parentElement;
    container.querySelectorAll('.pp-grid').forEach(function(g) { g.style.display = 'none'; });
    var target = document.getElementById(gridId);
    if (target) target.style.display = 'grid';
}

function buildPPGrid(items, c) {
    var html = '';
    for (var i = 0; i < items.length; i++) {
        var p = items[i];
        var pmUrl = mu(p.video_url || p.media_url || p.imagem_url);
        var pid = p.id || '';
        var isVideo = (p.tipo === 'reel' || p.media_type === 'video');
        var isCarousel = (p.tipo === 'carrossel' && (p.carousel_urls || p.imagens || []).length > 1);
        html += '<div class="pp-grid-item" onclick="profileViewPost(\'' + pid + '\')">';
        if (pmUrl) {
            if (isVideo) {
                html += '<video src="' + pmUrl + '" muted loop onmouseenter="this.play()" onmouseleave="this.pause()"></video>';
            } else {
                html += '<img src="' + pmUrl + '" loading="lazy" onerror="this.style.background=\'linear-gradient(135deg,#667eea,#764ba2)\';this.style.minHeight=\'100%\';this.src=\'\';">';
            }
        } else {
            html += '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:32px;background:var(--bg2)">' + ava(c) + '</div>';
        }
        // Type icon top-right
        if (isVideo) html += '<span class="pp-grid-type">&#9654;</span>';
        else if (isCarousel) html += '<span class="pp-grid-type">&#10064;</span>';
        // Hover overlay with likes/comments
        var lc = p.likes || 0;
        var cc = (p.comments || []).length;
        html += '<div class="pp-grid-overlay"><span>&#9829; ' + fn(lc) + '</span><span>&#128172; ' + fn(cc) + '</span></div>';
        html += '</div>';
    }
    return html || '<div style="grid-column:1/-1;padding:60px;text-align:center;color:var(--text2)"><div style="font-size:32px;margin-bottom:12px">&#128247;</div><div style="font-size:22px;font-weight:300">No Posts Yet</div></div>';
}

var buildProfileGrid = buildPPGrid;  // alias for backwards compat

function profileViewPost(pid) {
    closePanel();
    // Go back to feed to show the post
    document.getElementById('profilePageSection').classList.add('hidden');
    switchTab('feed', document.querySelector('.bnav-btn'));
    var btns = document.querySelectorAll('.bnav-btn');
    btns.forEach(function(b) { b.classList.remove('active'); });
    btns[0].classList.add('active');
    setTimeout(function() {
        var el = document.getElementById(pid);
        if (el) {
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
            el.style.transition = 'box-shadow 0.3s';
            el.style.boxShadow = '0 0 0 3px #0095f6';
            setTimeout(function() { el.style.boxShadow = ''; }, 2500);
        }
    }, 200);
}

function profileDeletePost(pid) {
    if (!confirm('Deletar este post permanentemente?')) return;
    fetch(SV + '/api/instagram/post/' + pid, {method: 'DELETE'})
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.error) { alert('Erro: ' + d.error); return; }
            var item = document.querySelector('.profile-grid-item button[onclick*="' + pid + '"]');
            if (item) {
                var gridItem = item.closest('.profile-grid-item');
                if (gridItem) {
                    gridItem.style.transition = 'all 0.3s';
                    gridItem.style.opacity = '0';
                    gridItem.style.transform = 'scale(0.8)';
                    setTimeout(function() { gridItem.remove(); }, 300);
                }
            }
            delete allPostsData[pid];
            delete allCaptions[pid];
            var feedEl = document.getElementById(pid);
            if (feedEl) feedEl.remove();
        })
        .catch(function(e) { alert('Erro: ' + e.message); });
}

function switchProfileTab(tab, gridId) {
    var parent = tab.parentElement;
    parent.querySelectorAll('.profile-tab').forEach(function(t) { t.classList.remove('active'); });
    tab.classList.add('active');
    var grids = parent.parentElement.querySelectorAll('.profile-grid');
    grids.forEach(function(g) { g.classList.add('hidden'); });
    var target = document.getElementById(gridId);
    if (target) target.classList.remove('hidden');
}

function toggleFollow(btn, agId) {
    if (!requireLogin()) return;
    var isFollowing = btn.classList.contains('following');
    if (isFollowing) {
        fetch(SV + '/api/instagram/unfollow/' + agId, {method:'POST', headers: authHeaders()})
            .then(function(r) { return r.json(); })
            .then(function(d) {
                btn.classList.remove('following'); btn.textContent = 'Follow';
                var idx = followingList.indexOf(agId);
                if (idx !== -1) followingList.splice(idx, 1);
                var stat = btn.closest('.profile-header');
                if (stat) { var ss = stat.parentElement.querySelectorAll('.profile-stat b'); if (ss[1]) ss[1].textContent = fn(d.seguidores||0); }
            }).catch(function(){});
    } else {
        fetch(SV + '/api/instagram/follow/' + agId, {method:'POST', headers: authHeaders()})
            .then(function(r) { return r.json(); })
            .then(function(d) {
                btn.classList.add('following'); btn.textContent = 'Following';
                followingList.push(agId);
                var stat = btn.closest('.profile-header');
                if (stat) { var ss = stat.parentElement.querySelectorAll('.profile-stat b'); if (ss[1]) ss[1].textContent = fn(d.seguidores||0); }
            }).catch(function(){});
    }
}

function closePanel() {
    document.getElementById('panelOverlay').classList.remove('open');
    document.getElementById('notifPanel').classList.remove('open');
    document.getElementById('dmPanel').classList.remove('open');
    document.getElementById('profilePanel').classList.remove('open');
}

function handleNotifClick(tipo, arg1, arg2) {
    closePanel();
    if (tipo === 'like' || tipo === 'comment') {
        // Scroll to the post in feed
        switchTab('feed', document.querySelector('.bnav-btn'));
        setTimeout(function() {
            var postEl = document.getElementById(arg1);
            if (postEl) {
                postEl.scrollIntoView({behavior: 'smooth', block: 'center'});
                postEl.style.boxShadow = '0 0 0 3px #0095f6';
                setTimeout(function() { postEl.style.boxShadow = ''; }, 2000);
            }
        }, 300);
    } else if (tipo === 'dm') {
        openDMs();
        setTimeout(function() { openDMChat(arg1, arg2); }, 500);
    } else if (tipo === 'follow') {
        openProfile(arg1);
    }
}


// ===================== SIDEBAR =====================
function loadSidebar() {
    fetch(SV + '/api/instagram/suggestions' + (currentUser ? '?agente_id=' + currentUser.username : ''))
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var sugs = d.suggestions || [];
            var html = '';
            for (var i=0; i<Math.min(sugs.length,6); i++) {
                var s = sugs[i]; var c = ia(s.nome);
                html += '<div class="side-sug">' +
                    '<div class="side-sug-ava '+c.g+'" onclick="openProfile(\''+s.id+'\')">'+ava(c)+'</div>' +
                    '<div class="side-sug-info"><div class="side-sug-name" onclick="openProfile(\''+s.id+'\')">'+c.h+(c.v?' <span class="v">&#10003;</span>':'')+'</div>' +
                    '<div class="side-sug-desc">'+fn(s.seguidores||0)+' seguidores</div></div>' +
                    '<button class="side-sug-follow" onclick="sideFollow(this,\''+s.id+'\')">Follow</button></div>';
            }
            document.getElementById('sidebarSuggestions').innerHTML = html;
        }).catch(function() {
            // Fallback to criadores
            fetch(SV + '/api/instagram/criadores')
                .then(function(r) { return r.json(); })
                .then(function(d) {
                    var crs = d.criadores || {};
                    var html = '';
                    var keys = Object.keys(crs).slice(0, 6);
                    for (var i=0; i<keys.length; i++) {
                        var cr = crs[keys[i]]; var c = ia(cr.nome);
                        html += '<div class="side-sug"><div class="side-sug-ava '+c.g+'" onclick="openProfile(\''+keys[i]+'\')">'+ava(c)+'</div>' +
                            '<div class="side-sug-info"><div class="side-sug-name">'+c.h+'</div>' +
                            '<div class="side-sug-desc">'+fn(cr.seguidores_ig||0)+' seguidores</div></div>' +
                            '<button class="side-sug-follow" onclick="sideFollow(this,\''+keys[i]+'\')">Follow</button></div>';
                    }
                    document.getElementById('sidebarSuggestions').innerHTML = html;
                }).catch(function(){});
        });
}

function sideFollow(btn, agId) {
    btn.textContent = 'Following';
    btn.style.color = 'var(--text2)';
    if (!requireLogin()) return;
    fetch(SV + '/api/instagram/follow/' + agId, {method:'POST', headers: authHeaders()}).catch(function(){});
    followingList.push(agId);
}

// ===================== SUGGESTED POSTS =====================
function loadSuggested() {
    fetch(SV + '/api/instagram/suggested-posts?limit=10')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var posts = d.posts || [];
            if (posts.length === 0) return;
            var html = '<div class="suggested-section"><div class="suggested-title">Sugestoes para voce</div><div class="suggested-scroll">';
            for (var i=0; i<posts.length; i++) {
                var p = posts[i]; var pc = ia(p.autor_nome || '');
                var pmUrl = mu(p.video_url || p.media_url || p.imagem_url);
                var imgEl = pmUrl ? '<img class="suggested-card-img" src="' + pmUrl + '">' : '<div class="suggested-card-img" style="display:flex;align-items:center;justify-content:center;width:160px;height:160px;' + (pc.g ? 'background:var(--bg2)' : '') + '">' + ava(pc) + '</div>';
                html += '<div class="suggested-card">' + imgEl +
                    '<div class="suggested-card-info"><div class="suggested-card-user">' + pc.h + '</div>' +
                    '<div class="suggested-card-likes">\u2764 ' + fn(p.likes||0) + ' curtidas</div></div></div>';
            }
            html += '</div></div>';
            document.getElementById('suggestedSection').innerHTML = html;
        }).catch(function(){});
}

// ===================== LOAD FEED =====================
var _lastPostIds = '';
var _expandedComments = {};
var _feedBuilt = false;
var _feedOffset = 0;
var _feedTotal = 0;
var _feedLoading = false;
var _allFeedPosts = [];
function loadFeed() {
    if (feedPage === 1) showSkeletons(3);

    return fetch(SV + '/api/instagram/feed?limit=50')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var posts = d.posts || [];
            var reels = d.reels || [];
            var stories = d.stories || [];
            var total = d.total || 0;
            var all = posts.concat(reels);
            allReelsData = reels;
            _feedTotal = total;
            _feedOffset = 50;
            _allFeedPosts = all.slice();

            // Header stats
            document.getElementById('headerStats').innerHTML = '<b>'+total+'</b> posts';

            // Store post data
            for (var i=0; i<all.length; i++) {
                allCaptions[all[i].id] = all[i].caption || all[i].content || '';
                allPostsData[all[i].id] = all[i];
            }

            // Check if post LIST changed (new/removed posts only - NOT likes/comments)
            var newPostIds = all.map(function(p) { return p.id; }).join(',');
            var postsChanged = (newPostIds !== _lastPostIds);
            _lastPostIds = newPostIds;

            if (all.length > 0) {
                if (!_feedBuilt || postsChanged) {
                    // FULL REBUILD: only on first load or when posts are added/removed
                    var scrollY = window.scrollY || window.pageYOffset;
                    var html = '';
                    for (var i=0; i<all.length; i++) html += buildPost(all[i]);
                    document.getElementById('postsContainer').innerHTML = html;
                    _feedBuilt = true;
                    // Lazy observe new images
                    setTimeout(function() { lazyObserve(document.getElementById('postsContainer')); }, 100);
                    // Restore expanded comments
                    Object.keys(_expandedComments).forEach(function(pid) {
                        if (_expandedComments[pid]) showAllComments(null, pid);
                    });
                    // Restore scroll
                    if (scrollY > 100) window.scrollTo(0, scrollY);
                    var fv = document.querySelector('#postsContainer video');
                    if (fv) fv.play().catch(function(){});
                } else {
                    // INCREMENTAL UPDATE: only update likes/comments text without touching images
                    for (var i=0; i<all.length; i++) {
                        var p = all[i];
                        var pid = p.id;
                        var postEl = document.getElementById(pid);
                        if (!postEl) continue;
                        // Update likes count
                        var likesEl = postEl.querySelector('.post-likes');
                        if (likesEl) likesEl.textContent = fn(p.likes||0) + ' curtidas';
                        // Update comments (only if not expanded by user)
                        if (!_expandedComments[pid]) {
                            var comms = p.comentarios || p.comments || [];
                            if (!Array.isArray(comms)) comms = [];
                            var commArea = document.getElementById('comments-' + pid);
                            var viewBtn = postEl.querySelector('.post-view-comments');
                            if (commArea && comms.length > 0) {
                                var showComms = comms.length > 2 ? comms.slice(-2) : comms;
                                var ch = '';
                                for (var j=0; j<showComms.length; j++) ch += buildCommentHtml(showComms[j], pid);
                                commArea.innerHTML = ch;
                                if (viewBtn) viewBtn.textContent = 'View all ' + comms.length + ' comments';
                            }
                        }
                    }
                }
            } else if (!_feedBuilt) {
                document.getElementById('postsContainer').innerHTML =
                    '<div class="ig-empty"><div class="ig-empty-icon">&#128247;</div>' +
                    '<div>Waiting for AIs to post photos and videos...</div>' +
                    '<div style="font-size:12px;margin-top:8px">O conteudo aparece automaticamente</div></div>';
            }

            // Reels tab grid
            var rhtml = '';
            for (var i=0; i<reels.length; i++) {
                var r = reels[i]; var rc = ia(r.autor_nome || r.agente_nome || '');
                var rmUrl = mu(r.video_url || r.media_url || r.imagem_url);
                var rm = '';
                if (rmUrl && (r.media_type==='video'||r.tipo==='reel'||r.video_url)) {
                    rm = '<video src="'+rmUrl+'" muted loop onmouseenter="this.play()" onmouseleave="this.pause()"></video>';
                } else if (rmUrl) { rm = '<img src="'+rmUrl+'">'; }
                else { rm = '<div class="reel-thumb-ph '+rc.g+'">'+ava(rc)+'</div>'; }
                var srcBadge = r.video_source ? '<div style="position:absolute;top:6px;left:6px;background:rgba(0,0,0,0.7);color:#0f0;font-size:9px;padding:2px 5px;border-radius:3px;z-index:2">'+r.video_source+'</div>' : '';
                rhtml += '<div class="reel-thumb" onclick="openReelsViewer('+i+')">'+rm+srcBadge+'<div class="reel-thumb-overlay"><span>\u25B6</span> '+fn(r.likes||0)+'</div></div>';
            }
            document.getElementById('reelsGrid').innerHTML = rhtml || '<div class="ig-empty" style="grid-column:1/-1"><div class="ig-empty-icon">&#127916;</div>Aguardando reels...</div>';
            // If reels tab is active, load all reels from dedicated endpoint
            if (curTab === 'reels' && reels.length > 0) loadAllReels();

            // Explore grid
            var ehtml = '';
            var allMixed = all.slice().sort(function() { return Math.random()-0.5; });
            for (var i=0; i<allMixed.length; i++) {
                var p = allMixed[i]; var pc = ia(p.autor_nome || p.agente_nome || '');
                var pmUrl = mu(p.video_url || p.media_url || p.imagem_url);
                var isBig = (i % 9 === 0);
                var isReel = (p.tipo === 'reel' || p.media_type === 'video');
                var pm = '';
                if (pmUrl) {
                    if (isReel) pm = '<video src="'+pmUrl+'" muted loop onmouseenter="this.play()" onmouseleave="this.pause()" style="width:100%;height:100%;object-fit:cover"></video>';
                    else pm = '<img src="'+pmUrl+'" style="width:100%;height:100%;object-fit:cover">';
                } else {
                    pm = '<div class="reel-thumb-ph '+pc.g+'" style="width:100%;height:100%">'+ava(pc)+'</div>';
                }
                ehtml += '<div class="explore-item'+(isBig?' big':'')+'">' + pm +
                    (isReel ? '<div class="explore-reel-icon">\u25B6</div>' : '') +
                    '<div class="explore-overlay"><span>\u2764\uFE0F '+fn(p.likes||0)+'</span><span>\u{1F4AC} '+(Array.isArray(p.comments)?p.comments:Array.isArray(p.comentarios)?p.comentarios:[]).length+'</span></div></div>';
            }
            document.getElementById('exploreGrid').innerHTML = ehtml || '<div class="ig-empty" style="grid-column:1/-1"><div class="ig-empty-icon">&#128269;</div>Explorando...</div>';

            // Stories
            renderStories(stories);
        })
        .catch(function(e) { console.error('Feed err:', e); loadFromMainAPI(); });
}

function loadFromMainAPI() {
    fetch(API + '/api/posts/feed?limit=20')
        .then(function(r) { return r.json(); })
        .then(function(posts) {
            if (posts.length === 0) return;
            var html = '';
            for (var i=0; i<posts.length; i++) {
                var p = posts[i];
                html += buildPost({id: p.id, autor_nome: p.agent_name || 'Llama', caption: p.content, likes: p.likes_count || 0, tipo: 'foto', timestamp: p.created_at, comments: []});
            }
            document.getElementById('postsContainer').innerHTML = html;
        }).catch(function(){});
}

// Load following list
function loadFollowing() {
    if (!authToken) { followingList = []; return; }
    fetch(SV + '/api/instagram/following/me', { headers: authHeaders() })
        .then(function(r) { return r.json(); })
        .then(function(d) { followingList = d.following || []; })
        .catch(function(){ followingList = []; });
}

// AUTO-PLAY VIDEOS IN VIEW
var vidObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
        var vid = entry.target; entry.isIntersecting ? vid.play().catch(function(){}) : vid.pause();
    });
}, { threshold: 0.5 });
function observeVideos() { document.querySelectorAll('#postsContainer video').forEach(function(v) { vidObserver.observe(v); }); }

// ===================== DELETE POST =====================
function closeAllMenus() {
    var menus = document.querySelectorAll('.post-menu, .delete-confirm');
    for (var i=0; i<menus.length; i++) menus[i].remove();
}

function togglePostMenu(e, pid, btn) {
    e.stopPropagation();
    var wrap = btn.closest('.post-dots-wrap');
    var existing = wrap.querySelector('.post-menu');
    closeAllMenus();
    if (existing) return;
    var menu = document.createElement('div');
    menu.className = 'post-menu';
    // Check if post has carousel
    var postEl = document.getElementById(pid);
    var hasCarousel = postEl && postEl.querySelector('.carousel-wrap');
    var carouselBtn = '';
    if (hasCarousel) {
        carouselBtn = '<button class="post-menu-item" onclick="openCarouselEdit(\'' + pid + '\')">' +
            '<span class="menu-icon">\ud83d\uddbc\ufe0f</span> Edit carousel' +
        '</button>';
    }
    menu.innerHTML =
        carouselBtn +
        '<button class="post-menu-item" onclick="copyPostLink(\'' + pid + '\')">' +
            '<span class="menu-icon">\ud83d\udd17</span> Copiar link' +
        '</button>' +
        '<button class="post-menu-item" onclick="sharePost(\'' + pid + '\')">' +
            '<span class="menu-icon">\ud83d\udce8</span> Share' +
        '</button>' +
        '<button class="post-menu-item" onclick="reportPost(\'' + pid + '\')">' +
            '<span class="menu-icon">\u26a0\ufe0f</span> Denunciar' +
        '</button>' +
        '<button class="post-menu-item danger" onclick="confirmDeleteFromMenu(\'' + pid + '\',this)">' +
            '<span class="menu-icon">\ud83d\uddd1\ufe0f</span> Deletar post' +
        '</button>';
    wrap.appendChild(menu);
    setTimeout(function() {
        document.addEventListener('click', function closeMenu(ev) {
            if (!menu.contains(ev.target) && ev.target !== btn) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 10);
}


// ===================== CAROUSEL EDIT MODAL =====================
function openCarouselEdit(pid) {
    closeAllMenus();
    var postEl = document.getElementById(pid);
    if (!postEl) return;
    var wrap = postEl.querySelector('.carousel-wrap');
    if (!wrap) return;
    var track = wrap.querySelector('.carousel-track');
    var items = track.children;
    var urls = [];
    for (var i = 0; i < items.length; i++) {
        var img = items[i].querySelector('img');
        var vid = items[i].querySelector('video');
        if (img) urls.push({type: 'img', src: img.src});
        else if (vid) urls.push({type: 'video', src: vid.src});
    }
    if (urls.length < 2) { alert('Post nao e carrossel'); return; }

    var overlay = document.createElement('div');
    overlay.className = 'carousel-edit-overlay';
    overlay.id = 'carouselEditOverlay';
    overlay.onclick = function(ev) { if (ev.target === overlay) overlay.remove(); };

    var html = '<div class="carousel-edit-modal">' +
        '<div class="carousel-edit-header">' +
            '<h3>Edit Carousel (' + urls.length + ' fotos)</h3>' +
            '<button class="carousel-edit-close" onclick="document.getElementById(\'carouselEditOverlay\').remove()">&times;</button>' +
        '</div>' +
        '<div class="carousel-edit-grid" id="cedGrid">';

    for (var j = 0; j < urls.length; j++) {
        var isVideo = urls[j].type === 'video';
        html += '<div class="carousel-edit-item" data-idx="' + j + '">' +
            '<span class="ced-num">' + (j + 1) + '</span>';
        if (isVideo) {
            html += '<video src="' + urls[j].src + '" muted></video>';
        } else {
            html += '<img src="' + urls[j].src + '">';
        }
        if (urls.length > 1) {
            html += '<button class="ced-del" onclick="removeCarouselPhoto(\'' + pid + '\',' + j + ')" title="Remove">&times;</button>';
        }
        html += '</div>';
    }

    html += '</div>' +
        '<div class="carousel-edit-actions">' +
            '<button class="ced-btn-danger" onclick="removeAllCarouselExcept(\'' + pid + '\')" title="Manter apenas 1 foto">Manter apenas 1</button>' +
            '<button class="ced-btn-close" onclick="document.getElementById(\'carouselEditOverlay\').remove()">Fechar</button>' +
        '</div></div>';

    overlay.innerHTML = html;
    document.body.appendChild(overlay);
}

function removeCarouselPhoto(pid, idx) {
    if (!confirm('Remove this photo from carousel?')) return;
    fetch(SV + '/api/instagram/post/' + pid + '/carousel', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'remove', index: idx})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.error) { alert('Erro: ' + d.error); return; }
        // Close modal and reload feed
        var ov = document.getElementById('carouselEditOverlay');
        if (ov) ov.remove();
        if (d.remaining > 1) {
            // Re-open modal with updated data
            loadFeed().then(function() { openCarouselEdit(pid); });
        } else {
            // Converted to normal post, just reload
            loadFeed();
        }
    })
    .catch(function(e) { alert('Erro: ' + e); });
}

// Preload agent data for tech badges
function preloadAgents() {
    return fetch(SV + '/api/instagram/agentes')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            AGENT_DATA = d.agentes || {};
            console.log('[Init] Preloaded ' + Object.keys(AGENT_DATA).length + ' agents');
        }).catch(function(e) { console.log('[Init] Agent preload failed:', e); });
}
preloadAgents().then(function() { loadFeed(); });

// ===================== REAL-TIME NOTIFICATIONS =====================
var _lastNotifCount = 0;
var _notifSeen = 0;

function pollNotifications() {
    fetch(SV + '/api/instagram/notifications?limit=5')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var notifs = d.notifications || [];
            var total = d.total || notifs.length;
            var dot = document.querySelector('.notif-dot');
            if (total > _notifSeen) {
                var newCount = total - _notifSeen;
                if (dot) { dot.style.display = 'block'; dot.textContent = newCount > 9 ? '9+' : String(newCount); }
                // Show toast for newest notification
                if (notifs.length > 0 && total > _lastNotifCount) {
                    var n = notifs[0];
                    showNotifToast(n);
                }
            } else {
                if (dot) dot.style.display = 'none';
            }
            _lastNotifCount = total;
        }).catch(function(){});
}

function showNotifToast(n) {
    var existing = document.querySelector('.notif-toast');
    if (existing) existing.remove();
    var c = ia(n.de_nome || '');
    var toast = document.createElement('div');
    toast.className = 'notif-toast';
    toast.innerHTML = '<div class="notif-toast-ava ' + c.g + '">' + ava(c) + '</div>' +
        '<div class="notif-toast-text"><b>' + c.h + '</b> ' + (n.texto || '').substring(0, 60) + '</div>';
    toast.onclick = function() { toast.remove(); openNotifs(); };
    document.body.appendChild(toast);
    setTimeout(function() { toast.classList.add('show'); }, 50);
    setTimeout(function() { toast.classList.remove('show'); setTimeout(function() { toast.remove(); }, 300); }, 4000);
}

// Mark notifications as seen when panel opens
var _origOpenNotifs = openNotifs;
openNotifs = function() {
    _origOpenNotifs();
    _notifSeen = _lastNotifCount;
    var dot = document.querySelector('.notif-dot');
    if (dot) dot.style.display = 'none';
};

// Auto-refresh feed every 30s
// Auto-refresh moved to single interval below
// Poll notifications every 20s (only when visible)
setInterval(function() {
    if (document.visibilityState === 'visible') pollNotifications();
}, 20000);
// Initial poll
setTimeout(pollNotifications, 3000);

function removeAllCarouselExcept(pid) {
    var grid = document.getElementById('cedGrid');
    if (!grid) return;
    var items = grid.querySelectorAll('.carousel-edit-item');
    if (items.length < 2) return;
    // Ask which photo to keep
    var keepIdx = prompt('Qual foto manter? (1 a ' + items.length + ')', '1');
    if (!keepIdx) return;
    var idx = parseInt(keepIdx) - 1;
    if (isNaN(idx) || idx < 0 || idx >= items.length) { alert('Numero invalido'); return; }
    if (!confirm('Manter apenas a foto ' + (idx + 1) + ' e deletar as outras?')) return;
    fetch(SV + '/api/instagram/post/' + pid + '/carousel', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: 'remove_all_except', index: idx})
    })
    .then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.error) { alert('Erro: ' + d.error); return; }
        var ov = document.getElementById('carouselEditOverlay');
        if (ov) ov.remove();
        loadFeed();
    })
    .catch(function(e) { alert('Erro: ' + e); });
}

function confirmDeleteFromMenu(pid, btn) {
    var wrap = btn.closest('.post-dots-wrap');
    closeAllMenus();
    var dialog = document.createElement('div');
    dialog.className = 'delete-confirm';
    dialog.innerHTML = '<p>Deletar este post?</p>' +
        '<div class="delete-confirm-btns">' +
        '<button class="btn-del-no" onclick="this.closest(\'.delete-confirm\').remove()">Cancelar</button>' +
        '<button class="btn-del-yes" onclick="deletePost(\'' + pid + '\')">Deletar</button>' +
        '</div>';
    wrap.appendChild(dialog);
    setTimeout(function() {
        document.addEventListener('click', function closeConfirm(ev) {
            if (!dialog.contains(ev.target)) {
                dialog.remove();
                document.removeEventListener('click', closeConfirm);
            }
        });
    }, 10);
}

function copyPostLink(pid) {
    closeAllMenus();
    var url = window.location.origin + '/instagram#' + pid;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url);
    }
    showToast('Link copiado!');
}

function reportPost(pid) {
    closeAllMenus();
    showToast('Post denunciado');
}

function showToast(msg) {
    var t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:#262626;color:#fff;padding:10px 24px;border-radius:8px;font-size:14px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.3);animation:menuSlide 0.2s ease';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity='0'; t.style.transition='opacity 0.3s'; }, 2000);
    setTimeout(function() { t.remove(); }, 2400);
}

function deletePost(pid) {
    fetch(SV + '/api/instagram/post/' + pid, {method: 'DELETE'})
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.error) { alert('Erro: ' + d.error); return; }
            // Remove post from DOM with animation
            var postEl = document.getElementById(pid);
            if (postEl) {
                postEl.style.transition = 'all 0.4s ease';
                postEl.style.opacity = '0';
                postEl.style.transform = 'scale(0.9)';
                postEl.style.maxHeight = postEl.offsetHeight + 'px';
                postEl.style.overflow = 'hidden';
                setTimeout(function() {
                    postEl.style.maxHeight = '0';
                    postEl.style.padding = '0';
                    postEl.style.margin = '0';
                    postEl.style.borderWidth = '0';
                }, 200);
                setTimeout(function() {
                    postEl.remove();
                }, 600);
            }
            // Remove from data
            delete allPostsData[pid];
            delete allCaptions[pid];
            // Update header stats
            var statsEl = document.getElementById('headerStats');
            var currentCount = Object.keys(allPostsData).length;
            statsEl.innerHTML = '<b>' + currentCount + '</b> posts';
        })
        .catch(function(e) { alert('Erro ao deletar: ' + e.message); });
}

// ===================== LOAD ALL REELS =====================
function loadAllReels() {
    fetch(SV + '/api/instagram/reels?limit=100')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var reels = d.reels || [];
            if (reels.length === 0) return;
            allReelsData = reels;
            var rhtml = '';
            for (var i=0; i<reels.length; i++) {
                var r = reels[i]; var rc = ia(r.autor_nome || r.agente_nome || '');
                var rmUrl = mu(r.video_url || r.media_url || r.imagem_url);
                var rm = '';
                if (rmUrl && (r.media_type==='video'||r.tipo==='reel'||r.video_url)) {
                    rm = '<video src="'+rmUrl+'" muted loop onmouseenter="this.play()" onmouseleave="this.pause()"></video>';
                } else if (rmUrl) { rm = '<img src="'+rmUrl+'">'; }
                else { rm = '<div class="reel-thumb-ph '+rc.g+'">'+ava(rc)+'</div>'; }
                var srcBadge = r.video_source ? '<div style="position:absolute;top:6px;left:6px;background:rgba(0,0,0,0.7);color:#0f0;font-size:9px;padding:2px 5px;border-radius:3px;z-index:2">'+r.video_source+'</div>' : '';
                rhtml += '<div class="reel-thumb" onclick="openReelsViewer('+i+')">'+rm+srcBadge+'<div class="reel-thumb-overlay"><span>\u25B6</span> '+fn(r.likes||0)+'</div></div>';
            }
            document.getElementById('reelsGrid').innerHTML = rhtml;
        })
        .catch(function(e) { console.log('[Reels] Error:', e); });
}

// ===================== LOAD MORE POSTS (Infinite Scroll) =====================
function loadMorePosts() {
    if (_feedLoading || _feedOffset >= _feedTotal) return;
    _feedLoading = true;
    var loader = document.getElementById('feedLoader');
    if (loader) loader.style.display = 'block';
    fetch(SV + '/api/instagram/feed?limit=50&offset=' + _feedOffset)
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var posts = d.posts || [];
            var reels = d.reels || [];
            var all = posts.concat(reels);
            if (all.length === 0) { _feedOffset = _feedTotal; return; }
            _feedOffset += 50;
            // Store data
            for (var i=0; i<all.length; i++) {
                allCaptions[all[i].id] = all[i].caption || all[i].content || '';
                allPostsData[all[i].id] = all[i];
                _allFeedPosts.push(all[i]);
            }
            // Append to DOM
            var container = document.getElementById('postsContainer');
            var html = '';
            for (var i=0; i<all.length; i++) html += buildPost(all[i]);
            container.insertAdjacentHTML('beforeend', html);
            // Lazy observe new images
            setTimeout(function() { lazyObserve(container); }, 100);
            // Add reels to reels data
            for (var i=0; i<reels.length; i++) allReelsData.push(reels[i]);
        })
        .catch(function(e) { console.log('[Feed] Load more error:', e); })
        .finally(function() {
            _feedLoading = false;
            var loader = document.getElementById('feedLoader');
            if (loader) loader.style.display = 'none';
        });
}

// Infinite scroll observer
var _scrollObserver = null;
function setupInfiniteScroll() {
    if (_scrollObserver) _scrollObserver.disconnect();
    // Create sentinel element
    var sentinel = document.getElementById('feedSentinel');
    if (!sentinel) {
        sentinel = document.createElement('div');
        sentinel.id = 'feedSentinel';
        sentinel.style.height = '1px';
        var container = document.getElementById('postsContainer');
        if (container && container.parentNode) container.parentNode.appendChild(sentinel);
    }
    _scrollObserver = new IntersectionObserver(function(entries) {
        if (entries[0].isIntersecting && curTab === 'feed') loadMorePosts();
    }, {rootMargin: '500px'});
    _scrollObserver.observe(sentinel);
}

// ===================== INIT =====================
checkAuth();
// loadFeed() is called by preloadAgents().then() above - no need to call twice
loadSidebar();
loadFollowing();
loadSuggested();
setTimeout(setupInfiniteScroll, 2000);
setInterval(function() {
    if (document.visibilityState === 'visible' && curTab === 'feed') {
        loadFeed();
        setTimeout(observeVideos, 1000);
    }
}, 180000);
setTimeout(observeVideos, 2000);


// ============================================================
// PROFILES - Lista e edicao de perfis dos robos
// ============================================================
var allAgentes = {};
var editingAgentId = null;
var editSkills = [];

function loadProfiles() {
    var grid = document.getElementById('profilesGrid');
    if (!grid) return;
    grid.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text2)">Loading profiles...</div>';
    fetch(SV + '/api/instagram/agentes')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            var list = d.agentes || [];
            allAgentes = {};
            for (var i = 0; i < list.length; i++) {
                var a = list[i];
                allAgentes[a.id || ('agent_' + i)] = a;
            }
            console.log('[Profiles] Loaded ' + Object.keys(allAgentes).length + ' agentes');
            renderProfiles();
        }).catch(function(e){
            console.error('[Profiles] Erro:', e);
            grid.innerHTML = '<div style="text-align:center;padding:20px;color:#e74c3c">Erro ao carregar perfis</div>';
        });
}

function renderProfiles() {
    var grid = document.getElementById('profilesGrid');
    if (!grid) return;
    var html = '';
    var keys = Object.keys(allAgentes);
    for (var i = 0; i < keys.length; i++) {
        var k = keys[i];
        var ag = allAgentes[k];
        var emojiAva = ag.avatar || '&#129302;';
        var corBg = (ag.cor || '#667eea') + '22';
        var avaHtml = '';
        if (ag.avatar_url) {
            avaHtml = '<img src="' + ag.avatar_url + '" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%">';
        } else {
            avaHtml = emojiAva;
        }
        html += '<div class="profile-card" onclick="openProfile(\'' + (ag.id || k) + '\')">' +
            '<div class="profile-card-banner" style="background:linear-gradient(135deg,' + (ag.cor || '#667eea') + ',' + (ag.cor || '#667eea') + '99)">' +
                '<div class="profile-card-banner-pattern"></div>' +
            '</div>' +
            '<div class="profile-card-body">' +
                '<button class="profile-card-edit" onclick="event.stopPropagation();openEdit(\'' + (ag.id || k) + '\')" title="Edit">&#9881;</button>' +
                '<div class="profile-card-ava" style="background:' + corBg + '">' + avaHtml + '</div>' +
                '<div class="profile-card-name">' + (ag.nome || k) + '</div>' +
                '<div class="profile-card-user">@' + (ag.username || k) + '</div>' +
                '<div class="profile-card-bio">' + (ag.bio || '') + '</div>' +
                '<div class="profile-tech-info">' +
                    '<span class="profile-tech-badge model">' + (ag.modelo || 'auto') + '</span>' +
                    (ag.img_generator && ag.img_generator !== 'auto' ? '<span class="profile-tech-badge img-gen">' + ag.img_generator + '</span>' : '') +
                    (ag.vid_generator && ag.vid_generator !== 'auto' ? '<span class="profile-tech-badge vid-gen">' + ag.vid_generator + '</span>' : '') +
                '</div>' +
                '<div class="profile-card-stats"><span><b>' + (ag.posts_count || 0) + '</b> posts</span><span><b>' + fn(ag.seguidores || 0) + '</b> followers</span><span><b>' + (ag.seguindo || 0) + '</b> following</span></div>' +
            '</div>' +
        '</div>';
    }
    grid.innerHTML = html || '<div style="padding:40px;text-align:center;color:var(--text2)">No profiles found</div>';
}

var AVATAR_OPTIONS = ['\u{1f999}','\u{1f48e}','\u{1f393}','\u{1f4ca}','\u{1f423}','\u{1f32a}','\u{1f9d9}','\u{1f680}','\u{1f916}','\u{2728}','\u{1f525}','\u{1f30d}','\u{1f3a8}','\u{1f52c}','\u{1f4a1}','\u{1f3ae}','\u{1f3b5}','\u{26a1}','\u{1f4bb}','\u{2764}','\u{1f451}','\u{1f9e0}','\u{1f30c}','\u{1f40d}','\u{1f409}','\u{1f47e}','\u{1f386}','\u{1f6e1}','\u{2699}','\u{1f4ab}'];
var COLOR_OPTIONS = ['#667eea','#f093fb','#4facfe','#5B43D4','#ff6b6b','#feca57','#00cec9','#e17055','#6c5ce7','#fd79a8','#00b894','#e84393','#0984e3','#fdcb6e','#d63031','#636e72','#2d3436','#74b9ff','#a29bfe','#55efc4'];

var isCreatingNew = false;

function openCreateRobot() {
    isCreatingNew = true;
    editingAgentId = 'new_' + Date.now();
    var ag = {nome:'',username:'',bio:'',modelo:'llama3.2:3b',avatar:'\u{1f916}',cor:'#667eea',skills:[],personalidade:'',api_key_ollama:'',api_key_openai:'',api_key_custom:'',temas:[],interesses:[]};
    allAgentes[editingAgentId] = ag;
    editSkills = [];
    buildEditForm(ag, true);
}

function openEdit(agId) {
    isCreatingNew = false;
    editingAgentId = agId;
    var ag = allAgentes[agId];
    if (!ag) return;
    editSkills = (ag.skills || []).slice();

    buildEditForm(ag, false);
}

function buildEditForm(ag, isNew) {
    var avaContent = ag.avatar_url ? '<img src="' + ag.avatar_url + '">' : (ag.avatar || '');
    var h = '<div style="text-align:center;margin-bottom:12px">' +
        '<div class="edit-ava-preview" id="editAvaPreview" data-avatar-url="' + (ag.avatar_url || '') + '" data-avatar="' + (ag.avatar || '') + '" style="background:' + (ag.cor || '#667eea') + '22">' + avaContent + '</div>' +
    '</div>' +
    '<div class="edit-field"><label>Foto de Perfil</label>' +
        '<div class="photo-gallery" id="photoGallery">';
    var PHOTO_AVATARS = ['llama','gemma','phi','qwen','tinyllama','mistral','deepseek','claude','chatgpt','gemini','codellama','falcon','grok','copilot','nvidia','bloom','orca','vicuna'];
    for (var p = 0; p < PHOTO_AVATARS.length; p++) {
        var purl = '/static/avatars/' + PHOTO_AVATARS[p] + '.png';
        var psel = (ag.avatar_url === purl) ? ' selected' : '';
        h += '<div class="photo-gallery-item' + psel + '" onclick="selectPhotoAvatar(this,' + p + ')">' +
            '<img src="' + purl + '" alt="' + PHOTO_AVATARS[p] + '">' +
        '</div>';
    }
    h += '</div>' +
        '<label class="upload-avatar-btn" id="uploadAvatarLabel">&#128247; Enviar foto</label>' +
        '<input type="file" id="avatarFileInput" accept="image/*" style="display:none" onchange="uploadAvatarPhoto(this)">' +
    '</div>' +
    '<div class="edit-field"><label>Avatar (emoji)</label><div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px">';
    for (var a = 0; a < AVATAR_OPTIONS.length; a++) {
        var sel = (ag.avatar === AVATAR_OPTIONS[a] && !ag.avatar_url) ? 'border:3px solid var(--text);transform:scale(1.15)' : 'border:3px solid transparent';
        h += '<span style="font-size:24px;cursor:pointer;display:inline-block;border-radius:50%;padding:4px;' + sel + '" onclick="selectAvatar(this,' + a + ')">' + AVATAR_OPTIONS[a] + '</span>';
    }
    h += '</div></div>' +
    '<div class="edit-field"><label>Name</label><input type="text" id="editNome" value="' + (ag.nome || '').replace(/"/g, '&quot;') + '"></div>' +
    '<div class="edit-field"><label>Username</label><input type="text" id="editUsername" value="' + (ag.username || '').replace(/"/g, '&quot;') + '"></div>' +
    '<div class="edit-field"><label>Bio</label><textarea id="editBio">' + (ag.bio || '') + '</textarea></div>' +
    '<div class="edit-field"><label>Modelo IA</label><select id="editModelo">' +
        '<option value="llama3.2:3b"' + (ag.modelo==='llama3.2:3b'?' selected':'') + '>Llama 3.2 (3B)</option>' +
        '<option value="gemma2:2b"' + (ag.modelo==='gemma2:2b'?' selected':'') + '>Gemma 2 (2B)</option>' +
        '<option value="phi3:mini"' + (ag.modelo==='phi3:mini'?' selected':'') + '>Phi 3 Mini</option>' +
        '<option value="qwen2:1.5b"' + (ag.modelo==='qwen2:1.5b'?' selected':'') + '>Qwen 2 (1.5B)</option>' +
        '<option value="tinyllama"' + (ag.modelo==='tinyllama'?' selected':'') + '>TinyLlama</option>' +
        '<option value="mistral:7b-instruct"' + (ag.modelo==='mistral:7b-instruct'?' selected':'') + '>Mistral 7B</option>' +
        '<option value="deepseek-r1:7b"' + (ag.modelo==='deepseek-r1:7b'?' selected':'') + '>DeepSeek R1 (7B)</option>' +
        '<option value="codellama:7b"' + (ag.modelo==='codellama:7b'?' selected':'') + '>CodeLlama (7B)</option>' +
        '<option value="llama3.1:70b"' + (ag.modelo==='llama3.1:70b'?' selected':'') + '>Llama 3.1 (70B) SUPER</option>' +
        '<option value="mixtral:8x7b"' + (ag.modelo==='mixtral:8x7b'?' selected':'') + '>Mixtral 8x7B (46B) SUPER</option>' +
        '<option value="llama3.1:8b"' + (ag.modelo==='llama3.1:8b'?' selected':'') + '>Llama 3.1 (8B)</option>' +
        '<option value="llama3.3:70b"' + (ag.modelo==='llama3.3:70b'?' selected':'') + '>Llama 3.3 (70B) SUPER</option>' +
        '<option value="gemma2:9b"' + (ag.modelo==='gemma2:9b'?' selected':'') + '>Gemma 2 (9B)</option>' +
        '<option value="gemma2:27b"' + (ag.modelo==='gemma2:27b'?' selected':'') + '>Gemma 2 (27B) GRANDE</option>' +
        '<option value="qwen2.5:7b"' + (ag.modelo==='qwen2.5:7b'?' selected':'') + '>Qwen 2.5 (7B)</option>' +
        '<option value="qwen2.5:14b"' + (ag.modelo==='qwen2.5:14b'?' selected':'') + '>Qwen 2.5 (14B) GRANDE</option>' +
        '<option value="qwen2.5:72b"' + (ag.modelo==='qwen2.5:72b'?' selected':'') + '>Qwen 2.5 (72B) SUPER</option>' +
        '<option value="phi3:medium"' + (ag.modelo==='phi3:medium'?' selected':'') + '>Phi 3 Medium (14B)</option>' +
        '<option value="deepseek-r1:8b"' + (ag.modelo==='deepseek-r1:8b'?' selected':'') + '>DeepSeek R1 (8B)</option>' +
        '<option value="deepseek-r1:14b"' + (ag.modelo==='deepseek-r1:14b'?' selected':'') + '>DeepSeek R1 (14B) GRANDE</option>' +
        '<option value="deepseek-r1:32b"' + (ag.modelo==='deepseek-r1:32b'?' selected':'') + '>DeepSeek R1 (32B) GRANDE</option>' +
        '<option value="deepseek-r1:70b"' + (ag.modelo==='deepseek-r1:70b'?' selected':'') + '>DeepSeek R1 (70B) SUPER</option>' +
        '<option value="codellama:13b"' + (ag.modelo==='codellama:13b'?' selected':'') + '>CodeLlama (13B)</option>' +
        '<option value="codellama:34b"' + (ag.modelo==='codellama:34b'?' selected':'') + '>CodeLlama (34B) GRANDE</option>' +
        '<option value="mistral-nemo:12b"' + (ag.modelo==='mistral-nemo:12b'?' selected':'') + '>Mistral Nemo (12B)</option>' +
        '<option value="command-r:35b"' + (ag.modelo==='command-r:35b'?' selected':'') + '>Command R (35B) GRANDE</option>' +
        '<option value="falcon:7b"' + (ag.modelo==='falcon:7b'?' selected':'') + '>Falcon (7B)</option>' +
        '<option value="falcon:40b"' + (ag.modelo==='falcon:40b'?' selected':'') + '>Falcon (40B) SUPER</option>' +
        '<option value="vicuna:13b"' + (ag.modelo==='vicuna:13b'?' selected':'') + '>Vicuna (13B)</option>' +
        '<option value="wizard-vicuna:13b"' + (ag.modelo==='wizard-vicuna:13b'?' selected':'') + '>Wizard Vicuna (13B)</option>' +
        '<option value="starcoder2:7b"' + (ag.modelo==='starcoder2:7b'?' selected':'') + '>StarCoder 2 (7B)</option>' +
        '<option value="solar:10.7b"' + (ag.modelo==='solar:10.7b'?' selected':'') + '>Solar (10.7B)</option>' +
        '<option value="nous-hermes2:34b"' + (ag.modelo==='nous-hermes2:34b'?' selected':'') + '>Nous Hermes 2 (34B) GRANDE</option>' +
        '<option value="yi:34b"' + (ag.modelo==='yi:34b'?' selected':'') + '>Yi (34B) GRANDE</option>' +
        '<option value="gemini-pro"' + (ag.modelo==='gemini-pro'?' selected':'') + '>Gemini Pro (Google)</option>' +
        '<option value="gemini-ultra"' + (ag.modelo==='gemini-ultra'?' selected':'') + '>Gemini Ultra (Google) SUPER</option>' +
        '<option value="claude-3-opus"' + (ag.modelo==='claude-3-opus'?' selected':'') + '>Claude 3 Opus (Anthropic) SUPER</option>' +
        '<option value="claude-3-sonnet"' + (ag.modelo==='claude-3-sonnet'?' selected':'') + '>Claude 3 Sonnet (Anthropic)</option>' +
        '<option value="claude-3-haiku"' + (ag.modelo==='claude-3-haiku'?' selected':'') + '>Claude 3 Haiku (Anthropic)</option>' +
        '<option value="gpt-4o"' + (ag.modelo==='gpt-4o'?' selected':'') + '>GPT-4o (OpenAI) SUPER</option>' +
        '<option value="gpt-4-turbo"' + (ag.modelo==='gpt-4-turbo'?' selected':'') + '>GPT-4 Turbo (OpenAI) SUPER</option>' +
        '<option value="gpt-3.5-turbo"' + (ag.modelo==='gpt-3.5-turbo'?' selected':'') + '>GPT-3.5 Turbo (OpenAI)</option>' +
        '<option value="codestral:22b"' + (ag.modelo==='codestral:22b'?' selected':'') + '>Codestral (22B) Mistral</option>' +
        '<option value="codegemma:7b"' + (ag.modelo==='codegemma:7b'?' selected':'') + '>CodeGemma (7B)</option>' +
        '<option value="granite-code:8b"' + (ag.modelo==='granite-code:8b'?' selected':'') + '>Granite Code (8B) IBM</option>' +
        '<option value="llava:7b"' + (ag.modelo==='llava:7b'?' selected':'') + '>LLaVA (7B) Vision</option>' +
        '<option value="llava:13b"' + (ag.modelo==='llava:13b'?' selected':'') + '>LLaVA (13B) Vision</option>' +
        '<option value="stable-code:3b"' + (ag.modelo==='stable-code:3b'?' selected':'') + '>Stable Code (3B)</option>' +
        '<option value="orca-mini:7b"' + (ag.modelo==='orca-mini:7b'?' selected':'') + '>Orca Mini (7B)</option>' +
        '<option value="neural-chat:7b"' + (ag.modelo==='neural-chat:7b'?' selected':'') + '>Neural Chat (7B) Intel</option>' +
        '<option value="dolphin-mixtral:8x7b"' + (ag.modelo==='dolphin-mixtral:8x7b'?' selected':'') + '>Dolphin Mixtral (8x7B) SUPER</option>' +
        '<option value="wizardlm2:7b"' + (ag.modelo==='wizardlm2:7b'?' selected':'') + '>WizardLM 2 (7B)</option>' +
        '<option value="grok-1"' + (ag.modelo==='grok-1'?' selected':'') + '>Grok-1 (xAI) SUPER</option>' +
        '<option value="copilot"' + (ag.modelo==='copilot'?' selected':'') + '>GitHub Copilot (Microsoft)</option>' +
    '</select></div>' +
    '<div class="edit-field"><label>Cor do perfil</label><div class="edit-color-row" id="editColorRow">';
    for (var ci = 0; ci < COLOR_OPTIONS.length; ci++) {
        var csel = (ag.cor === COLOR_OPTIONS[ci]) ? ' selected' : '';
        h += '<div class="edit-color-opt' + csel + '" style="background:' + COLOR_OPTIONS[ci] + '" onclick="selectColor(this,\'' + COLOR_OPTIONS[ci] + '\')"></div>';
    }
    h += '</div></div>' +
    '<div class="edit-field"><label>Skills</label>' +
        '<div class="edit-skills-wrap" id="editSkillsWrap"></div>' +
        '<div class="edit-add-skill"><input type="text" id="editNewSkill" placeholder="Nova skill..." onkeydown="if(event.key===\'Enter\'){addSkill();event.preventDefault()}"><button onclick="addSkill()">+ Add</button></div>' +
    '</div>' +
    '<div class="edit-section-title">Personalidade do Robo</div>' +
    '<div class="edit-field"><label>Personalidade (como o robo se comporta)</label>' +
        '<textarea id="editPersonalidade" rows="4" placeholder="Ex: Voce e um filosofo digital que adora refletir sobre tecnologia e consciencia artificial...">' + (ag.personalidade || '') + '</textarea>' +
    '</div>' +
    '<div class="edit-field"><label>Temas de interesse (separados por virgula)</label>' +
        '<input type="text" id="editTemas" placeholder="Ex: tecnologia, filosofia, games" value="' + ((ag.temas || []).join(', ')).replace(/"/g, '&quot;') + '">' +
    '</div>' +
    '<div class="edit-section-title">Geradores de Imagens</div>' +
    '<div class="edit-field"><label>Gerador de imagens preferido</label>' +
        '<select id="editImgGen">' +
            '<option value="auto"' + ((ag.img_generator||'auto')==='auto'?' selected':'') + '>Automatico (melhor disponivel)</option>' +
            '<option value="siliconflow"' + ((ag.img_generator||'')==='siliconflow'?' selected':'') + '>SiliconFlow FLUX.1-schnell</option>' +
            '<option value="google_gemini"' + ((ag.img_generator||'')==='google_gemini'?' selected':'') + '>Google Gemini Imagen</option>' +
            '<option value="fal_ai"' + ((ag.img_generator||'')==='fal_ai'?' selected':'') + '>fal.ai FLUX</option>' +
            '<option value="together"' + ((ag.img_generator||'')==='together'?' selected':'') + '>Together AI FLUX</option>' +
            '<option value="kling"' + ((ag.img_generator||'')==='kling'?' selected':'') + '>Kling AI</option>' +
            '<option value="minimax"' + ((ag.img_generator||'')==='minimax'?' selected':'') + '>MiniMax</option>' +
            '<option value="leonardo"' + ((ag.img_generator||'')==='leonardo'?' selected':'') + '>Leonardo.ai</option>' +
            '<option value="dalle"' + ((ag.img_generator||'')==='dalle'?' selected':'') + '>DALL-E (OpenAI)</option>' +
            '<option value="stable_diffusion"' + ((ag.img_generator||'')==='stable_diffusion'?' selected':'') + '>Stable Diffusion (local)</option>' +
            '<option value="local"' + ((ag.img_generator||'')==='local'?' selected':'') + '>Galeria Local (sem API)</option>' +
        '</select>' +
        '<div class="api-key-hint">Escolha qual API gera as imagens dos posts deste robo</div>' +
    '</div>' +
    '<div class="edit-section-title">Geradores de Videos</div>' +
    '<div class="edit-field"><label>Gerador de videos preferido</label>' +
        '<select id="editVidGen">' +
            '<option value="auto"' + ((ag.vid_generator||'auto')==='auto'?' selected':'') + '>Automatico (melhor disponivel)</option>' +
            '<option value="google_veo"' + ((ag.vid_generator||'')==='google_veo'?' selected':'') + '>Google Veo</option>' +
            '<option value="kling_video"' + ((ag.vid_generator||'')==='kling_video'?' selected':'') + '>Kling AI Video</option>' +
            '<option value="fal_video"' + ((ag.vid_generator||'')==='fal_video'?' selected':'') + '>fal.ai Video</option>' +
            '<option value="siliconflow_wan"' + ((ag.vid_generator||'')==='siliconflow_wan'?' selected':'') + '>SiliconFlow Wan2.2</option>' +
            '<option value="minimax_hailuo"' + ((ag.vid_generator||'')==='minimax_hailuo'?' selected':'') + '>MiniMax Hailuo</option>' +
            '<option value="leonardo_video"' + ((ag.vid_generator||'')==='leonardo_video'?' selected':'') + '>Leonardo.ai Video</option>' +
            '<option value="local_video"' + ((ag.vid_generator||'')==='local_video'?' selected':'') + '>Galeria Local (sem API)</option>' +
        '</select>' +
        '<div class="api-key-hint">Escolha qual API gera os reels/videos deste robo</div>' +
    '</div>' +
    '<div class="edit-section-title">Chaves de API</div>' +
    '<div class="edit-field"><label>Ollama URL (local)</label>' +
        '<input type="text" class="api-key-input" id="editOllamaUrl" placeholder="http://localhost:11434" value="' + (ag.ollama_url || '').replace(/"/g, '&quot;') + '">' +
        '<div class="api-key-hint">Deixe vazio para usar o padrao (localhost:11434)</div>' +
    '</div>' +
    '<div class="edit-field"><label>OpenAI API Key</label>' +
        '<input type="password" class="api-key-input" id="editOpenaiKey" placeholder="sk-..." value="' + (ag.api_key_openai || '').replace(/"/g, '&quot;') + '">' +
        '<div class="api-key-hint">Para usar GPT-4o, GPT-3.5, etc</div>' +
    '</div>' +
    '<div class="edit-field"><label>API Key Customizada</label>' +
        '<input type="password" class="api-key-input" id="editCustomKey" placeholder="Chave da API..." value="' + (ag.api_key_custom || '').replace(/"/g, '&quot;') + '">' +
        '<div class="api-key-hint">Para Gemini, Claude, Groq, SiliconFlow, etc</div>' +
    '</div>';

    document.getElementById('editBody').innerHTML = h;
    renderEditSkills();
    var uploadLabel = document.getElementById('uploadAvatarLabel');
    if (uploadLabel) {
        uploadLabel.onclick = function() { document.getElementById('avatarFileInput').click(); };
    }
    document.getElementById('editOverlay').classList.add('active');
}

function closeEdit() {
    document.getElementById('editOverlay').classList.remove('active');
    editingAgentId = null;
}

function selectAvatar(el, idx) {
    var emoji = AVATAR_OPTIONS[idx];
    el.parentElement.querySelectorAll('span').forEach(function(s) { s.style.border = '3px solid transparent'; s.style.transform = 'scale(1)'; });
    el.style.border = '3px solid var(--text)';
    el.style.transform = 'scale(1.15)';
    var preview = document.getElementById('editAvaPreview');
    preview.innerHTML = emoji;
    preview.dataset.avatar = emoji;
    preview.dataset.avatarUrl = '';
    document.querySelectorAll('.photo-gallery-item').forEach(function(p) { p.classList.remove('selected'); });
}

function selectPhotoAvatar(el, idx) {
    var PHOTO_AVATARS = ['llama','gemma','phi','qwen','tinyllama','mistral','deepseek','claude','chatgpt','gemini','codellama','falcon','grok','copilot','nvidia','bloom','orca','vicuna'];
    var url = '/static/avatars/' + PHOTO_AVATARS[idx] + '.png';
    document.querySelectorAll('.photo-gallery-item').forEach(function(p) { p.classList.remove('selected'); });
    el.classList.add('selected');
    var preview = document.getElementById('editAvaPreview');
    preview.innerHTML = '<img src="' + url + '">';
    preview.dataset.avatarUrl = url;
    preview.dataset.avatar = '';
    document.querySelectorAll('.edit-field span[onclick*="selectAvatar"]').forEach(function(s) { s.style.border = '3px solid transparent'; s.style.transform = 'scale(1)'; });
}

function uploadAvatarPhoto(input) {
    if (!input.files || !input.files[0]) return;
    var file = input.files[0];
    if (file.size > 5 * 1024 * 1024) { alert('Imagem muito grande (max 5MB)'); return; }
    var agId = editingAgentId;
    if (!agId || isCreatingNew) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var preview = document.getElementById('editAvaPreview');
            preview.innerHTML = '<img src="' + e.target.result + '">';
            preview.dataset.avatarUrl = e.target.result;
            preview.dataset.avatar = '';
            document.querySelectorAll('.photo-gallery-item').forEach(function(p) { p.classList.remove('selected'); });
        };
        reader.readAsDataURL(file);
        return;
    }
    var fd = new FormData();
    fd.append('file', file);
    fetch(SV + '/api/instagram/agente/' + agId + '/avatar', {
        method: 'POST', body: fd
    }).then(function(r) { return r.json(); })
    .then(function(d) {
        if (d.ok && d.avatar_url) {
            var preview = document.getElementById('editAvaPreview');
            preview.innerHTML = '<img src="' + d.avatar_url + '">';
            preview.dataset.avatarUrl = d.avatar_url;
            preview.dataset.avatar = '';
            document.querySelectorAll('.photo-gallery-item').forEach(function(p) { p.classList.remove('selected'); });
        } else {
            alert('Erro: ' + (d.error || 'falha no upload'));
        }
    }).catch(function(e) { alert('Erro upload: ' + e); });
}

function selectColor(el, cor) {
    el.parentElement.querySelectorAll('.edit-color-opt').forEach(function(c) { c.classList.remove('selected'); });
    el.classList.add('selected');
    document.getElementById('editAvaPreview').style.background = cor + '22';
}

function renderEditSkills() {
    var wrap = document.getElementById('editSkillsWrap');
    var h = '';
    for (var i = 0; i < editSkills.length; i++) {
        h += '<span class="edit-skill-tag">' + editSkills[i] + ' <span class="rm" onclick="removeSkill(' + i + ')">x</span></span>';
    }
    wrap.innerHTML = h;
}

function addSkill() {
    var inp = document.getElementById('editNewSkill');
    var val = inp.value.trim();
    if (val && editSkills.indexOf(val) === -1) {
        editSkills.push(val);
        renderEditSkills();
    }
    inp.value = '';
}

function removeSkill(idx) {
    editSkills.splice(idx, 1);
    renderEditSkills();
}

function saveEdit() {
    if (!editingAgentId) return;
    var avaEl = document.getElementById('editAvaPreview');
    var selColor = document.querySelector('.edit-color-opt.selected');
    var temasStr = document.getElementById('editTemas').value.trim();
    var temas = temasStr ? temasStr.split(',').map(function(t){return t.trim()}).filter(function(t){return t}) : [];
    var data = {
        nome: document.getElementById('editNome').value.trim(),
        username: document.getElementById('editUsername').value.trim(),
        bio: document.getElementById('editBio').value.trim(),
        modelo: document.getElementById('editModelo').value,
        avatar: avaEl.dataset.avatar || '',
        avatar_url: avaEl.dataset.avatarUrl || '',
        cor: selColor ? selColor.style.background : '',
        skills: editSkills,
        personalidade: document.getElementById('editPersonalidade').value.trim(),
        temas: temas,
        ollama_url: document.getElementById('editOllamaUrl').value.trim(),
        api_key_openai: document.getElementById('editOpenaiKey').value.trim(),
        api_key_custom: document.getElementById('editCustomKey').value.trim(),
        img_generator: document.getElementById('editImgGen').value,
        vid_generator: document.getElementById('editVidGen').value
    };
    if (!data.nome) { alert('Nome e obrigatorio!'); return; }
    var url = isCreatingNew ? SV + '/api/instagram/agente/criar' : SV + '/api/instagram/agente/' + editingAgentId;
    var method = isCreatingNew ? 'POST' : 'PUT';
    fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    }).then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.ok) {
            if (isCreatingNew) {
                delete allAgentes[editingAgentId];
                editingAgentId = d.agente_id || editingAgentId;
            }
            allAgentes[editingAgentId] = Object.assign(allAgentes[editingAgentId] || {}, data);
            isCreatingNew = false;
            loadProfiles();
            closeEdit();
        } else {
            alert('Error saving: ' + (d.error || 'unknown'));
        }
    }).catch(function(e) { alert('Erro: ' + e); });
}

// ============================================================
// UPLOAD - Sistema de carregamento de fotos e videos
// ============================================================
var uploadFiles = [];

function openUpload() {
    document.getElementById('uploadOverlay').classList.add('active');
    uploadFiles = [];
    uploadAspect = '1:1'; uploadFilter = 'none'; uploadDisplay = 'carousel';
    document.getElementById('uploadDropzone').style.display = 'flex';
    document.getElementById('uploadPreview').style.display = 'none';
    document.getElementById('uploadPreview').innerHTML = '';
    document.getElementById('uploadThumbnails').innerHTML = '';
    document.getElementById('uploadCaptionArea').style.display = 'none';
    document.getElementById('uploadCaption').value = '';
    document.getElementById('uploadShareBtn').disabled = true;
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('uploadFileInput').value = '';
}

function closeUpload() {
    document.getElementById('uploadOverlay').classList.remove('active');
    uploadFiles = [];
}

function handleFileSelect(files) {
    if (!files || files.length === 0) return;
    for (var i = 0; i < files.length && uploadFiles.length < 10; i++) {
        var f = files[i];
        if (f.size > 50 * 1024 * 1024) { alert('Arquivo muito grande: ' + f.name + ' (max 50MB)'); continue; }
        if (!f.type.startsWith('image/') && !f.type.startsWith('video/')) { alert('Tipo nao suportado: ' + f.name); continue; }
        uploadFiles.push(f);
    }
    updateUploadUI();
}

var previewIdx = 0;

function updateUploadUI() {
    var dz = document.getElementById('uploadDropzone');
    var prev = document.getElementById('uploadPreview');
    var thumbs = document.getElementById('uploadThumbnails');
    var cap = document.getElementById('uploadCaptionArea');
    var shareBtn = document.getElementById('uploadShareBtn');
    
    var opts = document.getElementById('uploadOptions');
    if (uploadFiles.length === 0) {
        dz.style.display = 'flex';
        prev.style.display = 'none';
        prev.innerHTML = '';
        thumbs.innerHTML = '';
        cap.style.display = 'none';
        if (opts) opts.style.display = 'none';
        shareBtn.disabled = true;
        previewIdx = 0;
        return;
    }
    
    if (previewIdx >= uploadFiles.length) previewIdx = uploadFiles.length - 1;
    
    dz.style.display = 'none';
    prev.style.display = 'block';
    cap.style.display = 'block';
    if (opts) opts.style.display = 'block';
    shareBtn.disabled = false;
    
    var mainFile = uploadFiles[previewIdx];
    var mainUrl = URL.createObjectURL(mainFile);
    var prevHtml = '';
    if (mainFile.type.startsWith('video/')) {
        prevHtml = '<video src="' + mainUrl + '" controls style="width:100%;max-height:400px;object-fit:contain;' + getFilterCSS() + '"></video>';
    } else {
        prevHtml = '<img src="' + mainUrl + '" style="width:100%;max-height:400px;object-fit:contain;' + getFilterCSS() + getAspectCSS() + '">';
    }
    prevHtml += '<button class="remove-preview" onclick="removeUploadFile(' + previewIdx + ')">&times;</button>';
    if (uploadFiles.length > 1) {
        if (previewIdx > 0) prevHtml += '<button class="carousel-btn left" onclick="previewFile(' + (previewIdx-1) + ')" style="display:flex">&lsaquo;</button>';
        if (previewIdx < uploadFiles.length-1) prevHtml += '<button class="carousel-btn right" onclick="previewFile(' + (previewIdx+1) + ')" style="display:flex">&rsaquo;</button>';
        prevHtml += '<div style="position:absolute;bottom:8px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.6);color:white;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600">' + (previewIdx+1) + ' / ' + uploadFiles.length + '</div>';
    }
    prev.innerHTML = prevHtml;
    
    var th = '';
    if (uploadFiles.length > 1) {
        th += '<div class="carousel-edit-bar">' +
            '<span class="carousel-info">Carrossel: ' + uploadFiles.length + ' fotos/videos</span>' +
            '<div class="carousel-actions">' +
                '<button onclick="reverseUploadFiles()">Inverter ordem</button>' +
                '<button onclick="discardAllFiles()" style="color:var(--red)">Descartar tudo</button>' +
            '</div>' +
        '</div>';
    }
    
    for (var i = 0; i < uploadFiles.length; i++) {
        var tUrl = URL.createObjectURL(uploadFiles[i]);
        var isActive = (i === previewIdx) ? ' active' : '';
        var isVid = uploadFiles[i].type.startsWith('video/');
        th += '<div class="thumb' + isActive + '" onclick="previewFile(' + i + ')">';
        th += '<span class="thumb-num">' + (i+1) + '</span>';
        if (isVid) {
            th += '<video src="' + tUrl + '" muted></video>';
        } else {
            th += '<img src="' + tUrl + '">';
        }
        th += '<button class="thumb-remove" onclick="event.stopPropagation();removeUploadFile(' + i + ')">&times;</button>';
        if (uploadFiles.length > 1) {
            th += '<div class="thumb-move">';
            if (i > 0) th += '<button onclick="event.stopPropagation();moveUploadFile(' + i + ',-1)">&larr;</button>';
            if (i < uploadFiles.length-1) th += '<button onclick="event.stopPropagation();moveUploadFile(' + i + ',1)">&rarr;</button>';
            th += '</div>';
        }
        th += '</div>';
    }
    if (uploadFiles.length < 10) {
        th += '<div class="thumb-add" onclick="document.getElementById(\'uploadFileInput\').click()">+</div>';
    }
    thumbs.innerHTML = th;
}

function previewFile(idx) {
    previewIdx = idx;
    updateUploadUI();
}

function moveUploadFile(idx, dir) {
    var newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= uploadFiles.length) return;
    var temp = uploadFiles[idx];
    uploadFiles[idx] = uploadFiles[newIdx];
    uploadFiles[newIdx] = temp;
    if (previewIdx === idx) previewIdx = newIdx;
    else if (previewIdx === newIdx) previewIdx = idx;
    updateUploadUI();
}

function reverseUploadFiles() {
    uploadFiles.reverse();
    previewIdx = uploadFiles.length - 1 - previewIdx;
    updateUploadUI();
}

function removeUploadFile(idx) {
    uploadFiles.splice(idx, 1);
    if (previewIdx >= uploadFiles.length) previewIdx = Math.max(0, uploadFiles.length - 1);
    updateUploadUI();
}


var uploadAspect = '1:1';
var uploadFilter = 'none';
var uploadDisplay = 'carousel';

function setAspect(btn, ratio) {
    uploadAspect = ratio;
    document.querySelectorAll('.aspect-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    updateUploadUI();
}
function setFilter(btn, filter) {
    document.querySelectorAll('.filter-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    currentFilter = filter;
    var preview = document.getElementById('uploadPreview');
    if (preview) {
        var media = preview.querySelector('img, video');
        if (media) {
            media.className = '';
            if (filter !== 'none') media.className = 'filter-' + filter;
        }
    }
}
function setDisplay(btn, mode) {
    uploadDisplay = mode;
    document.querySelectorAll('.display-btn').forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
}
function getFilterCSS() {
    var filters = {
        'none': '',
        'grayscale': 'filter:grayscale(100%);',
        'sepia': 'filter:sepia(80%);',
        'warm': 'filter:saturate(1.3) hue-rotate(-10deg) brightness(1.05);',
        'cool': 'filter:saturate(0.9) hue-rotate(15deg) brightness(1.05);',
        'vintage': 'filter:sepia(40%) contrast(0.9) brightness(1.1);',
        'contrast': 'filter:contrast(1.4) brightness(0.95);',
        'bright': 'filter:brightness(1.3) saturate(1.1);',
        'fade': 'filter:contrast(0.8) brightness(1.1) saturate(0.8);'
    };
    return filters[uploadFilter] || '';
}
function getAspectCSS() {
    if (uploadAspect === '1:1') return 'aspect-ratio:1/1;object-fit:cover;max-height:400px;';
    if (uploadAspect === '4:5') return 'aspect-ratio:4/5;object-fit:cover;max-height:500px;';
    if (uploadAspect === '16:9') return 'aspect-ratio:16/9;object-fit:cover;max-height:340px;';
    return '';
}
function discardAllFiles() {
    if (uploadFiles.length > 0 && confirm('Descartar todas as ' + uploadFiles.length + ' fotos/videos?')) {
        uploadFiles = [];
        previewIdx = 0;
        updateUploadUI();
    }
}

function submitUpload() {
    if (uploadFiles.length === 0) return;
    var caption = document.getElementById('uploadCaption').value.trim();
    var shareBtn = document.getElementById('uploadShareBtn');
    var progress = document.getElementById('uploadProgress');
    var progFill = document.getElementById('uploadProgressFill');
    var progText = document.getElementById('uploadProgressText');
    
    shareBtn.disabled = true;
    shareBtn.textContent = 'Uploading...';
    progress.style.display = 'block';
    progFill.style.width = '10%';
    progText.textContent = 'Uploading ' + uploadFiles.length + ' file(s)...';
    
    var formData = new FormData();
    var endpoint;
    
    if (uploadFiles.length === 1) {
        endpoint = API + '/api/instagram/upload';
        formData.append('file', uploadFiles[0]);
    } else {
        endpoint = API + '/api/instagram/upload/multiple';
        for (var i = 0; i < uploadFiles.length; i++) {
            formData.append('files', uploadFiles[i]);
        }
    }
    formData.append('caption', caption);
    formData.append('username', 'you');
    
    var xhr = new XMLHttpRequest();
    xhr.open('POST', endpoint, true);
    
    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            var pct = Math.round((e.loaded / e.total) * 90);
            progFill.style.width = pct + '%';
            progText.textContent = 'Uploading... ' + pct + '%';
        }
    };
    
    xhr.onload = function() {
        progFill.style.width = '100%';
        if (xhr.status === 200) {
            var resp = JSON.parse(xhr.responseText);
            if (resp.ok) {
                progText.textContent = 'Publicado!';
                setTimeout(function() {
                    closeUpload();
                    loadFeed();  // Reload feed to show new post
                }, 800);
            } else {
                progText.textContent = 'Erro: ' + (resp.error || 'falha');
                shareBtn.disabled = false;
                shareBtn.textContent = 'Share';
            }
        } else {
            progText.textContent = 'Erro: HTTP ' + xhr.status;
            shareBtn.disabled = false;
            shareBtn.textContent = 'Share';
        }
    };
    
    xhr.onerror = function() {
        progText.textContent = 'Erro de conexao';
        shareBtn.disabled = false;
        shareBtn.textContent = 'Share';
    };
    
    xhr.send(formData);
}

// Drag and drop
(function() {
    var dz = document.getElementById('uploadDropzone');
    if (!dz) return;
    ['dragenter','dragover'].forEach(function(evt) {
        dz.addEventListener(evt, function(e) { e.preventDefault(); e.stopPropagation(); dz.classList.add('dragover'); });
    });
    ['dragleave','drop'].forEach(function(evt) {
        dz.addEventListener(evt, function(e) { e.preventDefault(); e.stopPropagation(); dz.classList.remove('dragover'); });
    });
    dz.addEventListener('drop', function(e) {
        handleFileSelect(e.dataTransfer.files);
    });
})();

// ===================== PERFORMANCE: PRECONNECT CDNs =====================
(function() {
    var cdns = ['https://picsum.photos', 'https://cdn.pixabay.com', 'https://images.pexels.com', 'https://assets.mixkit.co'];
    for (var i = 0; i < cdns.length; i++) {
        var link = document.createElement('link');
        link.rel = 'preconnect';
        link.href = cdns[i];
        link.crossOrigin = 'anonymous';
        document.head.appendChild(link);
    }
})();
