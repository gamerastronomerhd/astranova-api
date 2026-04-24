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
        const response = await fetch(`${SUPABASE_URL}/rest/v1/ships?select=id,name,icon_url,painting_url,faction,hull_type&icon_url=not.is.null`, {
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
	
	// Update Historical Photo
    const histArtImg = document.getElementById('history-art');
    // If your database eventually has a 'historical_photo_url', it will use it. 
    // Otherwise, it defaults to a standard placeholder.
    histArtImg.src = ship.historical_photo_url || 'https://www.transparenttextures.com/patterns/black-linen.png';

    // --- PROGRESSIVE LOADING ENGINE ---
    const artImg = document.getElementById('dossier-art');
    
    // 1. Instant Feedback: Use the small icon, stretch it, and dim it
    artImg.src = ship.icon_url; 
    artImg.style.opacity = '0.4';
    artImg.style.transition = 'opacity 0.4s ease-in-out';

    // 2. Determine the High-Res Target
    const fallbackArtUrl = `https://azurlane.mrlar.dev/images/ships/${ship.name.toLowerCase().replace(/ /g, '_')}.png`;
    const targetHighResUrl = ship.painting_url || fallbackArtUrl;

    // 3. Load the heavy image stealthily in the background
    const heavyImage = new Image();
    heavyImage.src = targetHighResUrl;

    heavyImage.onload = () => {
        // 4. Safety Check: Only swap if the user hasn't closed or clicked a new ship!
        if (!modal.classList.contains('hidden') && document.getElementById('dossier-name').textContent === ship.name) {
            artImg.src = heavyImage.src; // Swap to the crisp image
            artImg.style.opacity = '1';  // Fade it in brilliantly
        }
    };
    
    modal.classList.remove('hidden');
}
function logout() { 
    localStorage.removeItem('astra_token'); 
    window.location.href = 'login.html'; 
}