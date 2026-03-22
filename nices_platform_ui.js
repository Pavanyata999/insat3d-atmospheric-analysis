const NICESPlatform = {
    currentYear: 2023,
    availableYears: [],
    isPlaying: false,
    playInterval: null,
    currentView: 'spatial' // spatial, globe, animation
};

function initNICESPlatform(year = 2023) {
    // Check if already open
    if (document.getElementById('nices-platform-container')) {
        return;
    }
    
    NICESPlatform.currentYear = year;
    
    // Create full-screen dashboard
    createNICESDashboard();
    
    // Load data
    loadNICESData(year);
}

function createNICESDashboard() {
    // Remove any existing
    const existing = document.getElementById('nices-platform-container');
    if (existing) existing.remove();
    
    const dashboard = document.createElement('div');
    dashboard.id = 'nices-platform-container';
    dashboard.innerHTML = `
        <style>
            #nices-platform-container {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: linear-gradient(135deg, #010814 0%, #020d1f 50%, #041529 100%);
                z-index: 10000;
                overflow-y: auto;
                font-family: 'Rajdhani', sans-serif;
            }
            .nices-header {
                background: rgba(0,20,40,0.9);
                border-bottom: 2px solid #00d4ff;
                padding: 15px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            .nices-title {
                color: #00d4ff;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: 2px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .nices-controls {
                display: flex;
                gap: 15px;
                align-items: center;
            }
            .nices-year-display {
                color: #fff;
                font-size: 28px;
                font-weight: 700;
                background: rgba(0,212,255,0.15);
                padding: 8px 20px;
                border-radius: 8px;
                border: 1px solid #00d4ff;
                min-width: 100px;
                text-align: center;
            }
            .nices-btn {
                background: linear-gradient(135deg, #00d4ff, #0088cc);
                color: #000;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                font-family: 'Rajdhani', sans-serif;
                font-size: 14px;
            }
            .nices-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(0,212,255,0.4);
            }
            .nices-close {
                background: rgba(255,50,50,0.8);
                color: #fff;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 20px;
                transition: all 0.3s;
            }
            .nices-close:hover {
                background: rgba(255,50,50,1);
                transform: scale(1.1);
            }
            .nices-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: auto auto;
                gap: 20px;
                padding: 20px;
                max-width: 1800px;
                margin: 0 auto;
            }
            .nices-panel {
                background: rgba(5, 15, 35, 0.8);
                border: 1px solid rgba(0,212,255,0.3);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            }
            .nices-panel-header {
                background: linear-gradient(90deg, rgba(0,212,255,0.2), transparent);
                padding: 12px 20px;
                border-bottom: 1px solid rgba(0,212,255,0.2);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .nices-panel-title {
                color: #fff;
                font-size: 16px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .nices-panel-icon {
                font-size: 20px;
            }
            .nices-panel-content {
                height: 400px;
                position: relative;
            }
            .nices-panel-full {
                grid-column: 1 / -1;
            }
            .nices-insight-box {
                background: rgba(0,20,40,0.9);
                border-left: 4px solid #00d4ff;
                padding: 15px 20px;
                margin: 20px;
                border-radius: 0 8px 8px 0;
            }
            .nices-insight-title {
                color: #00d4ff;
                font-weight: 600;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .nices-insight-text {
                color: #ccc;
                line-height: 1.6;
                font-size: 14px;
            }
            .nices-insight-recommendation {
                color: #ffd700;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(255,255,255,0.1);
                font-style: italic;
            }
            .nices-view-tabs {
                display: flex;
                gap: 10px;
            }
            .nices-tab {
                background: rgba(255,255,255,0.1);
                color: #fff;
                border: 1px solid rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 13px;
                transition: all 0.3s;
            }
            .nices-tab.active {
                background: #00d4ff;
                color: #000;
                border-color: #00d4ff;
            }
            .nices-loading {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #00d4ff;
                font-size: 18px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 15px;
            }
            .nices-spinner {
                width: 50px;
                height: 50px;
                border: 3px solid rgba(0,212,255,0.2);
                border-top-color: #00d4ff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .nices-slider-container {
                display: flex;
                align-items: center;
                gap: 15px;
                background: rgba(0,0,0,0.3);
                padding: 10px 20px;
                border-radius: 30px;
            }
            .nices-slider {
                width: 200px;
                height: 6px;
                -webkit-appearance: none;
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
                outline: none;
            }
            .nices-slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 20px;
                height: 20px;
                background: #00d4ff;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 0 10px rgba(0,212,255,0.5);
            }
        </style>
        
        <div class="nices-header">
            <div class="nices-title">
                🛰️ NICES SCIENTIFIC VISUALIZATION PLATFORM
            </div>
            <div class="nices-controls">
                <div class="nices-slider-container">
                    <button class="nices-btn" id="nices-play-btn" onclick="toggleNICESPlay()">▶ PLAY</button>
                    <input type="range" class="nices-slider" id="nices-year-slider" 
                           min="2009" max="2023" value="${NICESPlatform.currentYear}" 
                           onchange="updateNICESYear(this.value)">
                    <div class="nices-year-display" id="nices-year-display">${NICESPlatform.currentYear}</div>
                </div>
                <div class="nices-close" onclick="closeNICESPlatform()">✕</div>
            </div>
        </div>
        
        <div class="nices-grid">
            <!-- Panel 1: Spatial Distribution -->
            <div class="nices-panel">
                <div class="nices-panel-header">
                    <div class="nices-panel-title">
                        <span class="nices-panel-icon">🌍</span>
                        SPATIAL DISTRIBUTION
                    </div>
                    <div class="nices-view-tabs">
                        <button class="nices-tab active" onclick="switchNICESView('spatial')">Flat Map</button>
                        <button class="nices-tab" onclick="switchNICESView('globe')">Globe</button>
                    </div>
                </div>
                <div class="nices-panel-content" id="nices-spatial-plot">
                    <div class="nices-loading">
                        <div class="nices-spinner"></div>
                        <div>Loading spatial data...</div>
                    </div>
                </div>
            </div>
            
            <!-- Panel 2: Animation -->
            <div class="nices-panel">
                <div class="nices-panel-header">
                    <div class="nices-panel-title">
                        <span class="nices-panel-icon">🎞️</span>
                        TEMPORAL EVOLUTION
                    </div>
                </div>
                <div class="nices-panel-content" id="nices-animation-plot">
                    <div class="nices-loading">
                        <div class="nices-spinner"></div>
                        <div>Loading animation frames...</div>
                    </div>
                </div>
            </div>
            
            <!-- Panel 3: Trend Graph -->
            <div class="nices-panel">
                <div class="nices-panel-header">
                    <div class="nices-panel-title">
                        <span class="nices-panel-icon">📊</span>
                        TREND ANALYSIS
                    </div>
                </div>
                <div class="nices-panel-content" id="nices-trend-plot">
                    <div class="nices-loading">
                        <div class="nices-spinner"></div>
                        <div>Calculating trends...</div>
                    </div>
                </div>
            </div>
            
            <!-- Panel 4: Vertical Profile -->
            <div class="nices-panel">
                <div class="nices-panel-header">
                    <div class="nices-panel-title">
                        <span class="nices-panel-icon">⛰️</span>
                        VERTICAL PROFILE
                    </div>
                </div>
                <div class="nices-panel-content" id="nices-profile-plot">
                    <div class="nices-loading">
                        <div class="nices-spinner"></div>
                        <div>Loading altitude data...</div>
                    </div>
                </div>
            </div>
            
            <!-- AI Insight Panel -->
            <div class="nices-panel nices-panel-full">
                <div class="nices-panel-header">
                    <div class="nices-panel-title">
                        <span class="nices-panel-icon">🧠</span>
                        AI INSIGHT ENGINE
                    </div>
                </div>
                <div class="nices-insight-box" id="nices-insight-box">
                    <div class="nices-insight-title">🔄 Analyzing atmospheric conditions...</div>
                    <div class="nices-insight-text">Please wait while AI processes the data.</div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(dashboard);
}

/**
 * Load data from backend
 */
async function loadNICESData(year) {
    try {
        const response = await fetch(`http://127.0.0.1:8067/get_full_analysis?year=${year}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            NICESPlatform.availableYears = data.statistics.available_years || [];
            
            // Update year slider
            const slider = document.getElementById('nices-year-slider');
            if (slider && NICESPlatform.availableYears.length > 0) {
                slider.min = Math.min(...NICESPlatform.availableYears);
                slider.max = Math.max(...NICESPlatform.availableYears);
            }
            
            // Render all visualizations
            renderNICESSpatial(data.spatial_map, data.globe_map);
            renderNICESAnimation(data.animation_frames);
            renderNICESTrend(data.trend_graph);
            renderNICESProfile(data.vertical_profile);
            renderNICESInsight(data.insight);
            
            // Update year display
            document.getElementById('nices-year-display').textContent = year;
        } else {
            showNICESError('Failed to load data: ' + data.message);
        }
    } catch (error) {
        console.error('NICES Error:', error);
        showNICESError('Connection error. Please check if server is running.');
    }
}

/**
 * Render Spatial Distribution (Flat Map or Globe)
 */
function renderNICESSpatial(spatialData, globeData) {
    const container = document.getElementById('nices-spatial-plot');
    if (!container) return;
    
    // Use appropriate data based on view
    const data = NICESPlatform.currentView === 'globe' ? globeData : spatialData;
    
    if (!data || !data.data || data.data.length === 0) {
        container.innerHTML = '<div style="color:#ff6b6b;text-align:center;padding:50px;">No spatial data available</div>';
        return;
    }
    
    Plotly.newPlot(container, data.data, data.layout, {responsive: true});
}

function switchNICESView(view) {
    NICESPlatform.currentView = view;
    
    // Update tab styles
    document.querySelectorAll('.nices-tab').forEach((tab, idx) => {
        if ((view === 'spatial' && idx === 0) || (view === 'globe' && idx === 1)) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Reload with new view
    loadNICESData(NICESPlatform.currentYear);
}

function renderNICESAnimation(animationData) {
    const container = document.getElementById('nices-animation-plot');
    if (!container) return;
    
    if (!animationData || !animationData.frames || animationData.frames.length === 0) {
        container.innerHTML = '<div style="color:#ff6b6b;text-align:center;padding:50px;">No animation data available</div>';
        return;
    }
    
    Plotly.newPlot(container, {
        data: animationData.data,
        layout: animationData.layout,
        frames: animationData.frames
    }, {responsive: true});
}

function renderNICESTrend(trendData) {
    const container = document.getElementById('nices-trend-plot');
    if (!container) return;
    
    if (!trendData || !trendData.data || trendData.data.length === 0) {
        container.innerHTML = '<div style="color:#ff6b6b;text-align:center;padding:50px;">No trend data available</div>';
        return;
    }
    
    Plotly.newPlot(container, trendData.data, trendData.layout, {responsive: true});
}

function renderNICESProfile(profileData) {
    const container = document.getElementById('nices-profile-plot');
    if (!container) return;
    
    if (!profileData || !profileData.data || profileData.data.length === 0) {
        container.innerHTML = '<div style="color:#ff6b6b;text-align:center;padding:50px;">No profile data available</div>';
        return;
    }
    
    Plotly.newPlot(container, profileData.data, profileData.layout, {responsive: true});
}

function renderNICESInsight(insight) {
    const container = document.getElementById('nices-insight-box');
    if (!container || !insight) return;
    
    const alertColors = {
        'high': '#ff4444',
        'medium': '#ffaa00',
        'low': '#00d4ff',
        'info': '#888'
    };
    
    const alertIcon = {
        'high': '🚨',
        'medium': '⚠️',
        'low': '✓',
        'info': 'ℹ️'
    };
    
    container.innerHTML = `
        <div class="nices-insight-title" style="color: ${alertColors[insight.alert_level] || '#00d4ff'}">
            ${alertIcon[insight.alert_level] || '🔍'} ANALYSIS COMPLETE
        </div>
        <div class="nices-insight-text">${insight.summary || 'No analysis available.'}</div>
        ${insight.recommendation ? `
            <div class="nices-insight-recommendation">
                💡 <strong>Recommendation:</strong> ${insight.recommendation}
            </div>
        ` : ''}
    `;
    
    // Update border color
    container.style.borderLeftColor = alertColors[insight.alert_level] || '#00d4ff';
}

function updateNICESYear(year) {
    year = parseInt(year);
    NICESPlatform.currentYear = year;
    document.getElementById('nices-year-display').textContent = year;
    loadNICESData(year);
}

function toggleNICESPlay() {
    const btn = document.getElementById('nices-play-btn');
    
    if (NICESPlatform.isPlaying) {
        // Pause
        clearInterval(NICESPlatform.playInterval);
        NICESPlatform.isPlaying = false;
        btn.textContent = '▶ PLAY';
        
        // Stop Plotly animation
        const animContainer = document.getElementById('nices-animation-plot');
        if (animContainer) {
            Plotly.animate(animContainer, null, {mode: 'immediate'});
        }
    } else {
        // Play
        NICESPlatform.isPlaying = true;
        btn.textContent = '⏸ PAUSE';
        
        // Animate through years
        const years = NICESPlatform.availableYears.length > 0 ? 
            NICESPlatform.availableYears : 
            Array.from({length: 15}, (_, i) => 2009 + i);
        
        let currentIdx = years.indexOf(NICESPlatform.currentYear);
        if (currentIdx === -1) currentIdx = 0;
        
        NICESPlatform.playInterval = setInterval(() => {
            currentIdx = (currentIdx + 1) % years.length;
            const nextYear = years[currentIdx];
            
            // Update slider and load data
            const slider = document.getElementById('nices-year-slider');
            if (slider) slider.value = nextYear;
            updateNICESYear(nextYear);
        }, 1500);
    }
}

function showNICESError(message) {
    const panels = ['nices-spatial-plot', 'nices-animation-plot', 'nices-trend-plot', 'nices-profile-plot'];
    panels.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = `<div style="color:#ff6b6b;text-align:center;padding:50px;">${message}</div>`;
        }
    });
}

function closeNICESPlatform() {
    // Stop animation
    if (NICESPlatform.playInterval) {
        clearInterval(NICESPlatform.playInterval);
    }
    NICESPlatform.isPlaying = false;
    
    // Remove dashboard
    const dashboard = document.getElementById('nices-platform-container');
    if (dashboard) {
        dashboard.remove();
    }
}

function detectNICESPlatformTrigger(message) {
    const triggers = [
        'full analysis',
        'scientific view',
        'nices platform',
        'complete analysis',
        'visualization platform',
        'show all charts',
        'all visualizations',
        'research dashboard'
    ];
    
    const msg = message.toLowerCase();
    return triggers.some(trigger => msg.includes(trigger));
}

// Export for global access
window.initNICESPlatform = initNICESPlatform;
window.updateNICESYear = updateNICESYear;
window.toggleNICESPlay = toggleNICESPlay;
window.switchNICESView = switchNICESView;
window.closeNICESPlatform = closeNICESPlatform;
window.detectNICESPlatformTrigger = detectNICESPlatformTrigger;
