
// Global Variables
let currentMode = 'strict';
let users = [];
let filteredUsers = [];

// API Configuration (schimbă cu URL-ul tău real)
const API_BASE = window.location.origin;

// Add this right after your global variables at the top of script.js
console.log('Chart.js loaded:', typeof Chart !== 'undefined');
console.log('DOM loaded:', document.readyState);

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    showLoading(true);
    
    // Initialize all components
    initializeTabs();
    initializeSliders();
    initializeEventListeners();
    loadMockData();
    initializeCharts();
    startRealTimeClock();
    
    // Hide loading after initialization
    setTimeout(() => {
        showLoading(false);
    }, 2000);
});

// ========================================
// TAB NAVIGATION
// ========================================

function initializeTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
       
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
       
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
       
    if (tabName === 'analytics') {
        setTimeout(initializeAnalyticsCharts, 100);
    }
}

   
   
// ========================================

function loadMockData() {
    users = [
        {
            id: 1,
            username: "ToxicUser123",
            discriminator: "1234",
            riskScore: 85,
            riskLevel: "high",
            totalMessages: 156,
            toxicMessages: 23,
            positiveMessages: 12,
            lastSeen: "2025-06-26T10:30:00",
            joinDate: "2024-01-15",
            infractions: [
                {
                    type: "Limbaj ofensator",
                    message: "Du-te naibii de aici!",
                    date: "2025-06-25T15:45:00",
                    action: "Avertisment automat + feedback educațional",
                    severity: "medium"
                },
                {
                    type: "Harassment",
                    message: "[mesaj șters pentru conținut grav ofensator]",
                    date: "2025-06-24T09:20:00",
                    action: "Timeout 24h + intervenție moderator",
                    severity: "severe"
                },
                {
                    type: "Spam",
                    message: "gg gg gg gg gg gg gg gg gg gg",
                    date: "2025-06-23T14:20:00",
                    action: "Avertisment pentru spam repetat",
                    severity: "low"
                }
            ],
            progressData: [45, 52, 48, 65, 70, 68, 72]
        },
        {
            id: 2,
            username: "PositiveHelper",
            discriminator: "5678",
            riskScore: 15,
            riskLevel: "low",
            totalMessages: 342,
            toxicMessages: 2,
            positiveMessages: 89,
            lastSeen: "2025-06-26T11:15:00",
            joinDate: "2023-08-10",
            infractions: [
                {
                    type: "Spam minor",
                    message: "wow wow wow awesome!",
                    date: "2025-05-15T10:30:00",
                    action: "Avertisment preventiv",
                    severity: "low"
                }
            ],
            progressData: [85, 88, 92, 90, 95, 93, 96]
        },
        {
            id: 3,
            username: "CasualGamer",
            discriminator: "9999",
            riskScore: 45,
            riskLevel: "medium",
            totalMessages: 234,
            toxicMessages: 8,
            positiveMessages: 34,
            lastSeen: "2025-06-26T08:45:00",
            joinDate: "2024-03-22",
            infractions: [
                {
                    type: "Limbaj nepotrivit",
                    message: "Ce dracu' faci aici?",
                    date: "2025-06-23T16:30:00",
                    action: "Feedback educațional despre limbajul potrivit",
                    severity: "medium"
                },
                {
                    type: "Off-topic",
                    message: "Cine vrea să se joace Fortnite?",
                    date: "2025-06-20T12:15:00",
                    action: "Redirecționare către canalul potrivit",
                    severity: "low"
                }
            ],
            progressData: [60, 58, 65, 62, 68, 70, 72]
        },
        {
            id: 4,
            username: "NewbieUser",
            discriminator: "0001",
            riskScore: 25,
            riskLevel: "low",
            totalMessages: 45,
            toxicMessages: 1,
            positiveMessages: 8,
            lastSeen: "2025-06-26T12:00:00",
            joinDate: "2025-06-20",
            infractions: [],
            progressData: [70, 75, 80, 78, 82, 85, 88]
        },
        {
            id: 5,
            username: "ProblematicMember",
            discriminator: "6666",
            riskScore: 92,
            riskLevel: "high",
            totalMessages: 89,
            toxicMessages: 34,
            positiveMessages: 3,
            lastSeen: "2025-06-25T22:15:00",
            joinDate: "2025-05-01",
            infractions: [
                {
                    type: "Amenințări",
                    message: "[conținut șters - amenințări grave]",
                    date: "2025-06-25T20:30:00",
                    action: "Ban 7 zile + raport la autorități",
                    severity: "severe"
                },
                {
                    type: "Discriminare",
                    message: "[conținut șters - limbaj discriminatoriu]",
                    date: "2025-06-24T18:45:00",
                    action: "Timeout 48h + sesiune educațională obligatorie",
                    severity: "severe"
                },
                {
                    type: "Trolling",
                    message: "Haha toți sunteți prost",
                    date: "2025-06-23T15:20:00",
                    action: "Avertisment final",
                    severity: "medium"
                }
            ],
            progressData: [95, 90, 88, 92, 94, 96, 98]
        }
    ];
    
    filteredUsers = [...users];
    renderUsers();
    updateChartsWithRealData();
}

async function loadRealUsers() {
    try {
        const response = await fetch(`${API_BASE}/api/users/risk-analysis`);
        const data = await response.json();
        users = data.users;
        filteredUsers = [...users];
        renderUsers();
    } catch (error) {
        console.error('Error loading users:', error);
        loadMockData(); // Fallback la date mock
    }
}

// ========================================
// USER INTERFACE RENDERING
// ========================================

function renderUsers() {
    const grid = document.getElementById('usersGrid');
    
    if (filteredUsers.length === 0) {
        grid.innerHTML = '<div class="text-center" style="grid-column: 1/-1; padding: 2rem;">Nu s-au găsit utilizatori.</div>';
        return;
    }
    
    grid.innerHTML = filteredUsers.map(user => `
        <div class="user-card ${user.riskLevel}-risk" onclick="openUserModal(${user.id})" style="cursor: pointer;">
            <div class="user-header">
                <div class="user-name">${user.username}#${user.discriminator}</div>
                <div class="risk-score ${user.riskLevel}">${user.riskScore}%</div>
            </div>
            
            <div class="user-stats">
                <div class="user-stat">
                    <span>Mesaje totale:</span>
                    <strong>${user.totalMessages}</strong>
                </div>
                <div class="user-stat">
                    <span>Mesaje toxice:</span>
                    <strong>${user.toxicMessages}</strong>
                </div>
                <div class="user-stat">
                    <span>Mesaje pozitive:</span>
                    <strong>${user.positiveMessages}</strong>
                </div>
                <div class="user-stat">
                    <span>Ultima activitate:</span>
                    <strong>${formatTimeAgo(user.lastSeen)}</strong>
                </div>
            </div>
            
            <div class="user-actions">
                <button class="btn-sm btn-primary" onclick="event.stopPropagation(); viewUserHistory(${user.id})">
                    <i class="fas fa-history"></i> Istoric
                </button>
                <button class="btn-sm btn-secondary" onclick="event.stopPropagation(); sendWarning(${user.id})">
                    <i class="fas fa-exclamation-triangle"></i> Avertisment
                </button>
            </div>
        </div>
    `).join('');
}

// ========================================
// USER MODAL FUNCTIONALITY
// ========================================

function openUserModal(userId) {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    document.getElementById('modalUserName').textContent = `${user.username}#${user.discriminator}`;
    
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
            <div>
                <h4 style="margin-bottom: 1rem; color: #1f2937;">📊 Statistici Generale</h4>
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px;">
                    <p><strong>Scor de risc:</strong> <span class="risk-score ${user.riskLevel}" style="margin-left: 0.5rem;">${user.riskScore}%</span></p>
                    <p><strong>Total mesaje:</strong> ${user.totalMessages}</p>
                    <p><strong>Mesaje toxice:</strong> ${user.toxicMessages} (${((user.toxicMessages/user.totalMessages)*100).toFixed(1)}%)</p>
                    <p><strong>Mesaje pozitive:</strong> ${user.positiveMessages} (${((user.positiveMessages/user.totalMessages)*100).toFixed(1)}%)</p>
                    <p><strong>Data înrolării:</strong> ${formatDate(user.joinDate)}</p>
                    <p><strong>Ultima activitate:</strong> ${formatTimeAgo(user.lastSeen)}</p>
                </div>
            </div>
            
            <div>
                <h4 style="margin-bottom: 1rem; color: #1f2937;">📈 Progres în Timp</h4>
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px;">
                    <canvas id="userProgressChart" width="300" height="200"></canvas>
                </div>
            </div>
        </div>
        
        <div>
            <h4 style="margin-bottom: 1rem; color: #1f2937;">🚨 Istoricul Infracțiunilor (${user.infractions.length})</h4>
            <div class="infractions-list">
                ${user.infractions.length > 0 ? user.infractions.map(infraction => `
                    <div class="infraction-item ${infraction.severity === 'severe' ? 'severe' : ''}">
                        <div class="infraction-header">
                            <div class="infraction-type">
                                ${infraction.severity === 'severe' ? '🚨' : infraction.severity === 'medium' ? '⚠️' : '💛'} 
                                ${infraction.type}
                            </div>
                            <div class="infraction-date">${formatDate(infraction.date)}</div>
                        </div>
                        <div class="infraction-message">"${infraction.message}"</div>
                        <div class="infraction-action">✅ ${infraction.action}</div>
                    </div>
                `).join('') : '<p style="text-align: center; color: #64748b; padding: 2rem;">🎉 Nu sunt infracțiuni înregistrate! Utilizator exemplar.</p>'}
            </div>
        </div>
        
        <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 2px solid #e2e8f0;">
            <h4 style="margin-bottom: 1rem; color: #1f2937;">🛠️ Acțiuni Rapide</h4>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <button class="btn-primary" onclick="sendEducationalMessage(${user.id})">
                    <i class="fas fa-graduation-cap"></i> Trimite Mesaj Educațional
                </button>
                <button class="btn-secondary" onclick="adjustUserRisk(${user.id})">
                    <i class="fas fa-sliders-h"></i> Ajustează Risc Manual
                </button>
                <button class="btn-secondary" onclick="exportUserData(${user.id})">
                    <i class="fas fa-download"></i> Export Date
                </button>
                ${user.riskLevel === 'high' ? `
                    <button class="btn-secondary" style="background: #ef4444;" onclick="initiateTimeout(${user.id})">
                        <i class="fas fa-ban"></i> Timeout Utilizator
                    </button>
                ` : ''}
            </div>
        </div>
    `;
    const modal = document.getElementById('userModal');
    modal.classList.remove('hidden');

    setTimeout(() => initializeUserProgressChart(user), 100);

}

function closeUserModal() {
    document.getElementById('userModal').classList.add('hidden');
}

// ========================================
// CHARTS INITIALIZATION
// ========================================

function initializeCharts() {
    // Activity Chart with more realistic data
    const activityCtx = document.getElementById('activityChart').getContext('2d');
    new Chart(activityCtx, {
        type: 'line',
        data: {
            labels: ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'],
            datasets: [{
                label: 'Mesaje Totale',
                data: [120, 190, 300, 500, 200, 300, 450],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#667eea',
                pointBorderWidth: 2,
                pointRadius: 6
            }, {
                label: 'Mesaje Toxice',
                data: [5, 8, 12, 15, 8, 10, 18],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#ef4444',
                pointBorderWidth: 2,
                pointRadius: 6
            }, {
                label: 'Mesaje Pozitive',
                data: [45, 67, 89, 156, 78, 123, 134],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#10b981',
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#667eea',
                    borderWidth: 1
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            elements: {
                point: {
                    hoverRadius: 8
                }
            }
        }
    });

    // Enhanced Risk Distribution Chart
    const riskCtx = document.getElementById('riskChart').getContext('2d');
    new Chart(riskCtx, {
        type: 'doughnut',
        data: {
            labels: ['Risc Mic (0-39%)', 'Risc Mediu (40-69%)', 'Risc Mare (70-100%)'],
            datasets: [{
                data: [65, 25, 10],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)', 
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed * 100) / total).toFixed(1);
                            return `${context.label}: ${context.parsed} utilizatori (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateChartsWithRealData() {
    const totalMessages = users.reduce((sum, user) => sum + user.totalMessages, 0);
    const toxicMessages = users.reduce((sum, user) => sum + user.toxicMessages, 0);
    const positiveMessages = users.reduce((sum, user) => sum + user.positiveMessages, 0);

    const riskDistribution = {
        low: users.filter(user => user.riskLevel === 'low').length,
        medium: users.filter(user => user.riskLevel === 'medium').length,
        high: users.filter(user => user.riskLevel === 'high').length
    };

    document.getElementById('total-messages').textContent = totalMessages;
    document.getElementById('positive-messages').textContent = positiveMessages;
    document.getElementById('toxic-messages').textContent = toxicMessages;
    document.getElementById('positive-rate').textContent = ((positiveMessages/totalMessages)*100).toFixed(1) + '%';
    document.getElementById('toxic-rate').textContent = ((toxicMessages/totalMessages)*100).toFixed(1) + '%';
    
    console.log('Charts updated with real data:', { totalMessages, toxicMessages, positiveMessages, riskDistribution });
}

function initializeAnalyticsCharts() {
    const toxicityTrendCtx = document.getElementById('toxicityTrendChart').getContext('2d');
    new Chart(toxicityTrendCtx, {
        type: 'line',
        data: {
            labels: ['Ian', 'Feb', 'Mar', 'Apr', 'Mai', 'Iun'],
            datasets: [{
                label: 'Rata Toxicității (%)',
                data: [3.2, 2.8, 2.1, 1.9, 1.7, 1.5],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5
                }
            }
        }
    });

    const interventionCtx = document.getElementById('interventionChart').getContext('2d');
    new Chart(interventionCtx, {
        type: 'bar',
        data: {
            labels: ['Feedback Educațional', 'Avertismente', 'Timeout-uri', 'Ban-uri'],
            datasets: [{
                label: 'Rata de Succes (%)',
                data: [87, 72, 65, 45],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    const categoriesCtx = document.getElementById('categoriesChart').getContext('2d');
    new Chart(categoriesCtx, {
        type: 'doughnut',
        data: {
            labels: ['Limbaj ofensator', 'Spam', 'Harassment', 'Trolling', 'Alte'],
            datasets: [{
                data: [35, 25, 20, 15, 5],
                backgroundColor: ['#ef4444', '#f59e0b', '#8b5cf6', '#06b6d4', '#64748b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });


    const progressCtx = document.getElementById('progressChart').getContext('2d');
    new Chart(progressCtx, {
        type: 'bar',
        data: {
            labels: ['Săpt 1', 'Săpt 2', 'Săpt 3', 'Săpt 4'],
            datasets: [{
                label: 'Utilizatori Îmbunătățiți',
                data: [12, 18, 25, 32],
                backgroundColor: '#10b981',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function initializeUserProgressChart(user) {
    const ctx = document.getElementById('userProgressChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Săpt 1', 'Săpt 2', 'Săpt 3', 'Săpt 4', 'Săpt 5', 'Săpt 6', 'Săpt 7'],
            datasets: [{
                label: 'Scor Comportament',
                data: user.progressData,
                borderColor: user.riskLevel === 'high' ? '#ef4444' : user.riskLevel === 'medium' ? '#f59e0b' : '#10b981',
                backgroundColor: `rgba(${user.riskLevel === 'high' ? '239, 68, 68' : user.riskLevel === 'medium' ? '245, 158, 11' : '16, 185, 129'}, 0.1)`,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// ========================================
// SETTINGS MANAGEMENT
// ========================================

function initializeSliders() {
    const toxicitySlider = document.getElementById('toxicityThreshold');
    const autoActionSlider = document.getElementById('autoActionThreshold');
    
    toxicitySlider.addEventListener('input', function() {
        document.getElementById('toxicityValue').textContent = this.value + '%';
    });
    
    autoActionSlider.addEventListener('input', function() {
        document.getElementById('autoActionValue').textContent = this.value + '%';
    });

    // Mode selector
    const modeOptions = document.querySelectorAll('.mode-option');
    modeOptions.forEach(option => {
        option.addEventListener('click', function() {
            modeOptions.forEach(o => o.classList.remove('active'));
            this.classList.add('active');
            currentMode = this.dataset.mode;
            
            // Update sliders based on mode
            if (currentMode === 'strict') {
                toxicitySlider.value = 50;
                autoActionSlider.value = 70;
            } else {
                toxicitySlider.value = 80;
                autoActionSlider.value = 90;
            }
            
            document.getElementById('toxicityValue').textContent = toxicitySlider.value + '%';
            document.getElementById('autoActionValue').textContent = autoActionSlider.value + '%';
        });
    });
}

function saveSettings() {
    const settings = {
        mode: currentMode,
        toxicityThreshold: document.getElementById('toxicityThreshold').value,
        autoActionThreshold: document.getElementById('autoActionThreshold').value,
        autoModeration: document.getElementById('autoModeration').checked,
        educationalFeedback: document.getElementById('educationalFeedback').checked,
        rewardSystem: document.getElementById('rewardSystem').checked,
        realTimeAlerts: document.getElementById('realTimeAlerts').checked
    };
    
    console.log('Setări salvate:', settings);
    showNotification('✅ Setările au fost salvate cu succes!', 'success');
    
    // Pentru integrare cu API real:
    /*
    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        if (response.ok) {
            showNotification('✅ Setările au fost salvate cu succes!', 'success');
        } else {
            throw new Error('Eroare la salvare');
        }
    } catch (error) {
        showNotification('❌ Eroare la salvarea setărilor!', 'error');
    }
    */
}

function resetSettings() {
    if (confirm('Ești sigur că vrei să resetezi toate setările la valorile implicite?')) {
        document.getElementById('toxicityThreshold').value = 70;
        document.getElementById('autoActionThreshold').value = 85;
        document.getElementById('toxicityValue').textContent = '70%';
        document.getElementById('autoActionValue').textContent = '85%';
        
        document.querySelectorAll('.mode-option').forEach(o => o.classList.remove('active'));
        document.querySelector('[data-mode="strict"]').classList.add('active');
        currentMode = 'strict';
        
        document.getElementById('autoModeration').checked = true;
        document.getElementById('educationalFeedback').checked = true;
        document.getElementById('rewardSystem').checked = true;
        document.getElementById('realTimeAlerts').checked = true;
        
        showNotification('✅ Setările au fost resetate!', 'success');
    }
}

// ========================================
// USER ACTIONS
// ========================================

function viewUserHistory(userId) {
    openUserModal(userId);
}

function sendWarning(userId) {
    const user = users.find(u => u.id === userId);
    showNotification(`⚠️ Avertisment trimis către ${user.username}#${user.discriminator}`, 'warning');
    
    // Pentru integrare cu Discord API:
    /*
    try {
        await fetch(`${API_BASE}/api/discord/warning`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: user.id, 
                message: 'Avertisment pentru comportament neadecvat' 
            })
        });
    } catch (error) {
        console.error('Error sending warning:', error);
    }
    */
}

function sendEducationalMessage(userId) {
    const user = users.find(u => u.id === userId);
    showNotification(`📚 Mesaj educațional trimis către ${user.username}#${user.discriminator}`, 'info');
    
    // Pentru integrare cu sistemul AI:
    /*
    try {
        await fetch(`${API_BASE}/api/education/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: user.id, 
                riskLevel: user.riskLevel,
                infractions: user.infractions 
            })
        });
    } catch (error) {
        console.error('Error sending educational message:', error);
    }
    */
}

function adjustUserRisk(userId) {
    const user = users.find(u => u.id === userId);
    const newRisk = prompt(`Introdu noul scor de risc pentru ${user.username} (0-100):`, user.riskScore);
    
    if (newRisk !== null && !isNaN(newRisk) && newRisk >= 0 && newRisk <= 100) {
        user.riskScore = parseInt(newRisk);
        user.riskLevel = newRisk >= 70 ? 'high' : newRisk >= 40 ? 'medium' : 'low';
        renderUsers();
        showNotification('📊 Scorul de risc a fost actualizat!', 'success');
        
        // Pentru sincronizare cu baza de date:
        /*
        await fetch(`${API_BASE}/api/users/${userId}/risk`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ riskScore: newRisk })
        });
        */
    }
}

function exportUserData(userId) {
    const user = users.find(u => u.id === userId);
    const data = JSON.stringify(user, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `user_${user.username}_data.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification(`💾 Date exportate pentru ${user.username}`, 'success');
}

function initiateTimeout(userId) {
    const user = users.find(u => u.id === userId);
    const duration = prompt('Durata timeout (în ore):', '24');
    
    if (duration !== null && !isNaN(duration) && duration > 0) {
        showNotification(`⏱️ Timeout ${duration}h aplicat pentru ${user.username}`, 'warning');
        
        // Pentru integrare cu Discord API:
        /*
        await fetch(`${API_BASE}/api/discord/timeout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                userId: user.id, 
                duration: parseInt(duration) * 3600 // Convert to seconds
            })
        });
        */
    }
}

// ========================================
// EVENT LISTENERS
// ========================================

function initializeEventListeners() {
    // Search functionality
    document.getElementById('userSearch').addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        filteredUsers = users.filter(user => 
            user.username.toLowerCase().includes(searchTerm) ||
            user.discriminator.includes(searchTerm)
        );
        renderUsers();
    });

    // Risk filter
    document.getElementById('riskFilter').addEventListener('change', function() {
        const riskLevel = this.value;
        if (riskLevel) {
            filteredUsers = users.filter(user => user.riskLevel === riskLevel);
        } else {
            filteredUsers = [...users];
        }
        renderUsers();
    });

    // Server filter
    document.getElementById('serverFilter').addEventListener('change', function() {
        const serverId = this.value;
        // Aici poți filtra după server dacă ai acea proprietate în datele utilizatorilor
        console.log('Filter by server:', serverId);
    });

    // Close modal when clicking outside
    document.getElementById('userModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeUserModal();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeUserModal();
        }
    });
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ro-RO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTimeAgo(dateString) {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    
    if (diffMinutes < 1) return 'acum';
    if (diffMinutes < 60) return `${diffMinutes}m`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h`;
    if (diffMinutes < 10080) return `${Math.floor(diffMinutes / 1440)}z`;
    return formatDate(dateString);
}

function startRealTimeClock() {
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('ro-RO');
        document.getElementById('current-time').textContent = timeString;
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

function showNotification(message, type = 'info') {
    // Creează element de notificare
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        max-width: 400px;
        font-weight: 600;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animație de intrare
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove după 4 secunde
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// ========================================
// API INTEGRATION FUNCTIONS
// ========================================

// Funcții pentru integrarea cu backend-ul tău
// Decomentează și adaptează după nevoile tale

/*
async function fetchUserStats(userId) {
    try {
        const response = await fetch(`${API_BASE}/api/users/${userId}/stats`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching user stats:', error);
        return null;
    }
}

async function updateUserSettings(userId, settings) {
    try {
        const response = await fetch(`${API_BASE}/api/users/${userId}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        return response.ok;
    } catch (error) {
        console.error('Error updating user settings:', error);
        return false;
    }
}

async function fetchServerAnalytics(serverId, timeframe = '7d') {
    try {
        const response = await fetch(`${API_BASE}/api/servers/${serverId}/analytics?timeframe=${timeframe}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching server analytics:', error);
        return null;
    }
}

async function sendDiscordMessage(channelId, message) {
    try {
        const response = await fetch(`${API_BASE}/api/discord/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channelId, message })
        });
        return response.ok;
    } catch (error) {
        console.error('Error sending Discord message:', error);
        return false;
    }
}

async function analyzeMessage(messageContent) {
    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: messageContent })
        });
        return await response.json();
    } catch (error) {
        console.error('Error analyzing message:', error);
        return null;
    }
}
*/

// ========================================
// REAL-TIME UPDATES (WebSocket)
// ========================================

// Pentru actualizări în timp real folosind WebSocket
/*
function initializeWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
    
    ws.onopen = function() {
        console.log('WebSocket connection established');
        showNotification('📡 Conexiune în timp real activă', 'success');
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'new_infraction':
                handleNewInfraction(data.payload);
                break;
            case 'user_update':
                handleUserUpdate(data.payload);
                break;
            case 'stats_update':
                handleStatsUpdate(data.payload);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    };
    
    ws.onclose = function() {
        console.log('WebSocket connection closed');
        showNotification('📡 Conexiune în timp real închisă', 'warning');
        
        // Reconnect după 5 secunde
        setTimeout(initializeWebSocket, 5000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        showNotification('❌ Eroare conexiune timp real', 'error');
    };
}

function handleNewInfraction(payload) {
    const { userId, infraction } = payload;
    const user = users.find(u => u.id === userId);
    
    if (user) {
        user.infractions.unshift(infraction);
        user.toxicMessages++;
        
        // Recalculează scorul de risc
        user.riskScore = calculateRiskScore(user);
        user.riskLevel = user.riskScore >= 70 ? 'high' : user.riskScore >= 40 ? 'medium' : 'low';
        
        renderUsers();
        showNotification(`🚨 Nouă infracțiune detectată pentru ${user.username}`, 'warning');
    }
}

function handleUserUpdate(payload) {
    const { userId, updates } = payload;
    const userIndex = users.findIndex(u => u.id === userId);
    
    if (userIndex !== -1) {
        users[userIndex] = { ...users[userIndex], ...updates };
        renderUsers();
    }
}

function handleStatsUpdate(payload) {
    // Actualizează statisticile generale
    document.getElementById('total-messages').textContent = payload.totalMessages.toLocaleString();
    document.getElementById('positive-messages').textContent = payload.positiveMessages.toLocaleString();
    document.getElementById('toxic-messages').textContent = payload.toxicMessages.toLocaleString();
    document.getElementById('active-users').textContent = payload.activeUsers.toLocaleString();
}

function calculateRiskScore(user) {
    const toxicityRate = (user.toxicMessages / user.totalMessages) * 100;
    const recentInfractions = user.infractions.filter(inf => {
        const infDate = new Date(inf.date);
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        return infDate > weekAgo;
    }).length;
    
    // Algoritmul tău de calculare a riscului
    let score = toxicityRate * 0.6 + recentInfractions * 5;
    
    // Ajustări pentru severitate
    const severeInfractions = user.infractions.filter(inf => inf.severity === 'severe').length;
    score += severeInfractions * 10;
    
    return Math.min(Math.round(score), 100);
}
*/

// ========================================
// INITIALIZATION
// ========================================

// Uncomment pentru a activa WebSocket în producție
// initializeWebSocket();

// Export functions pentru testing (opcional)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatDate,
        formatTimeAgo,
        showNotification,
        calculateRiskScore
    };
}