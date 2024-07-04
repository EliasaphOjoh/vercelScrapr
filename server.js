const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware to enable CORS
app.use(cors());

// Serve static files from the 'build' directory (React app)
app.use(express.static(path.join(__dirname, 'build')));

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Function to get the first image from a directory and convert it to base64
const getFirstImageFromDirectory = (dirPath) => {
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
        const ext = path.extname(file).toLowerCase();
        if (['.png', '.jpg', '.jpeg', '.gif'].includes(ext)) {
            const filePath = path.join(dirPath, file);
            const bitmap = fs.readFileSync(filePath);
            return `data:image/${ext.slice(1)};base64,${Buffer.from(bitmap).toString('base64')}`;
        }
    }
    return 'No image';
};

// API endpoint to fetch articles
app.get('/api/articles', (req, res) => {
    const articlesDir = path.join(__dirname, 'articles');
    fs.readdir(articlesDir, (err, files) => {
        if (err) {
            console.error('Failed to read articles directory:', err);
            return res.status(500).json({ error: 'Failed to read articles directory' });
        }

        const articles = files.map((file) => {
            const filePath = path.join(articlesDir, file);
            const content = fs.readFileSync(filePath, 'utf8');

            const titleMatch = content.match(/<h1>(.*?)<\/h1>/);
            const briefMatch = content.match(/<p>(.*?)<\/p>/);

            // Get the first image from the corresponding folder
            const imageDir = path.join(__dirname, 'images', path.basename(file, path.extname(file)));
            const image = fs.existsSync(imageDir) ? getFirstImageFromDirectory(imageDir) : 'No image';

            return {
                title: titleMatch ? titleMatch[1] : 'No title',
                brief: briefMatch ? briefMatch[1] : 'No brief',
                image: image,
                filename: file
            };
        });

        console.log('Articles fetched:', articles); // Log articles for debugging
        res.json(articles);
    });
});

// Endpoint to serve the main React app
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Catch-all handler to serve React app for any other route
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
