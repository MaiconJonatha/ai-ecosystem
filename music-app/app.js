// =====================
// DATA
// =====================
const SONGS = [
  { id:1, title:'Blinding Lights', artist:'The Weeknd', album:'After Hours', duration:'3:20', emoji:'🌟', color:'#ff6b35' },
  { id:2, title:'Levitating', artist:'Dua Lipa', album:'Future Nostalgia', duration:'3:23', emoji:'💫', color:'#9b59b6' },
  { id:3, title:'Stay', artist:'The Kid Laroi & Justin Bieber', album:'F*CK LOVE 3', duration:'2:21', emoji:'💙', color:'#3498db' },
  { id:4, title:'Peaches', artist:'Justin Bieber', album:'Justice', duration:'3:18', emoji:'🍑', color:'#e67e22' },
  { id:5, title:'Good 4 U', artist:'Olivia Rodrigo', album:'SOUR', duration:'2:58', emoji:'💚', color:'#27ae60' },
  { id:6, title:'drivers license', artist:'Olivia Rodrigo', album:'SOUR', duration:'4:02', emoji:'🚗', color:'#e74c3c' },
  { id:7, title:'Montero', artist:'Lil Nas X', album:'MONTERO', duration:'2:17', emoji:'🔥', color:'#c0392b' },
  { id:8, title:'Permission To Dance', artist:'BTS', album:'Butter', duration:'3:17', emoji:'🎵', color:'#1abc9c' },
  { id:9, title:'Heat Waves', artist:'Glass Animals', album:'Dreamland', duration:'3:59', emoji:'🌊', color:'#2980b9' },
  { id:10, title:'Watermelon Sugar', artist:'Harry Styles', album:'Fine Line', duration:'2:54', emoji:'🍉', color:'#e74c3c' },
  { id:11, title:'Save Your Tears', artist:'The Weeknd', album:'After Hours', duration:'3:35', emoji:'😢', color:'#8e44ad' },
  { id:12, title:'Industry Baby', artist:'Lil Nas X & Jack Harlow', album:'MONTERO', duration:'3:32', emoji:'🏭', color:'#f39c12' },
  { id:13, title:'Cold Heart', artist:'Elton John & Dua Lipa', album:'The Lockdown Sessions', duration:'3:22', emoji:'❄️', color:'#2c3e50' },
  { id:14, title:'Bad Habits', artist:'Ed Sheeran', album:'=', duration:'3:51', emoji:'😈', color:'#d35400' },
  { id:15, title:'Easy on Me', artist:'Adele', album:'30', duration:'3:44', emoji:'🎶', color:'#7f8c8d' },
  { id:16, title:'Shivers', artist:'Ed Sheeran', album:'=', duration:'3:27', emoji:'🌙', color:'#16a085' },
  { id:17, title:'Ghost', artist:'Justin Bieber', album:'Justice', duration:'2:33', emoji:'👻', color:'#95a5a6' },
  { id:18, title:'happier than ever', artist:'Billie Eilish', album:'Happier Than Ever', duration:'4:58', emoji:'🌺', color:'#8e44ad' },
  { id:19, title:'Butter', artist:'BTS', album:'Butter', duration:'2:42', emoji:'🧈', color:'#f1c40f' },
  { id:20, title:'Solar Power', artist:'Lorde', album:'Solar Power', duration:'3:54', emoji:'☀️', color:'#27ae60' },
];

const PLAYLISTS = [
  { name:'🔥 Top Hits 2024', songs:[0,1,2,3,4,5], description:'Os maiores hits do momento' },
  { name:'🌙 Lo-Fi Night', songs:[6,7,8,9,10], description:'Relaxe com sons suaves' },
  { name:'⚡ Energia Total', songs:[11,12,13,14,15], description:'Máxima energia para seu treino' },
  { name:'🎸 Rock Clássico', songs:[16,17,18,4,5], description:'Clássicos atemporais' },
  { name:'💜 R&B Vibes', songs:[19,0,3,1,7], description:'O melhor do R&B e Soul' },
];

const CATEGORIES = [
  { name:'Pop', emoji:'⭐', color:'linear-gradient(135deg,#ee0979,#ff6a00)' },
  { name:'Hip-Hop', emoji:'🎤', color:'linear-gradient(135deg,#373B44,#4286f4)' },
  { name:'Eletrônico', emoji:'🎧', color:'linear-gradient(135deg,#00c6ff,#0072ff)' },
  { name:'Rock', emoji:'🎸', color:'linear-gradient(135deg,#f7971e,#ffd200)' },
  { name:'R&B / Soul', emoji:'💜', color:'linear-gradient(135deg,#a18cd1,#fbc2eb)' },
  { name:'Lo-Fi', emoji:'🌙', color:'linear-gradient(135deg,#3d7eaa,#ffe47a)' },
  { name:'Sertanejo', emoji:'🤠', color:'linear-gradient(135deg,#d4a017,#8b4513)' },
  { name:'Latin', emoji:'🌶️', color:'linear-gradient(135deg,#f953c6,#b91d73)' },
  { name:'Jazz', emoji:'🎷', color:'linear-gradient(135deg,#434343,#000000)' },
  { name:'Funk', emoji:'🔊', color:'linear-gradient(135deg,#fc4a1a,#f7b733)' },
];

// =====================
// STATE
// =====================
let currentTrackIdx = -1;
let isPlaying = false;
let isShuffle = false;
let isRepeat = false;
let isLiked = false;
let currentPlaylist = null;
let playQueue = [];
let fakeTimer = null;
let fakeProgress = 0;
let fakeDuration = 200;

// =====================
// INIT
// =====================
document.addEventListener('DOMContentLoaded', () => {
  renderQuickPicks();
  renderFeaturedCards();
  renderRecentCards();
  renderCategories();
  renderLibrary();
});

// =====================
// RENDER FUNCTIONS
// =====================
function renderQuickPicks() {
  const container = document.getElementById('quickPicks');
  const picks = SONGS.slice(0, 6);
  container.innerHTML = picks.map((s, i) => `
    <div class="quick-card" onclick="playSong(${i})" id="qcard-${i}">
      <div class="quick-thumb" style="background:${s.color}20;">${s.emoji}</div>
      <div class="quick-name">${s.title}</div>
      <button class="quick-play" onclick="event.stopPropagation();playSong(${i})">
        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      </button>
    </div>
  `).join('');
}

function renderFeaturedCards() {
  const container = document.getElementById('featuredCards');
  const featured = SONGS.slice(6, 14);
  container.innerHTML = featured.map((s, i) => `
    <div class="music-card" onclick="playSong(${i+6})" id="fcard-${i+6}">
      <div class="card-art" style="background:${s.color}25;">
        <span>${s.emoji}</span>
        <button class="card-play" onclick="event.stopPropagation();playSong(${i+6})">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>
      </div>
      <div class="card-title">${s.title}</div>
      <div class="card-sub">${s.artist}</div>
    </div>
  `).join('');
}

function renderRecentCards() {
  const container = document.getElementById('recentCards');
  const recent = SONGS.slice(14, 20);
  container.innerHTML = recent.map((s, i) => `
    <div class="music-card" onclick="playSong(${i+14})">
      <div class="card-art" style="background:${s.color}25;">
        <span>${s.emoji}</span>
        <button class="card-play" onclick="event.stopPropagation();playSong(${i+14})">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>
      </div>
      <div class="card-title">${s.title}</div>
      <div class="card-sub">${s.artist}</div>
    </div>
  `).join('');
}

function renderCategories() {
  const container = document.getElementById('categoriesGrid');
  container.innerHTML = CATEGORIES.map(c => `
    <div class="category-card" style="background:${c.color}" onclick="filterByCategory('${c.name}')">
      <span>${c.name}</span>
      <span class="category-emoji">${c.emoji}</span>
    </div>
  `).join('');
}

function renderLibrary() {
  const container = document.getElementById('libraryList');
  container.innerHTML = PLAYLISTS.map((p, i) => `
    <div class="library-item" onclick="loadPlaylist(${i})">
      <div class="library-thumb" style="background:${SONGS[p.songs[0]].color}25">${p.name.split(' ')[0]}</div>
      <div class="library-info">
        <div class="library-name">${p.name}</div>
        <div class="library-sub">Playlist · ${p.songs.length} músicas</div>
      </div>
    </div>
  `).join('');
}

// =====================
// VIEWS
// =====================
function switchView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('view-' + name).classList.add('active');
  document.querySelector(`[data-view="${name}"]`).classList.add('active');
}

// =====================
// PLAY LOGIC
// =====================
function playSong(idx) {
  currentTrackIdx = idx;
  const song = SONGS[idx];
  if (!song) return;

  isLiked = false;
  updatePlayerUI(song);
  startFakePlay(song);
}

function updatePlayerUI(song) {
  // Bottom bar
  document.getElementById('playerThumb').textContent = song.emoji;
  document.getElementById('playerThumb').style.background = song.color + '30';
  document.getElementById('playerTrackName').textContent = song.title;
  document.getElementById('playerTrackArtist').textContent = song.artist;

  // Full panel
  document.getElementById('fullAlbumArt').textContent = song.emoji;
  document.getElementById('fullAlbumArt').style.background = song.color + '40';
  document.getElementById('fullTrackName').textContent = song.title;
  document.getElementById('fullTrackArtist').textContent = song.artist;

  // Duration
  const dur = parseDuration(song.duration);
  fakeDuration = dur;
  document.getElementById('totalTime').textContent = song.duration;
  document.getElementById('fullDuration').textContent = song.duration;

  // Liked
  updateLikeUI();
}

function parseDuration(str) {
  const parts = str.split(':');
  return parseInt(parts[0]) * 60 + parseInt(parts[1]);
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function startFakePlay(song) {
  clearFakeTimer();
  fakeProgress = 0;
  fakeDuration = parseDuration(song.duration);
  isPlaying = true;
  updatePlayButtons(true);
  runFakeTimer();
}

function runFakeTimer() {
  fakeTimer = setInterval(() => {
    if (!isPlaying) return;
    fakeProgress += 0.5;
    if (fakeProgress >= fakeDuration) {
      // Song ended
      if (isRepeat) {
        fakeProgress = 0;
      } else {
        nextTrack();
        return;
      }
    }
    const pct = (fakeProgress / fakeDuration) * 100;
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressThumb').style.left = pct + '%';
    document.getElementById('currentTime').textContent = formatTime(fakeProgress);
    document.getElementById('fullCurrentTime').textContent = formatTime(fakeProgress);

    const fpBar = document.getElementById('fullProgressBar');
    fpBar.value = pct;
  }, 500);
}

function clearFakeTimer() {
  if (fakeTimer) { clearInterval(fakeTimer); fakeTimer = null; }
}

function togglePlay() {
  if (currentTrackIdx < 0) { playSong(0); return; }
  isPlaying = !isPlaying;
  updatePlayButtons(isPlaying);
  if (isPlaying && !fakeTimer) runFakeTimer();
  if (!isPlaying) clearFakeTimer();
}

function updatePlayButtons(playing) {
  [document.getElementById('barPlayBtn'), document.getElementById('mainPlayBtn')].forEach(btn => {
    if (!btn) return;
    const pi = btn.querySelector('.play-icon');
    const pa = btn.querySelector('.pause-icon');
    if (playing) { if(pi) pi.style.display='none'; if(pa) pa.style.display=''; }
    else { if(pi) pi.style.display=''; if(pa) pa.style.display='none'; }
  });
}

function nextTrack() {
  let next;
  if (isShuffle) {
    next = Math.floor(Math.random() * SONGS.length);
  } else {
    next = (currentTrackIdx + 1) % SONGS.length;
  }
  playSong(next);
}

function prevTrack() {
  if (fakeProgress > 5) {
    fakeProgress = 0;
    return;
  }
  const prev = (currentTrackIdx - 1 + SONGS.length) % SONGS.length;
  playSong(prev);
}

function seekTo(val) {
  fakeProgress = (val / 100) * fakeDuration;
}

function seekFromBar(e) {
  const bar = document.getElementById('progressBar');
  const rect = bar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  fakeProgress = pct * fakeDuration;
  const fill = document.getElementById('progressFill');
  fill.style.width = (pct * 100) + '%';
}

function setVolume(val) {
  // Sync both sliders
  document.getElementById('volumeSlider').value = val;
  document.getElementById('barVolume').value = val;
}

function toggleShuffle() {
  isShuffle = !isShuffle;
  document.getElementById('shuffleBtn')?.classList.toggle('active', isShuffle);
}

function toggleRepeat() {
  isRepeat = !isRepeat;
  document.getElementById('repeatBtn')?.classList.toggle('active', isRepeat);
}

function toggleLike() {
  isLiked = !isLiked;
  updateLikeUI();
}

function updateLikeUI() {
  const likeBtn = document.getElementById('likeBtn');
  const playerLike = document.getElementById('playerLike');
  if (likeBtn) {
    likeBtn.textContent = isLiked ? '♥' : '♡';
    likeBtn.classList.toggle('liked', isLiked);
  }
  if (playerLike) {
    playerLike.textContent = isLiked ? '♥' : '♡';
    playerLike.classList.toggle('liked', isLiked);
  }
}

// =====================
// PANEL
// =====================
function openPanel() {
  const panel = document.getElementById('nowPlayingPanel');
  panel.style.display = 'flex';
  if (currentTrackIdx >= 0) {
    updatePlayerUI(SONGS[currentTrackIdx]);
  }
}

function closePanel() {
  document.getElementById('nowPlayingPanel').style.display = 'none';
}

// =====================
// SEARCH
// =====================
function searchSongs(query) {
  const resultsEl = document.getElementById('searchResults');
  const categoriesEl = document.getElementById('categoriesGrid');
  const titleEl = document.querySelector('#view-search .section-subtitle');

  if (!query.trim()) {
    resultsEl.style.display = 'none';
    categoriesEl.style.display = 'grid';
    if(titleEl) titleEl.style.display = '';
    return;
  }

  categoriesEl.style.display = 'none';
  if(titleEl) titleEl.style.display = 'none';
  resultsEl.style.display = 'block';

  const q = query.toLowerCase();
  const matches = SONGS.filter(s =>
    s.title.toLowerCase().includes(q) ||
    s.artist.toLowerCase().includes(q) ||
    s.album.toLowerCase().includes(q)
  );

  if (!matches.length) {
    resultsEl.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:40px;">Nenhum resultado para "${query}"</p>`;
    return;
  }

  resultsEl.innerHTML = `
    <h3 style="margin-bottom:16px;font-size:1rem;">Resultados para "${query}"</h3>
    ${matches.map((s, i) => {
      const idx = SONGS.indexOf(s);
      return `
        <div class="search-result-item" onclick="playSong(${idx})">
          <span class="result-num">${i + 1}</span>
          <div class="result-thumb" style="background:${s.color}30">${s.emoji}</div>
          <div class="result-info">
            <div class="result-title">${s.title}</div>
            <div class="result-artist">${s.artist}</div>
          </div>
          <span class="result-duration">${s.duration}</span>
        </div>
      `;
    }).join('')}
  `;
}

function filterByCategory(cat) {
  switchView('search');
  document.getElementById('searchInput').value = cat;
  searchSongs(cat);
}

// =====================
// PLAYLIST / MODAL
// =====================
function loadPlaylist(idx) {
  currentPlaylist = PLAYLISTS[idx];
  const songs = currentPlaylist.songs.map(si => SONGS[si]);

  document.getElementById('modalCover').textContent = currentPlaylist.name.split(' ')[0];
  document.getElementById('modalName').textContent = currentPlaylist.name;
  document.getElementById('modalMeta').textContent = `${songs.length} músicas · ${currentPlaylist.description}`;

  const list = document.getElementById('modalTrackList');
  list.innerHTML = songs.map((s, i) => `
    <li class="track-list-item ${currentTrackIdx === currentPlaylist.songs[i] ? 'playing' : ''}"
        onclick="playFromPlaylist(${idx}, ${i})">
      <span class="tl-num">${i + 1}</span>
      <div class="tl-thumb" style="background:${s.color}30">${s.emoji}</div>
      <div class="tl-info">
        <div class="tl-title">${s.title}</div>
        <div class="tl-artist">${s.artist}</div>
      </div>
      <span class="tl-duration">${s.duration}</span>
    </li>
  `).join('');

  document.getElementById('trackModal').style.display = 'flex';
}

function playFromPlaylist(pIdx, songIdx) {
  const playlist = PLAYLISTS[pIdx];
  const songGlobalIdx = playlist.songs[songIdx];
  playSong(songGlobalIdx);
  closeTrackModal();
}

function playAllInModal() {
  if (currentPlaylist) {
    playSong(currentPlaylist.songs[0]);
    closeTrackModal();
  }
}

function closeTrackModal() {
  document.getElementById('trackModal').style.display = 'none';
}

function showAddPlaylist() {
  const name = prompt('Nome da nova playlist:');
  if (name) {
    PLAYLISTS.push({ name: '🎵 ' + name, songs: [], description: 'Minha playlist' });
    renderLibrary();
  }
}

// Click outside modal to close
document.getElementById('trackModal')?.addEventListener('click', function(e) {
  if (e.target === this) closeTrackModal();
});

// =====================
// AI DJ ASSISTANT
// =====================

const AI_CHIPS = [
  '🔥 Músicas para animar', '😴 Algo para relaxar',
  '💪 Playlist de treino', '🌙 Lo-fi para estudar',
  '🎸 Rock clássico', '💜 R&B romântico',
  '🎵 O que está tocando agora?', '🤩 Recomendar por artista',
];

const AI_RESPONSES = {
  animar: { text: 'Aqui vão músicas para bombar seu dia! 🔥', songs: [11,12,2,4,8] },
  relaxar: { text: 'Perfeito para relaxar e descansar a cabeça 🌊', songs: [8,9,15,18,6] },
  treino: { text: 'Ativa o modo treino! Energia total 💪⚡', songs: [1,2,4,11,12] },
  estud: { text: 'Concentração máxima com Lo-fi e sons suaves 🎧📚', songs: [9,10,15,19,8] },
  lofi: { text: 'Lo-fi selecionado especialmente para você 🌙', songs: [9,10,15,19,8] },
  rock: { text: 'Clássicos do rock que nunca decepcionam 🎸', songs: [5,6,16,17,13] },
  rb: { text: 'R&B que toca fundo no coração 💜', songs: [3,7,10,18,0] },
  romantic: { text: 'Músicas para o momento especial 💕', songs: [3,10,15,17,7] },
  weekend: { text: 'Ah, o que está tocando agora é ', songs: [] },
  tocando: { text: 'Ah, o que está tocando agora é ', songs: [] },
  weeknd: { text: 'The Weeknd tem hits incríveis! Selecionei os melhores 🌟', songs: [0,10] },
  dua: { text: 'Dua Lipa é incrível! Confere essas:', songs: [1,12] },
  olivia: { text: 'Olivia Rodrigo, a rainha do pop indie!', songs: [4,5] },
  billie: { text: 'Billie Eilish com o estilo único dela:', songs: [17] },
  bts: { text: 'ARMY aqui? Os melhores do BTS:', songs: [7,18] },
  ed: { text: 'Ed Sheeran na veia 🎶', songs: [13,15] },
  adele: { text: 'Adele, a voz que emociona:', songs: [14] },
  justin: { text: 'Justin Bieber hits na ordem:', songs: [3,16] },
};

function getAIResponse(input) {
  const q = input.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  for (const key of Object.keys(AI_RESPONSES)) {
    if (q.includes(key)) {
      const resp = AI_RESPONSES[key];
      if (key === 'tocando' || key === 'weekend') {
        if (currentTrackIdx >= 0) {
          const s = SONGS[currentTrackIdx];
          return { text: `Agora tocando: **${s.title}** de ${s.artist} ${s.emoji}`, songs: [] };
        } else {
          return { text: 'Nenhuma música tocando no momento. Toque algo primeiro! 🎵', songs: [] };
        }
      }
      return resp;
    }
  }
  // Default
  const random5 = [...Array(20).keys()].sort(() => Math.random() - 0.5).slice(0, 5);
  return {
    text: `Não entendi exatamente, mas aqui vai uma seleção aleatória incrível para você! 🎲`,
    songs: random5
  };
}

function initAI() {
  // Render chips
  const chips = document.getElementById('suggestionChips');
  if (chips) {
    chips.innerHTML = AI_CHIPS.map(c =>
      `<button class="chip" onclick="chipClick('${c}')">${c}</button>`
    ).join('');
  }
  // Welcome message
  setTimeout(() => {
    addAIMessage(
      '👋 Olá! Sou o **SoundWave IA DJ** – seu assistente musical inteligente!\n\nPosso recomendar músicas por humor, artista ou estilo. Experimente perguntar algo! 🎵'
    );
  }, 400);
}

function chipClick(text) {
  document.getElementById('aiInput').value = text;
  sendAiMessage();
}

function sendAiMessage() {
  const input = document.getElementById('aiInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  // User message
  addUserMessage(text);

  // Typing indicator
  const typingId = addTyping();

  // AI response after delay
  setTimeout(() => {
    removeTyping(typingId);
    const resp = getAIResponse(text);
    addAIMessage(resp.text, resp.songs);
  }, 900 + Math.random() * 600);
}

function addUserMessage(text) {
  const msgs = document.getElementById('aiMessages');
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `
    <div class="msg-avatar">🎧</div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  msgs.appendChild(div);
  scrollMsgs();
}

function addAIMessage(text, songIdxs = []) {
  const msgs = document.getElementById('aiMessages');
  const div = document.createElement('div');
  div.className = 'msg ai';

  const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
  let songsHtml = '';
  if (songIdxs && songIdxs.length > 0) {
    songsHtml = `<div class="msg-songs">` +
      songIdxs.map(i => {
        const s = SONGS[i];
        return `
          <div class="msg-song-item" onclick="playSong(${i})">
            <div class="msg-song-thumb">${s.emoji}</div>
            <div class="msg-song-info">
              <div class="msg-song-title">${s.title}</div>
              <div class="msg-song-artist">${s.artist}</div>
            </div>
            <button class="msg-song-play" onclick="event.stopPropagation();playSong(${i})">
              <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            </button>
          </div>
        `;
      }).join('') +
    `</div>`;
  }

  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble">${formattedText}${songsHtml}</div>
  `;
  msgs.appendChild(div);
  scrollMsgs();
}

function addTyping() {
  const msgs = document.getElementById('aiMessages');
  const div = document.createElement('div');
  div.className = 'msg ai';
  const id = 'typing-' + Date.now();
  div.id = id;
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble typing-bubble">
      <div class="typing-dots">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  msgs.appendChild(div);
  scrollMsgs();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollMsgs() {
  const msgs = document.getElementById('aiMessages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Init AI when view opens
const origSwitchView = switchView;
window.switchView = function(name) {
  origSwitchView(name);
  if (name === 'ai') {
    const msgs = document.getElementById('aiMessages');
    if (msgs && msgs.children.length === 0) initAI();
  }
};
