const express = require('express');
const cors = require('cors');
const fs = require('fs/promises');
const path = require('path');
const os = require('os');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Helper to get file stats safely
const getFileStats = async (filePath) => {
    try {
        const stats = await fs.stat(filePath);
        return {
            name: path.basename(filePath),
            path: filePath,
            isDirectory: stats.isDirectory(),
            size: stats.size,
            updatedAt: stats.mtime
        };
    } catch (err) {
        return null; // Ignore files we can't access
    }
};

// Endpoint to list files
app.get('/api/files', async (req, res) => {
    // Default to user's home directory or root if not specified
    const currentPath = req.query.path || os.homedir();

    try {
        const fileNames = await fs.readdir(currentPath);
        const fileStatPromises = fileNames.map(name =>
            getFileStats(path.join(currentPath, name))
        );

        const files = await Promise.all(fileStatPromises);
        const validFiles = files.filter(f => f !== null);

        // Sort: Directories first, then alphabetical
        validFiles.sort((a, b) => {
            if (a.isDirectory === b.isDirectory) {
                return a.name.localeCompare(b.name);
            }
            return a.isDirectory ? -1 : 1;
        });

        res.json({
            path: currentPath,
            files: validFiles
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Endpoint to read file content
app.get('/api/file', async (req, res) => {
    const filePath = req.query.path;
    if (!filePath) {
        return res.status(400).json({ error: 'Path is required' });
    }

    try {
        // Basic check to ensure we are reading a file
        const stats = await fs.stat(filePath);
        if (stats.isDirectory()) {
            return res.status(400).json({ error: 'Cannot read directory content as file' });
        }

        const content = await fs.readFile(filePath, 'utf-8');
        res.json({ content });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
