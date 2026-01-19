import * as vscode from 'vscode';
import * as path from 'path';
import { TextDecoder } from 'util';

// Extensiones de archivos de código soportadas
const CODE_EXTENSIONS = [
    'js', 'ts', 'jsx', 'tsx', 'mjs', 'cjs',
    'py', 'pyw',
    'java', 'kt', 'kts', 'scala',
    'c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'hxx',
    'cs', 'go', 'rb', 'rake', 'php', 'swift', 'rs',
    'vue', 'svelte', 'html', 'htm', 'xml', 'xhtml',
    'css', 'scss', 'sass', 'less',
    'json', 'jsonc', 'yaml', 'yml', 'sql',
    'sh', 'bash', 'zsh', 'fish', 'ps1', 'psm1', 'psd1',
    'r', 'R', 'lua', 'pl', 'pm', 'ex', 'exs',
    'clj', 'cljs', 'dart', 'hs', 'erl', 'hrl',
    'ml', 'mli', 'fs', 'fsx', 'groovy', 'gradle'
];

// Tipo de decoración para destacar código encontrado
let highlightDecoration: vscode.TextEditorDecorationType;

export function activate(context: vscode.ExtensionContext) {
    console.log('Clipboard Code Finder está activo (Modo Chunk-Anchor Fuzzy)');

    // Crear decoración para destacar el código encontrado
    highlightDecoration = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(255, 255, 0, 0.4)',
        border: '2px solid #FFD700',
        borderRadius: '3px',
        isWholeLine: false
    });

    // Registrar el comando principal
    const findCodeCommand = vscode.commands.registerCommand(
        'clipboard-code-finder.findCode',
        findClipboardCode
    );

    // Registrar el proveedor de vista del panel lateral
    const provider = new ClipboardFinderViewProvider(context.extensionUri);
    const webviewProvider = vscode.window.registerWebviewViewProvider(
        'clipboardFinderView',
        provider
    );

    context.subscriptions.push(findCodeCommand, webviewProvider, highlightDecoration);
}

// Interfaz de resultados
interface SearchResult {
    uri: vscode.Uri;
    startPosition: vscode.Position;
    endPosition: vscode.Position;
    matchType: 'exact' | 'similar';
    similarity: number;
}

// --- LÓGICA DE BÚSQUEDA PRINCIPAL ---

async function findClipboardCode(): Promise<void> {
    try {
        const clipboardContent = await vscode.env.clipboard.readText();

        if (!clipboardContent || clipboardContent.trim().length === 0) {
            vscode.window.showWarningMessage('El portapapeles está vacío. Copia un fragmento de código primero.');
            return;
        }

        const searchText = clipboardContent.trim();
        const decoder = new TextDecoder('utf-8');

        // Mostrar progreso mientras busca
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Buscando código en el workspace...',
            cancellable: true
        }, async (progress, token) => {

            const globPattern = `**/*.{${CODE_EXTENSIONS.join(',')}}`;

            // Buscar archivos (solo URIs)
            const files = await vscode.workspace.findFiles(
                globPattern,
                '**/node_modules/**',
                5000
            );

            if (token.isCancellationRequested) return;

            progress.report({ message: `Analizando ${files.length} archivos...` });

            const results: SearchResult[] = [];
            let processedFiles = 0;

            // Procesar archivos
            for (const file of files) {
                if (token.isCancellationRequested) return;

                try {
                    // Usar fs.readFile para mejor rendimiento que openTextDocument
                    const contentValues = await vscode.workspace.fs.readFile(file);
                    const text = decoder.decode(contentValues);

                    // Buscar coincidencia en este archivo
                    const result = findBestMatch(text, searchText, file);
                    if (result) {
                        results.push(result);
                    }

                } catch (err) {
                    console.error(`Error leyendo ${file.fsPath}:`, err);
                }

                processedFiles++;
                if (processedFiles % 50 === 0) {
                    progress.report({
                        message: `Analizando ${processedFiles}/${files.length} archivos...`,
                        increment: (50 / files.length) * 100
                    });
                }
            }

            // Procesar resultados final
            if (results.length === 0) {
                vscode.window.showInformationMessage('No se encontró ninguna coincidencia cercana.');
                return;
            }

            // Ordenar por similitud
            results.sort((a, b) => b.similarity - a.similarity);

            // Navegar directamente al mejor resultado
            if (results.length > 0) {
                await navigateToResult(results[0]);
            }
        });

    } catch (error) {
        vscode.window.showErrorMessage(`Error al buscar: ${error}`);
    }
}

// --- ALGORITMO DE BÚSQUEDA ---

function findBestMatch(fileText: string, searchText: string, uri: vscode.Uri): SearchResult | null {
    // 1. Intento Exacto (Fase rápida)
    const exactIndex = fileText.indexOf(searchText);
    if (exactIndex !== -1) {
        return createSearchResult(uri, fileText, exactIndex, searchText.length, 'exact', 100);
    }

    // Preparar versiones normalizadas
    const normFile = normalizeCode(fileText);
    const normSearch = normalizeCode(searchText);

    if (normSearch.length < 5) return null; // Ignorar búsquedas muy cortas para fuzzy

    // 2. Intento Normalizado (Ignora espacios y mayúsculas, pero requiere secuencia exacta de caracteres)
    const normIndex = normFile.indexOf(normSearch);
    if (normIndex !== -1) {
        const realOffset = mapNormalizedToOriginal(fileText, normIndex);
        if (realOffset !== -1) {
            // Estimar longitud original
            const estimatedLen = estimateOriginalLength(fileText, realOffset, searchText);
            return createSearchResult(uri, fileText, realOffset, estimatedLen, 'similar', 99);
        }
    }

    // 3. Intento Difuso (Chunk-Anchor & Levenshtein)
    // Dividir la búsqueda en fragmentos y buscar anclas
    return findFuzzyMatch(fileText, normFile, searchText, normSearch, uri);
}

function findFuzzyMatch(originalText: string, normFile: string, originalSearch: string, normSearch: string, uri: vscode.Uri): SearchResult | null {
    // Si la búsqueda es pequeña, usar un solo bloque. Si es grande, dividir en hasta 4 chunks.
    const chunks = splitIntoChunks(normSearch, Math.max(2, Math.min(4, Math.floor(normSearch.length / 10))));

    let bestSim = 0;
    let bestResult: SearchResult | null = null;

    for (const chunk of chunks) {
        if (chunk.length < 4) continue;

        // Buscar cada ocurrencia del chunk en el archivo normalizado
        let pos = -1;
        while ((pos = normFile.indexOf(chunk, pos + 1)) !== -1) {
            // Encontramos un ancla.
            // La búsqueda completa debería empezar aproximadamente en: pos - offset_del_chunk
            const chunkOffsetInSearch = normSearch.indexOf(chunk);
            const startEst = Math.max(0, pos - chunkOffsetInSearch);

            // Definir una ventana de candidato extraída del archivo normalizado
            // Damos un margen de error del 30% en longitud
            const searchLen = normSearch.length;
            const windowLen = Math.floor(searchLen * 1.3);
            const candidateNorm = normFile.substring(startEst, startEst + windowLen);

            // Calcular similitud en esta ventana
            const sim = calculateSimilarity(normSearch, candidateNorm);

            if (sim > 70 && sim > bestSim) { // Umbral del 70%
                // Mapear al texto original
                const realStart = mapNormalizedToOriginal(originalText, startEst);
                if (realStart !== -1) {
                    const realEnd = mapNormalizedToOriginal(originalText, startEst + candidateNorm.length) || (realStart + originalSearch.length);
                    const len = Math.max(originalSearch.length, realEnd - realStart);

                    bestSim = sim;
                    bestResult = createSearchResult(uri, originalText, realStart, len, 'similar', sim);

                    if (sim > 95) return bestResult; // Si es muy bueno, retornar ya
                }
            }
        }
    }

    return bestResult;
}

// --- HELPERS ---

function createSearchResult(uri: vscode.Uri, fullText: string, startIndex: number, length: number, type: 'exact' | 'similar', similarity: number): SearchResult {
    // Asegurar límites
    startIndex = Math.max(0, Math.min(startIndex, fullText.length));
    const endIndex = Math.min(fullText.length, startIndex + length);

    // Convertir offsets a Posiciones VS Code
    const doc = new DummyDocument(fullText); // Helper simple para calcular posiciones
    return {
        uri: uri,
        startPosition: doc.positionAt(startIndex),
        endPosition: doc.positionAt(endIndex),
        matchType: type,
        similarity: Math.round(similarity)
    };
}

// Clase auxiliar ligera para evitar cargar vscode.TextDocument solo para calcular posiciones
class DummyDocument {
    private lines: number[];
    constructor(private text: string) {
        this.lines = [0];
        for (let i = 0; i < text.length; i++) {
            if (text[i] === '\n') this.lines.push(i + 1);
        }
    }
    positionAt(offset: number): vscode.Position {
        // Búsqueda binaria para encontrar la línea
        let low = 0, high = this.lines.length - 1;
        while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (this.lines[mid] <= offset) low = mid + 1;
            else high = mid - 1;
        }
        const line = low - 1;
        const char = offset - this.lines[line];
        return new vscode.Position(line, char);
    }
}

function normalizeCode(code: string): string {
    return code.replace(/[^a-z0-9]/gi, '').toLowerCase();
}

function splitIntoChunks(text: string, count: number): string[] {
    const len = Math.max(1, Math.floor(text.length / count));
    const chunks = [];
    for (let i = 0; i < text.length; i += len) {
        chunks.push(text.substring(i, i + len));
    }
    return chunks;
}

function mapNormalizedToOriginal(original: string, targetNormIndex: number): number {
    let normCounter = 0;
    for (let i = 0; i < original.length; i++) {
        const code = original.charCodeAt(i);
        // Chequeo rápido de alfanumérico (a-z, 0-9)
        if (
            (code >= 48 && code <= 57) || // 0-9
            (code >= 65 && code <= 90) || // A-Z
            (code >= 97 && code <= 122)   // a-z
        ) {
            if (normCounter === targetNormIndex) return i;
            normCounter++;
        }
    }
    return -1;
}

function estimateOriginalLength(text: string, startPos: number, originalSearch: string): number {
    // Estimación simple: longitud de búsqueda + 20% por formato
    return Math.min(text.length - startPos, Math.floor(originalSearch.length * 1.2));
}

function calculateSimilarity(s1: string, s2: string): number {
    // Levenshtein distance
    if (s1 === s2) return 100;
    if (s1.length === 0) return 0;
    if (s2.length === 0) return 0;

    const longer = s1.length > s2.length ? s1 : s2;
    const shorter = s1.length > s2.length ? s2 : s1;

    // Si la diferencia de longitud es muy grande, penalizar
    if (longer.length > shorter.length * 2) return 0;

    const costs = new Array();
    for (let i = 0; i <= s1.length; i++) {
        let lastValue = i;
        for (let j = 0; j <= s2.length; j++) {
            if (i == 0) costs[j] = j;
            else {
                if (j > 0) {
                    let newValue = costs[j - 1];
                    if (s1.charAt(i - 1) != s2.charAt(j - 1)) newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                    costs[j - 1] = lastValue;
                    lastValue = newValue;
                }
            }
        }
        if (i > 0) costs[s2.length] = lastValue;
    }

    const distance = costs[s2.length];
    return Math.max(0, 100 - (distance * 100 / longer.length));
}

async function navigateToResult(result: SearchResult): Promise<void> {
    const document = await vscode.workspace.openTextDocument(result.uri);
    const editor = await vscode.window.showTextDocument(document, {
        preview: false,
        selection: new vscode.Range(result.startPosition, result.endPosition)
    });

    editor.revealRange(
        new vscode.Range(result.startPosition, result.endPosition),
        vscode.TextEditorRevealType.InCenter
    );

    const range = new vscode.Range(result.startPosition, result.endPosition);
    editor.setDecorations(highlightDecoration, [range]);

    setTimeout(() => {
        editor.setDecorations(highlightDecoration, []);
    }, 4000);

    vscode.window.showInformationMessage(
        `✓ Código encontrado en ${path.basename(result.uri.fsPath)} (Similitud: ${result.similarity}%)`
    );
}

// Proveedor de vista (Preservando lógica de auto-cierre)
class ClipboardFinderViewProvider implements vscode.WebviewViewProvider {
    constructor(private readonly extensionUri: vscode.Uri) { }
    resolveWebviewView(webviewView: vscode.WebviewView, _context: vscode.WebviewViewResolveContext, _token: vscode.CancellationToken): void {
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this.getHtmlContent();
        webviewView.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'findCode') {
                await vscode.commands.executeCommand('clipboard-code-finder.findCode');
            }
        });
        webviewView.onDidChangeVisibility(() => {
            if (webviewView.visible) {
                setTimeout(() => {
                    vscode.commands.executeCommand('clipboard-code-finder.findCode');
                    // Cerrar sidebar automáticamente para "Efecto Fantasma"
                    vscode.commands.executeCommand('workbench.action.closeSidebar');
                }, 200);
            }
        });
    }
    private getHtmlContent(): string {
        return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{padding:10px;font-family:var(--vscode-font-family);color:var(--vscode-foreground);} .search-button{cursor:pointer;padding:10px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;}</style>
</head>
<body>
    <h3>🔎 Finder</h3>
    <p>Buscando...</p>
    <script>
        const vscode = acquireVsCodeApi();
        function findCode() { vscode.postMessage({ command: 'findCode' }); }
        window.addEventListener('load', () => findCode());
    </script>
</body>
</html>`;
    }
}

export function deactivate() {
    if (highlightDecoration) highlightDecoration.dispose();
}