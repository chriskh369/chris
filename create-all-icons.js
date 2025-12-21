const fs = require('fs');
const { createCanvas } = require('canvas');

function createIcon(size, maskable = false) {
    const canvas = createCanvas(size, size);
    const ctx = canvas.getContext('2d');

    // Create gradient background
    const gradient = ctx.createLinearGradient(0, 0, size, size);
    gradient.addColorStop(0, '#8b5cf6');
    gradient.addColorStop(0.5, '#ec4899');
    gradient.addColorStop(1, '#22d3ee');

    if (maskable) {
        // Maskable icons need full bleed background (no rounded corners)
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);

        // Draw graduation cap smaller (80% safe zone)
        drawCap(ctx, size, 0.65);
    } else {
        // Regular icon with rounded corners
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

        drawCap(ctx, size, 1.0);
    }

    return canvas.toBuffer('image/png');
}

function drawCap(ctx, size, scaleFactor) {
    ctx.fillStyle = 'white';
    const centerX = size / 2;
    const centerY = size / 2;
    const scale = (size / 512) * scaleFactor;

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
}

// Create all icons
console.log('Creating icons...');

// Regular icons (any)
fs.writeFileSync('icons/icon-192.png', createIcon(192, false));
console.log('Created icon-192.png');
fs.writeFileSync('icons/icon-512.png', createIcon(512, false));
console.log('Created icon-512.png');

// Maskable icons (with safe zone padding)
fs.writeFileSync('icons/icon-192-maskable.png', createIcon(192, true));
console.log('Created icon-192-maskable.png');
fs.writeFileSync('icons/icon-512-maskable.png', createIcon(512, true));
console.log('Created icon-512-maskable.png');

console.log('Done!');
