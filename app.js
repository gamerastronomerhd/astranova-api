// ==========================================
// COMMANDER CONFIGURATION & STATE
// ==========================================
const HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': `Bearer ${SUPABASE_KEY}`,
    'Content-Type': 'application/json'
};

let masterFleet = []; 
let currentSkins = [];
let currentSkinIndex = 0;
let currentShipName = "";
let currentShipStats = {};

// Cached UI Elements (Performance Optimization)
const modal = document.getElementById('dossier-modal');
const closeModalBtn = document.getElementById('close-modal');
const historyToggle = document.getElementById('history-toggle');
const globalHistoryToggle = document.getElementById('global-history-toggle');
const viewGame = document.querySelector('.view-game');
const viewHistory = document.querySelector('.view-history');
const modalContainer = document.getElementById('modal-container');
const fleetCountDisplay = document.getElementById('fleet-count');
const grid = document.getElementById('fleet-grid');

// ==========================================
// UNIFIED RARITY DICTIONARY
// ==========================================
// This eliminates the massive if/else chains. It returns both the CSS class and the UI text.
function parseRarity(rarityString) {
    if (!rarityString) return { class: 'common', text: 'N' };
    const r = rarityString.toLowerCase();
    
    if (r.includes('decisive')) return { class: 'ur', text: 'DR' };
    if (r.includes('ultra')) return { class: 'ur', text: 'UR' };
    if (r.includes('priority')) return { class: 'ssr', text: 'PR' };
    if (r.includes('super')) return { class: 'ssr', text: 'SSR' };
    if (r.includes('elite')) return { class: 'elite', text: 'E' };
    if (r.includes('rare')) return { class: 'rare', text: 'R' };
    
    return { class: 'common', text: 'N' };
}

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    fetchFleetData();
    setupEventListeners();
});

async function fetchFleetData() {
    try {
        const response = await fetch(`${SUPABASE_URL}/rest/v1/ships?select=id,name,rarity,icon_url,painting_url,faction,hull_type,ship_base_stats(*),ship_skins(name,painting_url),ship_skills(*)&icon_url=not.is.null`, {            
            method: 'GET',
            headers: HEADERS
        });

        if (!response.ok) throw new Error('Failed to fetch from Supabase');

        masterFleet = await response.json();
        applyFiltersAndSort(); 

    } catch (error) {
        console.error('Data breach:', error);
        if (fleetCountDisplay) fleetCountDisplay.textContent = 'Connection Error';
    }
}

// ==========================================
// EVENT LISTENERS & LOGIC
// ==========================================
function setupEventListeners() {
    console.log("📡 Initializing listeners..."); 

    // Filters
    document.getElementById('search-bar')?.addEventListener('input', applyFiltersAndSort);
    document.getElementById('filter-faction')?.addEventListener('change', applyFiltersAndSort);
    document.getElementById('filter-type')?.addEventListener('change', applyFiltersAndSort);
    document.getElementById('sort-order')?.addEventListener('change', applyFiltersAndSort);

    // Modal Close Logic
    const closeDossier = () => {
        modal?.classList.add('hidden');
        const artEl = document.getElementById('dossier-art');
        if (artEl) artEl.src = ''; // Abort pending downloads
    };

    closeModalBtn?.addEventListener('click', closeDossier);
    modal?.addEventListener('click', (e) => { if (e.target === modal) closeDossier(); });

    // Theme Switches
    historyToggle?.addEventListener('change', toggleDossierView);
    globalHistoryToggle?.addEventListener('change', (e) => {
        document.body.classList.toggle('historical-theme', e.target.checked);
    });

    // Hall of Records Logic
    const rosterModal = document.getElementById('roster-modal');
    document.getElementById('open-roster-btn')?.addEventListener('click', () => rosterModal?.classList.remove('hidden'));
    document.getElementById('close-roster')?.addEventListener('click', () => rosterModal?.classList.add('hidden'));
    rosterModal?.addEventListener('click', (e) => { if (e.target === rosterModal) rosterModal.classList.add('hidden'); });

    // Global ESC Key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDossier();
            rosterModal?.classList.add('hidden');
        }
    });
}

function applyFiltersAndSort() {
    try {
        const searchTerm = document.getElementById('search-bar')?.value.toLowerCase() || '';
        const factionFilter = document.getElementById('filter-faction')?.value.toLowerCase() || 'all';
        const typeFilter = document.getElementById('filter-type')?.value.toLowerCase() || 'all';
        const sortOrder = document.getElementById('sort-order')?.value || 'az';

        let processedFleet = masterFleet.filter(ship => {
            const matchesSearch = ship.name.toLowerCase().includes(searchTerm);
            const matchesFaction = factionFilter === 'all' || (ship.faction && ship.faction.toLowerCase().includes(factionFilter));
            const matchesType = typeFilter === 'all' || (ship.hull_type && ship.hull_type.toLowerCase().includes(typeFilter));
            return matchesSearch && matchesFaction && matchesType;
        });

        processedFleet.sort((a, b) => {
            if (sortOrder === 'az') return a.name.localeCompare(b.name);
            if (sortOrder === 'za') return b.name.localeCompare(a.name);
            return 0;
        });

        if (fleetCountDisplay) fleetCountDisplay.textContent = `${processedFleet.length} Ships Displayed`;
        renderGrid(processedFleet);
    } catch (error) {
        console.error("Filter logic error:", error);
    }
}

function renderGrid(ships) {
    if (!grid) return;
    grid.innerHTML = ''; 

    ships.forEach(ship => {
        const card = document.createElement('div');
        const rarityData = parseRarity(ship.rarity);
        
        card.className = `ship-card rarity-${rarityData.class}`;
        card.addEventListener('click', () => openDossier(ship));

        card.innerHTML = `
            <div class="rarity-label">${rarityData.text}</div>
            <img class="ship-icon" src="${ship.icon_url}" alt="${ship.name}" onerror="this.onerror=null; this.src='https://placehold.co/100x100/1e293b/00f2fe?text=?';">
            <div class="ship-name">${ship.name}</div>
        `;
        grid.appendChild(card);
    });
}

// ==========================================
// DOSSIER & HISTORICAL ROUTING
// ==========================================
function getHistoricalPrefix(faction) {
    if (!faction) return ''; 
    const f = faction.toLowerCase();
    
    if (f.includes('eagle')) return 'USS ';
    if (f.includes('royal')) return 'HMS ';
    if (f.includes('sakura')) return 'IJN ';
    if (f.includes('iron')) return 'KMS ';
    if (f.includes('sardegna')) return 'RN ';
    if (f.includes('northern')) return 'SN ';
    if (f.includes('iris')) return 'FFL ';
    if (f.includes('vichya')) return 'MNF ';
    if (f.includes('dragon')) return 'ROC ';
    return ''; 
}

function updateStatGrid(level) {
    const s = currentShipStats || {};
    
    // Dynamic key mapping to prevent massive if/else blocks
    const mapping = {
        'base': { hp: 'health', fp: 'firepower', aa: 'anti_air', avi: 'aviation', trp: 'torpedo', rld: 'reload' },
        '100': { hp: 'hp_100', fp: 'fp_100', aa: 'aa_100', avi: 'avi_100', trp: 'trp_100', rld: 'reload_100' },
        '120': { hp: 'hp_120', fp: 'fp_120', aa: 'aa_120', avi: 'avi_120', trp: 'trp_120', rld: 'reload_120' },
        '125': { hp: 'hp_125', fp: 'fp_125', aa: 'aa_125', avi: 'avi_125', trp: 'trp_125', rld: 'reload_125' }
    };

    const keys = mapping[level] || mapping['120'];
    
    document.getElementById('dos-hp').textContent = s[keys.hp] || '---';
    document.getElementById('dos-fp').textContent = s[keys.fp] || '---';
    document.getElementById('dos-aa').textContent = s[keys.aa] || '---';
    document.getElementById('dos-avi').textContent = s[keys.avi] || '---';
    document.getElementById('dos-trp').textContent = s[keys.trp] || '---';
    document.getElementById('dos-rld').textContent = s[keys.rld] || '---';
}

function toggleDossierView(e) {
    const isChecked = e ? e.target.checked : historyToggle.checked;
    
    if (isChecked) {
        viewGame?.classList.remove('active-view');
        viewHistory?.classList.add('active-view');
        modalContainer?.classList.add('is-historical');
    } else {
        viewHistory?.classList.remove('active-view');
        viewGame?.classList.add('active-view');
        modalContainer?.classList.remove('is-historical');
    }
}

function openDossier(ship) {
    const dossierContent = document.querySelector('.dossier-content'); 
    const rarityData = parseRarity(ship.rarity);
    
    dossierContent.className = `modal-content dossier-content dossier-${rarityData.class}`;

    let badge = document.getElementById('dossier-rarity-badge');
    if (!badge) {
        badge = document.createElement('div');
        badge.id = 'dossier-rarity-badge';
        badge.className = 'dossier-rarity-badge';
        dossierContent.appendChild(badge);
    }
    badge.textContent = rarityData.text;
    
    const isGlobalArchive = document.body.classList.contains('historical-theme');
    if (historyToggle) historyToggle.checked = isGlobalArchive; 
    toggleDossierView(); 

    document.getElementById('dossier-name').textContent = ship.name;
    document.getElementById('dossier-faction').textContent = ship.faction || 'Unknown';
    document.getElementById('dossier-type').textContent = ship.hull_type || 'Unknown';
    
    // --- POPULATE STATS & TABS ---
    currentShipStats = (ship.ship_base_stats && ship.ship_base_stats.length > 0) ? ship.ship_base_stats[0] : {}; 
    
    const tabs = document.querySelectorAll('.stat-tab');
    if (tabs.length > 0) {
        tabs.forEach(t => t.classList.remove('active'));
        const defaultTab = document.querySelector('.stat-tab[data-level="120"]');
        if (defaultTab) defaultTab.classList.add('active');
        
        updateStatGrid('120');

        tabs.forEach(tab => {
            tab.onclick = (e) => {
                tabs.forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                updateStatGrid(e.target.getAttribute('data-level'));
            };
        });
    }

    // --- POPULATE SKILLS ---
    const skillsContainer = document.getElementById('dossier-skills-container');
    if (skillsContainer) {
        skillsContainer.innerHTML = ''; 
        if (ship.ship_skills && ship.ship_skills.length > 0) {
            ship.ship_skills.forEach(skill => {
                const iconUrl = skill.icon_url || 'https://placehold.co/48x48/1e293b/00f2fe?text=?';
                skillsContainer.innerHTML += `
                    <div class="skill-item">
                        <img class="skill-icon" src="${iconUrl}" alt="${skill.name}">
                        <div class="skill-info">
                            <div class="skill-name">${skill.name}</div>
                            <div class="skill-desc">${skill.description}</div>
                        </div>
                    </div>
                `;
            });
        } else {
            skillsContainer.innerHTML = '<p class="awaiting-data">No tactical skills detected in the Archive.</p>';
        }
    }
    
    const prefix = getHistoricalPrefix(ship.faction);
    document.getElementById('history-name').textContent = `${prefix}${ship.name}`;
    window.currentShipIcon = ship.icon_url;
    
    // Update Historical Photo
    const histArtImg = document.getElementById('history-art');
    if (histArtImg) histArtImg.src = ship.historical_photo_url || 'https://www.transparenttextures.com/patterns/black-linen.png';

    // --- PROGRESSIVE LOADING ENGINE & WARDROBE ---
    const artImg = document.getElementById('dossier-art');
    currentShipName = ship.name;

    artImg?.classList.remove('scale-normal', 'scale-large', 'scale-massive');
    if (rarityData.class === 'ur') artImg?.classList.add('scale-massive'); 
    else if (rarityData.class === 'ssr') artImg?.classList.add('scale-large');   
    else artImg?.classList.add('scale-normal');  

    // Compile Wardrobe
    const fallbackArtUrl = `https://azurlane.mrlar.dev/images/ships/${ship.name.toLowerCase().replaceAll(' ', '_')}.png`;
    currentSkins = [{ name: "Default", painting_url: ship.painting_url || fallbackArtUrl, is_base: true }];

    if (ship.ship_skins && ship.ship_skins.length > 0) {
        const retrofitSkin = ship.ship_skins.find(s => ['kai', 'retrofit'].includes(s.name.toLowerCase()));
        const otherSkins = ship.ship_skins.filter(s => !['kai', 'retrofit'].includes(s.name.toLowerCase()));

        if (retrofitSkin) currentSkins.push(retrofitSkin);
        currentSkins = currentSkins.concat(otherSkins);
    }

    currentSkinIndex = 0;

    // UI Toggles
    const prevBtn = document.querySelector('.skin-prev');
    const nextBtn = document.querySelector('.skin-next');
    const skinLabel = document.getElementById('skin-name-label');

    const hasSkins = currentSkins.length > 1;
    prevBtn?.classList.toggle('hidden', !hasSkins);
    nextBtn?.classList.toggle('hidden', !hasSkins);
    skinLabel?.classList.toggle('hidden', !hasSkins);

    loadCurrentSkin();
    modal?.classList.remove('hidden');
}

// ==========================================
// WARDROBE CONTROLS
// ==========================================
function nextSkin() {
    if (currentSkins.length <= 1) return;
    currentSkinIndex = (currentSkinIndex + 1) % currentSkins.length;
    loadCurrentSkin();
}

function prevSkin() {
    if (currentSkins.length <= 1) return;
    currentSkinIndex = (currentSkinIndex - 1 + currentSkins.length) % currentSkins.length;
    loadCurrentSkin();
}

function loadCurrentSkin() {
    const artImg = document.getElementById('dossier-art');
    const skinObj = currentSkins[currentSkinIndex];
    if (!artImg) return;
    
    const skinLabel = document.getElementById('skin-name-label');
    if (skinLabel) skinLabel.textContent = skinObj.name;

    if (skinObj.is_base && window.currentShipIcon) {
        artImg.src = window.currentShipIcon; 
    }
    
    artImg.style.opacity = '0.4';
    artImg.style.transition = 'opacity 0.4s ease-in-out';

    const heavyImage = new Image();
    heavyImage.src = skinObj.painting_url;

    heavyImage.onload = () => {
        if (!modal.classList.contains('hidden') && document.getElementById('dossier-name')?.textContent === currentShipName) {
            artImg.src = heavyImage.src; 
            artImg.style.opacity = '1';  
        }
    };
}
    
function logout() { 
    localStorage.removeItem('astra_token'); 
    window.location.href = 'login.html'; 
}