import * as vscode from 'vscode';
import * as path from 'path';

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

let highlightDecoration: vscode.TextEditorDecorationType;

interface SearchResult {
    uri: vscode.Uri;
    startPosition: vscode.Position;
    endPosition: vscode.Position;
    matchType: 'exact' | 'fuzzy';
    similarity: number;
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Clipboard Code Finder está activo (Modo Fuzzy)');

    highlightDecoration = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(255, 255, 0, 0.4)',
        border: '2px solid #FFD700',
        borderRadius: '3px',
        isWholeLine: false
    });

    const findCodeCommand = vscode.commands.registerCommand(
        'clipboard-code-finder.findCode',
        findClipboardCode
    );

    const provider = new ClipboardFinderViewProvider(context.extensionUri);
    const webviewProvider = vscode.window.registerWebviewViewProvider(
        'clipboardFinderView',
        provider
    );

    context.subscriptions.push(findCodeCommand, webviewProvider, highlightDecoration);
}

async function findClipboardCode(): Promise<void> {
    try {
        const clipboardContent = await vscode.env.clipboard.readText();

        if (!clipboardContent || clipboardContent.trim().length === 0) {
            vscode.window.showWarningMessage('El portapapeles está vacío.');
            return;
        }

        const searchText = clipboardContent.trim();

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Buscando código (Algoritmo Fuzzy)...',
            cancellable: true
        }, async (progress, token) => {

            const globPattern = `**/*.{${CODE_EXTENSIONS.join(',')}}`;

            // Limitamos a 2000 archivos para rendimiento, ya que el algoritmo fuzzy es más costoso
            const files = await vscode.workspace.findFiles(globPattern, '**/node_modules/**', 2000);

            if (token.isCancellationRequested) return;

            progress.report({ message: `Escaneando ${files.length} archivos...` });

            let bestGlobalResult: SearchResult | null = null;
            let processedFiles = 0;

            // Procesamiento de archivos
            for (const file of files) {
                if (token.isCancellationRequested) return;

                try {
                    const document = await vscode.workspace.openTextDocument(file);
                    const text = document.getText();

                    // 1. Intento de búsqueda exacta (Rápido)
                    const exactIndex = text.indexOf(searchText);
                    if (exactIndex !== -1) {
                        const result: SearchResult = {
                            uri: file,
                            startPosition: document.positionAt(exactIndex),
                            endPosition: document.positionAt(exactIndex + searchText.length),
                            matchType: 'exact',
                            similarity: 100
                        };
                        // Si encontramos exacto, es el mejor posible, terminamos.
                        bestGlobalResult = result;
                        break;
                    }

                    // 2. Búsqueda Difusa (Fuzzy) con Ventana Deslizante
                    // Solo ejecutamos si el archivo tiene un tamaño razonable para evitar bloqueos
                    if (text.length < 500000) {
                        const fuzzyMatch = findBestFuzzyMatch(text, searchText);

                        if (fuzzyMatch && fuzzyMatch.similarity >= 20) {
                            // Si este resultado es mejor que el que teníamos, lo guardamos
                            if (!bestGlobalResult || fuzzyMatch.similarity > bestGlobalResult.similarity) {
                                bestGlobalResult = {
                                    uri: file,
                                    startPosition: document.positionAt(fuzzyMatch.startIndex),
                                    endPosition: document.positionAt(fuzzyMatch.endIndex),
                                    matchType: 'fuzzy',
                                    similarity: fuzzyMatch.similarity
                                };
                            }
                        }
                    }

                } catch (err) {
                    // Ignorar errores de lectura
                }

                processedFiles++;
                if (processedFiles % 50 === 0) {
                    progress.report({
                        message: `Analizando ${processedFiles}/${files.length} (${bestGlobalResult ? 'Encontrado: ' + bestGlobalResult.similarity + '%' : '...'})`,
                        increment: (50 / files.length) * 100
                    });
                }
            }

            // Resultado Final
            if (bestGlobalResult) {
                const msg = bestGlobalResult.matchType === 'exact'
                    ? `Código encontrado (Exacto)`
                    : `Código similar encontrado (${bestGlobalResult.similarity.toFixed(1)}% similitud)`;

                vscode.window.setStatusBarMessage(msg, 4000);
                await navigateToResult(bestGlobalResult);
            } else {
                vscode.window.showInformationMessage('No se encontraron coincidencias superiores al 20%.');
            }
        });

    } catch (error) {
        vscode.window.showErrorMessage(`Error al buscar: ${error}`);
    }
}

/**
 * Busca la mejor coincidencia aproximada usando una ventana deslizante y Levenshtein.
 */
function findBestFuzzyMatch(fileText: string, searchText: string): { startIndex: number, endIndex: number, similarity: number } | null {
    // Normalización ligera para reducir ruido (espacios múltiples a uno solo)
    const normalize = (str: string) => str.replace(/\s+/g, ' ').trim();

    const cleanSearch = normalize(searchText);
    const cleanFile = normalize(fileText);

    // Si la búsqueda es muy pequeña, usar búsqueda simple
    if (cleanSearch.length < 5) return null;

    // --- HEURÍSTICA DE RENDIMIENTO ---
    // Si el archivo no contiene al menos algunas de las "palabras" del search, descartar.
    // Esto evita correr Levenshtein en archivos que no tienen nada que ver.
    const searchTokens = cleanSearch.split(' ').filter(w => w.length > 3);
    if (searchTokens.length > 0) {
        let foundTokens = 0;
        for (const token of searchTokens) {
            if (cleanFile.includes(token)) foundTokens++;
        }
        // Si no encontramos ni el 20% de las palabras clave, saltamos este archivo
        if ((foundTokens / searchTokens.length) < 0.2) return null;
    }

    // --- VENTANA DESLIZANTE ---
    // En lugar de comparar todo el archivo, movemos una ventana del tamaño del texto buscado
    const searchLen = searchText.length;
    const step = Math.max(1, Math.floor(searchLen / 4)); // Saltos para optimizar velocidad

    let bestSimilarity = 0;
    let bestIndex = -1;

    // Recorremos el texto original (sin normalizar posiciones)
    for (let i = 0; i < fileText.length - searchLen + 1; i += step) {
        // Extraemos un fragmento del archivo de longitud similar a la búsqueda (+ margen de error)
        // Damos un margen del 20% extra de longitud por si el código en el archivo tiene más espacios
        const windowText = fileText.substring(i, i + Math.ceil(searchLen * 1.2));

        // Calculamos similitud
        const currentSim = calculateLevenshteinSimilarity(searchText, windowText);

        if (currentSim > bestSimilarity) {
            bestSimilarity = currentSim;
            bestIndex = i;
        }

        // Optimización: Si encontramos algo muy bueno, paramos de buscar en este archivo
        if (bestSimilarity > 95) break;
    }

    if (bestIndex !== -1 && bestSimilarity >= 20) {
        return {
            startIndex: bestIndex,
            endIndex: bestIndex + searchLen,
            similarity: bestSimilarity
        };
    }

    return null;
}

/**
 * Calcula el porcentaje de similitud basado en la Distancia de Levenshtein.
 * 100% = idéntico, 0% = totalmente diferente.
 */
function calculateLevenshteinSimilarity(s1: string, s2: string): number {
    // Normalizar para ignorar diferencias puramente de espaciado/tabs/enters
    const a = s1.replace(/\s+/g, ' ').toLowerCase();
    const b = s2.replace(/\s+/g, ' ').toLowerCase();

    if (a === b) return 100;
    if (a.length === 0) return 0;
    if (b.length === 0) return 0;

    const matrix = [];

    // Incrementar el primer elemento de cada fila y columna
    for (let i = 0; i <= b.length; i++) { matrix[i] = [i]; }
    for (let j = 0; j <= a.length; j++) { matrix[0][j] = j; }

    // Rellenar matriz
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1, // sustitución
                    Math.min(
                        matrix[i][j - 1] + 1, // inserción
                        matrix[i - 1][j] + 1  // eliminación
                    )
                );
            }
        }
    }

    const distance = matrix[b.length][a.length];
    const maxLength = Math.max(a.length, b.length);

    return Math.max(0, ((maxLength - distance) / maxLength) * 100);
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
}

// ... (El resto del código de ClipboardFinderViewProvider y deactivate permanece igual)
// Asegúrate de incluir la clase ClipboardFinderViewProvider y deactivate aquí abajo
// tal como estaban en tu código original.

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
                    vscode.commands.executeCommand('workbench.action.closeSidebar');
                }, 200);
            }
        });
    }
    private getHtmlContent(): string {
        // Usa tu HTML original aquí, no ha cambiado
        return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{padding:10px;font-family:var(--vscode-font-family);color:var(--vscode-foreground);} .search-button{cursor:pointer;padding:10px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;}</style>
</head>
<body>
    <h3>🔎 Finder (Mejorado)</h3>
    <p>Buscando...</p>
    <button class="search-button" onclick="findCode()">Reintentar</button>
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