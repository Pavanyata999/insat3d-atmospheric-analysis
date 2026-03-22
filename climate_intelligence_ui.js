const ClimateSystem = {
    currentYear: 2009,
    availableYears: [],
    isPlaying: false,
    playSpeed: 1000,
    playInterval: null,
    globePlot: null,
    trendPlot: null,
    data: null,
    autoRotateInterval: null
};

function initClimateIntelligence() {
    console.log('Initializing Climate Intelligence System...');
    
    fetchAvailableYears().then(() => {
        if (ClimateSystem.availableYears.length > 0) {
            ClimateSystem.currentYear = ClimateSystem.availableYears[0];
        }
        
        createClimateUI();
        updateClimateDisplay(ClimateSystem.currentYear);
        
        console.log('Climate Intelligence System Ready');
    });
}

async function fetchAvailableYears() {
    try {
        const response = await fetch('/get_available_years');
        const result = await response.json();
        
        if (result.status === 'success') {
            ClimateSystem.availableYears = result.years;
        }
    } catch (error) {
        console.error('Failed to fetch years:', error);
        ClimateSystem.availableYears = [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023];
    }
}

function createClimateUI() {
    if (document.getElementById('climate-intelligence-container')) {
        return;
    }
    
    const container = document.createElement('div');
    container.id = 'climate-intelligence-container';
    container.className = 'climate-intelligence-dashboard';
    container.innerHTML = `
        <style>
            .climate-intelligence-dashboard {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(135deg, #000511 0%, #001122 50%, #000814 100%);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                font-family: 'Orbitron', 'Rajdhani', sans-serif;
                overflow: hidden;
            }
            
            .climate-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 30px;
                background: rgba(0, 20, 40, 0.8);
                border-bottom: 2px solid #00e5cc;
                box-shadow: 0 0 30px rgba(0, 229, 204, 0.3);
            }
            
            .climate-title {
                font-size: 24px;
                color: #00e5cc;
                text-transform: uppercase;
                letter-spacing: 3px;
                text-shadow: 0 0 20px rgba(0, 229, 204, 0.8);
                font-weight: 700;
            }
            
            .climate-subtitle {
                font-size: 12px;
                color: #a8e6f0;
                margin-left: 10px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .climate-close-btn {
                background: transparent;
                border: 2px solid #ff4444;
                color: #ff4444;
                padding: 8px 20px;
                cursor: pointer;
                font-family: 'Orbitron', sans-serif;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 2px;
                transition: all 0.3s ease;
                border-radius: 4px;
            }
            
            .climate-close-btn:hover {
                background: #ff4444;
                color: #000;
                box-shadow: 0 0 20px rgba(255, 68, 68, 0.5);
            }
            
            /* Main Content */
            .climate-main {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            /* Globe Section */
            .climate-globe-section {
                flex: 2;
                display: flex;
                flex-direction: column;
                padding: 20px;
                position: relative;
            }
            
            .climate-globe-container {
                flex: 1;
                background: rgba(5, 10, 25, 0.8);
                border: 2px solid rgba(0, 229, 204, 0.3);
                border-radius: 12px;
                position: relative;
                overflow: hidden;
                box-shadow: 
                    inset 0 0 60px rgba(0, 229, 204, 0.1),
                    0 0 40px rgba(0, 229, 204, 0.2);
            }
            
            .climate-globe-container::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, transparent, rgba(0, 229, 204, 0.3), transparent);
                border-radius: 12px;
                z-index: -1;
                animation: borderGlow 3s ease-in-out infinite;
            }
            
            @keyframes borderGlow {
                0%, 100% { opacity: 0.5; }
                50% { opacity: 1; }
            }
            
            #climate-globe-plot {
                width: 100%;
                height: 100%;
            }
            
            /* Globe Overlay Info */
            .climate-globe-overlay {
                position: absolute;
                top: 20px;
                left: 20px;
                background: rgba(0, 10, 20, 0.9);
                border: 1px solid rgba(0, 229, 204, 0.5);
                padding: 15px 20px;
                border-radius: 8px;
                color: #fff;
                font-size: 14px;
                backdrop-filter: blur(10px);
            }
            
            .climate-globe-overlay .year-display {
                font-size: 28px;
                color: #00e5cc;
                font-weight: 700;
                text-shadow: 0 0 15px rgba(0, 229, 204, 0.8);
            }
            
            .climate-globe-overlay .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 1.5s ease-in-out infinite;
            }
            
            .status-normal { background: #00ff00; }
            .status-warning { background: #ffaa00; }
            .status-critical { background: #ff0000; }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.5; transform: scale(1.2); }
            }
            
            /* Right Panel */
            .climate-right-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 20px;
                gap: 20px;
                max-width: 450px;
                background: rgba(0, 10, 20, 0.5);
                border-left: 1px solid rgba(0, 229, 204, 0.2);
            }
            
            /* Trend Panel */
            .climate-trend-panel {
                background: rgba(5, 15, 30, 0.9);
                border: 1px solid rgba(0, 200, 255, 0.3);
                border-radius: 10px;
                padding: 15px;
                height: 280px;
                box-shadow: 0 0 20px rgba(0, 200, 255, 0.1);
            }
            
            .panel-title {
                font-size: 13px;
                color: #00c8ff;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .panel-title::before {
                content: '▸';
                color: #00e5cc;
                font-size: 16px;
            }
            
            #climate-trend-plot {
                width: 100%;
                height: calc(100% - 35px);
            }
            
            /* Stats Panel */
            .climate-stats-panel {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 10px;
            }
            
            .stat-card {
                background: rgba(0, 15, 30, 0.8);
                border: 1px solid rgba(0, 229, 204, 0.2);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .stat-card:hover {
                border-color: rgba(0, 229, 204, 0.5);
                box-shadow: 0 0 15px rgba(0, 229, 204, 0.2);
            }
            
            .stat-label {
                font-size: 10px;
                color: #a8e6f0;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 5px;
            }
            
            .stat-value {
                font-size: 20px;
                color: #00e5cc;
                font-weight: 700;
                text-shadow: 0 0 10px rgba(0, 229, 204, 0.5);
            }
            
            .stat-unit {
                font-size: 11px;
                color: #6a9fb5;
            }
            
            /* Anomaly Panel */
            .climate-anomaly-panel {
                background: rgba(10, 0, 20, 0.9);
                border: 1px solid rgba(255, 0, 100, 0.3);
                border-radius: 10px;
                padding: 15px;
                position: relative;
                overflow: hidden;
            }
            
            .climate-anomaly-panel.critical {
                border-color: #ff0044;
                box-shadow: 0 0 20px rgba(255, 0, 68, 0.3);
                animation: criticalPulse 2s ease-in-out infinite;
            }
            
            .climate-anomaly-panel.warning {
                border-color: #ffaa00;
                box-shadow: 0 0 20px rgba(255, 170, 0, 0.3);
            }
            
            @keyframes criticalPulse {
                0%, 100% { box-shadow: 0 0 20px rgba(255, 0, 68, 0.3); }
                50% { box-shadow: 0 0 40px rgba(255, 0, 68, 0.6); }
            }
            
            .anomaly-title {
                font-size: 12px;
                color: #ff6b9d;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 10px;
            }
            
            .anomaly-message {
                font-size: 14px;
                color: #fff;
                line-height: 1.5;
                font-weight: 500;
            }
            
            .anomaly-zscore {
                font-size: 11px;
                color: #a8a8a8;
                margin-top: 8px;
            }
            
            /* Event Prediction Panel */
            .climate-event-panel {
                background: rgba(0, 20, 10, 0.9);
                border: 1px solid rgba(0, 255, 150, 0.3);
                border-radius: 10px;
                padding: 15px;
                flex: 1;
            }
            
            .climate-event-panel.monsoon {
                border-color: #00ff96;
                box-shadow: 0 0 20px rgba(0, 255, 150, 0.3);
            }
            
            .climate-event-panel.cyclone {
                border-color: #ff6600;
                box-shadow: 0 0 20px rgba(255, 102, 0, 0.3);
            }
            
            .climate-event-panel.dry {
                border-color: #ffcc00;
                box-shadow: 0 0 20px rgba(255, 204, 0, 0.3);
            }
            
            .event-title {
                font-size: 12px;
                color: #00ff96;
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 10px;
            }
            
            .event-description {
                font-size: 16px;
                color: #fff;
                font-weight: 600;
                margin-bottom: 10px;
                line-height: 1.4;
            }
            
            .event-confidence {
                font-size: 11px;
                color: #6aff9e;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .event-recommendation {
                font-size: 12px;
                color: #a8e6f0;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(0, 229, 204, 0.2);
                line-height: 1.5;
            }
            
            /* Time Control Panel */
            .climate-control-panel {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 20px;
                padding: 20px;
                background: rgba(0, 10, 20, 0.9);
                border-top: 2px solid rgba(0, 229, 204, 0.3);
            }
            
            .time-slider-container {
                flex: 1;
                max-width: 600px;
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .time-slider-label {
                font-size: 12px;
                color: #00e5cc;
                text-transform: uppercase;
                letter-spacing: 2px;
                min-width: 60px;
            }
            
            .time-slider {
                flex: 1;
                -webkit-appearance: none;
                appearance: none;
                height: 8px;
                background: rgba(0, 229, 204, 0.2);
                border-radius: 4px;
                outline: none;
            }
            
            .time-slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 24px;
                height: 24px;
                background: #00e5cc;
                border-radius: 50%;
                cursor: pointer;
                box-shadow: 0 0 20px rgba(0, 229, 204, 0.8);
                border: 3px solid #001122;
                transition: transform 0.2s ease;
            }
            
            .time-slider::-webkit-slider-thumb:hover {
                transform: scale(1.2);
            }
            
            .play-button {
                background: linear-gradient(135deg, #00e5cc 0%, #00c8ff 100%);
                border: none;
                color: #001122;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                box-shadow: 0 0 30px rgba(0, 229, 204, 0.5);
            }
            
            .play-button:hover {
                transform: scale(1.1);
                box-shadow: 0 0 40px rgba(0, 229, 204, 0.8);
            }
            
            .play-button.playing {
                background: linear-gradient(135deg, #ff4444 0%, #ff8844 100%);
                box-shadow: 0 0 30px rgba(255, 68, 68, 0.5);
            }
            
            .year-display-large {
                font-size: 48px;
                color: #00e5cc;
                font-weight: 700;
                text-shadow: 0 0 30px rgba(0, 229, 204, 0.8);
                min-width: 120px;
                text-align: center;
            }
            
            /* Loading Overlay */
            .climate-loading {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 5, 15, 0.95);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                transition: opacity 0.5s ease;
            }
            
            .climate-loading.hidden {
                opacity: 0;
                pointer-events: none;
            }
            
            .loading-spinner {
                width: 80px;
                height: 80px;
                border: 4px solid rgba(0, 229, 204, 0.2);
                border-top-color: #00e5cc;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                box-shadow: 0 0 30px rgba(0, 229, 204, 0.3);
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            .loading-text {
                margin-top: 20px;
                font-size: 14px;
                color: #00e5cc;
                text-transform: uppercase;
                letter-spacing: 3px;
                animation: loadingPulse 1.5s ease-in-out infinite;
            }
            
            @keyframes loadingPulse {
                0%, 100% { opacity: 0.5; }
                50% { opacity: 1; }
            }
        </style>
        
        <!-- Loading Screen -->
        <div class="climate-loading" id="climate-loading">
            <div class="loading-spinner"></div>
            <div class="loading-text">Initializing Atmospheric Intelligence...</div>
        </div>
        
        <!-- Header -->
        <div class="climate-header">
            <div>
                <span class="climate-title">🌍 NICES Climate Intelligence</span>
                <span class="climate-subtitle">ISRO-Grade Atmospheric Monitoring System</span>
            </div>
            <button class="climate-close-btn" onclick="closeClimateIntelligence()">✕ Close</button>
        </div>
        
        <!-- Main Content -->
        <div class="climate-main">
            <!-- Globe Section -->
            <div class="climate-globe-section">
                <div class="climate-globe-container">
                    <div id="climate-globe-plot"></div>
                    <div class="climate-globe-overlay">
                        <div>ATMOSPHERIC STATUS</div>
                        <div class="year-display" id="globe-year">2009</div>
                        <div style="margin-top: 10px;">
                            <span class="status-indicator" id="globe-status"></span>
                            <span id="globe-status-text">Monitoring...</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Panel -->
            <div class="climate-right-panel">
                <!-- Trend Panel -->
                <div class="climate-trend-panel">
                    <div class="panel-title">Temporal Evolution (2009-2023)</div>
                    <div id="climate-trend-plot"></div>
                </div>
                
                <!-- Stats Panel -->
                <div class="climate-stats-panel">
                    <div class="stat-card">
                        <div class="stat-label">Mean Value</div>
                        <div class="stat-value" id="stat-mean">--</div>
                        <div class="stat-unit">ppm</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Std Deviation</div>
                        <div class="stat-value" id="stat-std">--</div>
                        <div class="stat-unit">σ</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Maximum</div>
                        <div class="stat-value" id="stat-max">--</div>
                        <div class="stat-unit">ppm</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Minimum</div>
                        <div class="stat-value" id="stat-min">--</div>
                        <div class="stat-unit">ppm</div>
                    </div>
                </div>
                
                <!-- Anomaly Panel -->
                <div class="climate-anomaly-panel" id="anomaly-panel">
                    <div class="anomaly-title">⚠️ Anomaly Detection System</div>
                    <div class="anomaly-message" id="anomaly-message">Analyzing atmospheric patterns...</div>
                    <div class="anomaly-zscore" id="anomaly-zscore"></div>
                </div>
                
                <!-- Event Prediction Panel -->
                <div class="climate-event-panel" id="event-panel">
                    <div class="event-title">🔮 Event Prediction Engine</div>
                    <div class="event-description" id="event-description">Initializing prediction models...</div>
                    <div class="event-confidence" id="event-confidence"></div>
                    <div class="event-recommendation" id="event-recommendation"></div>
                </div>
            </div>
        </div>
        
        <!-- Time Control Panel -->
        <div class="climate-control-panel">
            <div class="time-slider-container">
                <span class="time-slider-label">Timeline</span>
                <input type="range" class="time-slider" id="time-slider" min="2009" max="2023" value="2009" step="1">
            </div>
            <button class="play-button" id="play-btn" onclick="togglePlay()">▶</button>
            <div class="year-display-large" id="control-year">2009</div>
        </div>
    `;
    
    document.body.appendChild(container);
    
    // Setup slider
    const slider = document.getElementById('time-slider');
    slider.min = Math.min(...ClimateSystem.availableYears);
    slider.max = Math.max(...ClimateSystem.availableYears);
    slider.value = ClimateSystem.currentYear;
    
    slider.addEventListener('input', (e) => {
        const year = parseInt(e.target.value);
        updateClimateDisplay(year);
    });
    
    // Hide loading after initialization
    setTimeout(() => {
        document.getElementById('climate-loading').classList.add('hidden');
    }, 1500);
}

async function updateClimateDisplay(year) {
    if (!ClimateSystem.availableYears.includes(year)) {
        console.warn(`Year ${year} not available in dataset`);
        return;
    }
    
    ClimateSystem.currentYear = year;
    
    // Update UI immediately for responsiveness
    document.getElementById('globe-year').textContent = year;
    document.getElementById('control-year').textContent = year;
    document.getElementById('time-slider').value = year;
    
    try {
        // Fetch climate data
        const response = await fetch(`/get_climate_intelligence?year=${year}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            ClimateSystem.data = data;
            renderClimateData(data);
        }
    } catch (error) {
        console.error('Failed to fetch climate data:', error);
    }
}

function renderClimateData(data) {
    // Update Globe
    if (data.globe && Object.keys(data.globe).length > 0) {
        renderGlobe(data.globe);
    }
    
    // Update Trend
    if (data.trend && Object.keys(data.trend).length > 0) {
        renderTrend(data.trend);
    }
    
    // Update Stats
    if (data.stats) {
        document.getElementById('stat-mean').textContent = data.stats.mean?.toFixed(2) || '--';
        document.getElementById('stat-std').textContent = data.stats.std?.toFixed(2) || '--';
        document.getElementById('stat-max').textContent = data.stats.max?.toFixed(2) || '--';
        document.getElementById('stat-min').textContent = data.stats.min?.toFixed(2) || '--';
    }
    
    // Update Anomaly
    updateAnomalyDisplay(data.anomaly);
    
    // Update Event
    updateEventDisplay(data.event);
}

function renderGlobe(globeData) {
    const container = document.getElementById('climate-globe-plot');
    
    if (!container) return;
    
    // Destroy previous plot if exists
    if (ClimateSystem.globePlot) {
        Plotly.react(container, globeData.data, globeData.layout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        });
    } else {
        ClimateSystem.globePlot = Plotly.newPlot(container, globeData.data, globeData.layout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        });
    }
    
    // Start auto-rotation
    startGlobeRotation();
}

function startGlobeRotation() {
    // Clear existing rotation
    if (ClimateSystem.autoRotateInterval) {
        clearInterval(ClimateSystem.autoRotateInterval);
    }
    
    const container = document.getElementById('climate-globe-plot');
    if (!container) return;
    
    let rotation = 80; // Start at India
    ClimateSystem.autoRotateInterval = setInterval(() => {
        rotation += 0.3;
        Plotly.relayout(container, {
            'geo.projection.rotation.lon': rotation
        });
    }, 50);
}

function renderTrend(trendData) {
    const container = document.getElementById('climate-trend-plot');
    
    if (!container) return;
    
    if (ClimateSystem.trendPlot) {
        Plotly.react(container, trendData.data, trendData.layout, {
            responsive: true,
            displayModeBar: false,
            displaylogo: false
        });
    } else {
        ClimateSystem.trendPlot = Plotly.newPlot(container, trendData.data, trendData.layout, {
            responsive: true,
            displayModeBar: false,
            displaylogo: false
        });
    }
}

function updateAnomalyDisplay(anomaly) {
    const panel = document.getElementById('anomaly-panel');
    const message = document.getElementById('anomaly-message');
    const zscore = document.getElementById('anomaly-zscore');
    const statusIndicator = document.getElementById('globe-status');
    const statusText = document.getElementById('globe-status-text');
    
    if (!anomaly) return;
    
    // Update panel styling
    panel.className = 'climate-anomaly-panel';
    if (anomaly.severity === 'critical') {
        panel.classList.add('critical');
        statusIndicator.className = 'status-indicator status-critical';
    } else if (anomaly.severity === 'warning') {
        panel.classList.add('warning');
        statusIndicator.className = 'status-indicator status-warning';
    } else {
        statusIndicator.className = 'status-indicator status-normal';
    }
    
    // Update text
    message.textContent = anomaly.message || 'No anomaly detected';
    zscore.textContent = `Z-Score: ${anomaly.z_score?.toFixed(2) || 'N/A'}`;
    statusText.textContent = anomaly.type === 'normal' ? 'Normal' : 'Alert';
}

function updateEventDisplay(event) {
    const panel = document.getElementById('event-panel');
    const description = document.getElementById('event-description');
    const confidence = document.getElementById('event-confidence');
    const recommendation = document.getElementById('event-recommendation');
    
    if (!event) return;
    
    // Update panel styling based on event type
    panel.className = 'climate-event-panel';
    if (event.type === 'monsoon_surge') {
        panel.classList.add('monsoon');
    } else if (event.type === 'cyclonic_buildup') {
        panel.classList.add('cyclone');
    } else if (event.type === 'dry_phase') {
        panel.classList.add('dry');
    }
    
    // Update content
    description.textContent = event.description || 'No events detected';
    confidence.textContent = `Confidence: ${(event.confidence * 100)?.toFixed(0) || 0}%`;
    recommendation.textContent = event.recommendation || '';
}

function togglePlay() {
    const btn = document.getElementById('play-btn');
    
    if (ClimateSystem.isPlaying) {
        stopPlayback();
        btn.textContent = '▶';
        btn.classList.remove('playing');
    } else {
        startPlayback();
        btn.textContent = '⏸';
        btn.classList.add('playing');
    }
}

function startPlayback() {
    ClimateSystem.isPlaying = true;
    
    ClimateSystem.playInterval = setInterval(() => {
        const currentIndex = ClimateSystem.availableYears.indexOf(ClimateSystem.currentYear);
        const nextIndex = (currentIndex + 1) % ClimateSystem.availableYears.length;
        const nextYear = ClimateSystem.availableYears[nextIndex];
        
        updateClimateDisplay(nextYear);
    }, ClimateSystem.playSpeed);
}

function stopPlayback() {
    ClimateSystem.isPlaying = false;
    
    if (ClimateSystem.playInterval) {
        clearInterval(ClimateSystem.playInterval);
        ClimateSystem.playInterval = null;
    }
}

function closeClimateIntelligence() {
    // Stop playback
    stopPlayback();
    
    // Stop globe rotation
    if (ClimateSystem.autoRotateInterval) {
        clearInterval(ClimateSystem.autoRotateInterval);
    }
    
    // Remove container
    const container = document.getElementById('climate-intelligence-container');
    if (container) {
        container.style.opacity = '0';
        container.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            container.remove();
        }, 500);
    }
}

window.ClimateSystem = ClimateSystem;
window.initClimateIntelligence = initClimateIntelligence;
window.updateClimateDisplay = updateClimateDisplay;
window.togglePlay = togglePlay;
window.closeClimateIntelligence = closeClimateIntelligence;

// Auto-initialize when script loads (optional)
// Uncomment below to auto-launch:
// document.addEventListener('DOMContentLoaded', initClimateIntelligence);
