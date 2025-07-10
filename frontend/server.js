
// server.js
const express = require('express');
const path = require('path');

const app = express();
const port = 3000;

// Serve static files from the 'dashboard' directory
app.use(express.static(path.join(__dirname, 'dashboard')));
app.use('/collector', express.static(path.join(__dirname, 'collector')));

app.listen(port, () => {
    console.log(`Dashboard server listening at http://localhost:${port}`);
});
