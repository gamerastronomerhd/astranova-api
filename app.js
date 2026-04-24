// ==========================================
// COMMANDER CONFIGURATION
// ==========================================
const SUPABASE_URL = 'https://xojhznvqftnwhvdxzndh.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhvamh6bnZxZnRud2h2ZHh6bmRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4NTY4ODQsImV4cCI6MjA5MDQzMjg4NH0.to5JcWEKZeHeFk646cJjSUFnHbz6gr0ThFPkUG2qWsM';

const HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': `Bearer ${SUPABASE_KEY}`,
    'Content-Type': 'application/json'
};

let masterFleet = []; 
let currentSkins = [];
let currentSkinIndex = 0;
let currentShipName = "";

// UI Elements
const modal = document.getElementById('dossier-modal');
const closeModalBtn = document.getElementById('close-modal');
const historyToggle = document.getElementById('history-toggle');
const globalHistoryToggle = document.getElementById('global-history-toggle');
const viewGame = document.querySelector('.view-game');
const viewHistory = document.querySelector('.view-history');
const modalContainer = document.getElementById('modal-container');

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    fetchFleetData();
    setupEventListeners();
});

async function fetchFleetData() {
    try {
        // ADDED 'rarity' TO THE SELECT QUERY RIGHT AFTER 'name'
        const response = await fetch(`${SUPABASE_URL}/rest/v1/ships?select=id,name,rarity,icon_url,painting_url,faction,hull_type,ship_skins(name,painting_url)&icon_url=not.is.null`, {
            method: 'GET',
            headers: HEADERS
        });

        if (!response.ok) throw new Error('Failed to fetch from Supabase');

        masterFleet = await response.json();
        applyFiltersAndSort(); 

    } catch (error) {
        console.error('Data breach:', error);
        document.getElementById('fleet-count').textContent = 'Connection Error';
    }
}

// ==========================================
// EVENT LISTENERS & LOGIC
// ==========================================
function setupEventListeners() {
    console.log("📡 Initializing listeners..."); 

    const search = document.getElementById('search-bar');
    
    // Filters
    document.getElementById('search-bar')?.addEventListener('input', applyFiltersAndSort);
    document.getElementById('filter-faction')?.addEventListener('change', applyFiltersAndSort);
    document.getElementById('filter-type')?.addEventListener('change', applyFiltersAndSort);
    document.getElementById('sort-order')?.addEventListener('change', applyFiltersAndSort);

    // --- Modal & Theme Toggles ---
    
    // 1. Close via the "X" button
    closeModalBtn?.addEventListener('click', () => {
        modal.classList.add('hidden');
        document.getElementById('dossier-art').src = ''; // 🚨 ABORT SWITCH: KILLS PENDING DOWNLOADS
    });

    // 2. Close via clicking the dark background
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.getElementById('dossier-art').src = ''; // 🚨 ABORT SWITCH: KILLS PENDING DOWNLOADS
        }
    });

    // 3. Theme Switches
    historyToggle?.addEventListener('change', toggleDossierView);
    globalHistoryToggle?.addEventListener('change', (e) => {
        document.body.classList.toggle('historical-theme', e.target.checked);
    });

    console.log("✅ Listeners attached successfully!"); 
}

function applyFiltersAndSort() {
    try {
        const searchTerm = document.getElementById('search-bar').value.toLowerCase();
        const factionFilter = document.getElementById('filter-faction').value.toLowerCase();
        const typeFilter = document.getElementById('filter-type').value.toLowerCase();
        const sortOrder = document.getElementById('sort-order').value;

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

        document.getElementById('fleet-count').textContent = `${processedFleet.length} Ships Displayed`;
        renderGrid(processedFleet);
    } catch (error) {
        console.error("Filter logic error:", error);
    }
}

function renderGrid(ships) {
    const grid = document.getElementById('fleet-grid');
    grid.innerHTML = ''; 

    ships.forEach(ship => {
        const card = document.createElement('div');
        card.className = 'ship-card';
        card.addEventListener('click', () => openDossier(ship));

        const img = document.createElement('img');
        img.className = 'ship-icon';
        img.src = ship.icon_url;
        img.alt = ship.name;
        img.onerror = function() {
            this.onerror = null; 
            this.src = 'https://placehold.co/100x100/1e293b/00f2fe?text=?';
        };

        const nameLabel = document.createElement('div');
        nameLabel.className = 'ship-name';
        nameLabel.textContent = ship.name;

        card.appendChild(img);
        card.appendChild(nameLabel);
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

function toggleDossierView(e) {
    const isChecked = e ? e.target.checked : historyToggle.checked;
    
    if (isChecked) {
        viewGame.classList.remove('active-view');
        viewHistory.classList.add('active-view');
        modalContainer.classList.add('is-historical');
    } else {
        viewHistory.classList.remove('active-view');
        viewGame.classList.add('active-view');
        modalContainer.classList.remove('is-historical');
    }
}

function openDossier(ship) {
    const isGlobalArchive = document.body.classList.contains('historical-theme');
    historyToggle.checked = isGlobalArchive; 
    toggleDossierView(); 

    document.getElementById('dossier-name').textContent = ship.name;
    document.getElementById('dossier-faction').textContent = ship.faction || 'Unknown';
    document.getElementById('dossier-type').textContent = ship.hull_type || 'Unknown';
    
    const prefix = getHistoricalPrefix(ship.faction);
    document.getElementById('history-name').textContent = `${prefix}${ship.name}`;
	window.currentShipIcon = ship.icon_url;
	
	// Update Historical Photo
    const histArtImg = document.getElementById('history-art');
    // If your database eventually has a 'historical_photo_url', it will use it. 
    // Otherwise, it defaults to a standard placeholder.
    histArtImg.src = ship.historical_photo_url || 'https://www.transparenttextures.com/patterns/black-linen.png';

    // --- PROGRESSIVE LOADING ENGINE & WARDROBE ---
    const artImg = document.getElementById('dossier-art');
    currentShipName = ship.name;

    // 1. DYNAMIC 3-TIER RARITY SCALING
    artImg.classList.remove('scale-normal', 'scale-large', 'scale-massive');
    const urRarities = ["Ultra Rare", "Decisive"];
    const ssrRarities = ["Super Rare", "Priority"];
    
    if (urRarities.includes(ship.rarity)) {
        artImg.classList.add('scale-massive'); 
    } else if (ssrRarities.includes(ship.rarity)) {
        artImg.classList.add('scale-large');   
    } else {
        artImg.classList.add('scale-normal');  
    }

    // 2. COMPILE THE WARDROBE
    const fallbackArtUrl = `https://azurlane.mrlar.dev/images/ships/${ship.name.toLowerCase().replace(/ /g, '_')}.png`;
    
    // The base default skin is always Slot 0
    currentSkins = [
        { name: "Default", painting_url: ship.painting_url || fallbackArtUrl, is_base: true }
    ];

    // Append any extra skins from the database
    if (ship.ship_skins && ship.ship_skins.length > 0) {
        currentSkins = currentSkins.concat(ship.ship_skins);
    }

    currentSkinIndex = 0;

    // 3. UI TOGGLES
    const prevBtn = document.querySelector('.skin-prev');
    const nextBtn = document.querySelector('.skin-next');
    const skinLabel = document.getElementById('skin-name-label');

    if (currentSkins.length > 1) {
        prevBtn.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
        skinLabel.classList.remove('hidden');
    } else {
        prevBtn.classList.add('hidden');
        nextBtn.classList.add('hidden');
        skinLabel.classList.add('hidden');
    }

    // Load the first skin
    loadCurrentSkin();
    
    modal.classList.remove('hidden');
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
    
    document.getElementById('skin-name-label').textContent = skinObj.name;

    // Use icon_url temporarily ONLY if it's the base skin, otherwise just dim
    if (skinObj.is_base && window.currentShipIcon) {
        artImg.src = window.currentShipIcon; 
    }
    
    artImg.style.opacity = '0.4';
    artImg.style.transition = 'opacity 0.4s ease-in-out';

    const heavyImage = new Image();
    heavyImage.src = skinObj.painting_url;

    heavyImage.onload = () => {
        // Safety Check: Ensure the user hasn't closed the modal or clicked another ship/skin
        if (!modal.classList.contains('hidden') && document.getElementById('dossier-name').textContent === currentShipName) {
            artImg.src = heavyImage.src; 
            artImg.style.opacity = '1';  
        }
    };
}
    
function logout() { 
    localStorage.removeItem('astra_token'); 
    window.location.href = 'login.html'; 
}