const fs = require('fs');
const { createCanvas } = require('canvas');

// Check if canvas is installed
try {
    require.resolve('canvas');
} catch(e) {
    console.log('Installing canvas package...');
    require('child_process').execSync('npm install canvas', { stdio: 'inherit' });
}

function createIcon(size) {
    const canvas = createCanvas(size, size);
    const ctx = canvas.getContext('2d');

    // Create gradient background
    const gradient = ctx.createLinearGradient(0, 0, size, size);
    gradient.addColorStop(0, '#8b5cf6');
    gradient.addColorStop(0.5, '#ec4899');
    gradient.addColorStop(1, '#22d3ee');

    // Draw rounded rectangle
    const radius = size * 0.2;
    ctx.beginPath();
    ctx.moveTo(radius, 0);
    ctx.lineTo(size - radius, 0);
    ctx.quadraticCurveTo(size, 0, size, radius);
    ctx.lineTo(size, size - radius);
    ctx.quadraticCurveTo(size, size, size - radius, size);
    ctx.lineTo(radius, size);
    ctx.quadraticCurveTo(0, size, 0, size - radius);
    ctx.lineTo(0, radius);
    ctx.quadraticCurveTo(0, 0, radius, 0);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw graduation cap
    ctx.fillStyle = 'white';
    const centerX = size / 2;
    const centerY = size / 2;
    const scale = size / 512;

    // Cap top
    ctx.beginPath();
    ctx.moveTo(centerX, centerY - 80 * scale);
    ctx.lineTo(centerX + 140 * scale, centerY);
    ctx.lineTo(centerX, centerY + 60 * scale);
    ctx.lineTo(centerX - 140 * scale, centerY);
    ctx.closePath();
    ctx.fill();

    // Cap band
    ctx.beginPath();
    ctx.moveTo(centerX - 100 * scale, centerY + 20 * scale);
    ctx.lineTo(centerX - 100 * scale, centerY + 80 * scale);
    ctx.lineTo(centerX, centerY + 120 * scale);
    ctx.lineTo(centerX + 100 * scale, centerY + 80 * scale);
    ctx.lineTo(centerX + 100 * scale, centerY + 20 * scale);
    ctx.fill();

    // Tassel
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 8 * scale;
    ctx.beginPath();
    ctx.moveTo(centerX + 120 * scale, centerY);
    ctx.lineTo(centerX + 120 * scale, centerY + 100 * scale);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(centerX + 120 * scale, centerY + 115 * scale, 15 * scale, 0, Math.PI * 2);
    ctx.fill();

    return canvas.toBuffer('image/png');
}

// Create icons
console.log('Creating icons...');
fs.writeFileSync('icons/icon-192.png', createIcon(192));
console.log('Created icon-192.png');
fs.writeFileSync('icons/icon-512.png', createIcon(512));
console.log('Created icon-512.png');
console.log('Done!');
