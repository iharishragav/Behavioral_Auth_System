
// dashboard.js
const riskScoreElement = document.getElementById('risk-score');
const alertContainer = document.getElementById('alert-container');

// In a real application, you would get this from a secure source.
const AUTH_TOKEN = 'your-secret-auth-token';

const userId = prompt("Please enter your username", "test-user");

window.socket = new WebSocket('ws://localhost:8765');
console.log('WebSocket initial state:', window.socket.readyState);

window.socket.onopen = () => {
    console.log('WebSocket connection established. State:', window.socket.readyState);
    
    // Send the authentication token as the first message.
    window.socket.send(JSON.stringify({ token: AUTH_TOKEN }));

    // Send a message to authenticate the user
    socket.send(JSON.stringify({
        type: 'user_authentication',
        userId: userId,
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
