
// dashboard.js
const riskScoreElement = document.getElementById('risk-score');
const alertContainer = document.getElementById('alert-container');

window.socket = new WebSocket('ws://localhost:8765');
console.log('WebSocket initial state:', window.socket.readyState);

window.socket.onopen = () => {
    console.log('WebSocket connection established. State:', window.socket.readyState);
    console.log('WebSocket connection established');
    // Send a message to authenticate the user
    socket.send(JSON.stringify({
        type: 'user_authentication',
        userId: 'test-user',
        sessionId: 'session_' + Date.now()
    }));
    // Start data collection after authentication message is sent
    collector.startSendingData();
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'analysis_result') {
        updateDashboard(data);
    }
};

socket.onclose = (event) => {
    console.log('WebSocket connection closed. Code:', event.code, 'Reason:', event.reason);
    if (event.wasClean) {
        console.log('Connection closed cleanly');
    } else {
        console.log('Connection died');
    }
};

function updateDashboard(data) {
    riskScoreElement.textContent = data.riskScore.toFixed(2);
    
    if (data.alert) {
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${data.alert.level.toLowerCase()}`;
        alertElement.textContent = data.alert.message;
        alertContainer.appendChild(alertElement);
    }
}
