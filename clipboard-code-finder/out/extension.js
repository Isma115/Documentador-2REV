"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
// Extensiones de archivos de código soportadas
const CODE_EXTENSIONS = [
    'js', 'ts', 'jsx', 'tsx', 'mjs', 'cjs',
    'py', 'pyw',
    'java', 'kt', 'kts', 'scala',
    'c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'hxx',
    'cs',
    'go',
    'rb', 'rake',
    'php',
    'swift',
    'rs',
    'vue', 'svelte',
    'html', 'htm', 'xml', 'xhtml',
    'css', 'scss', 'sass', 'less',
    'json', 'jsonc',
    'yaml', 'yml',
    'sql',
    'sh', 'bash', 'zsh', 'fish',
    'ps1', 'psm1', 'psd1',
    'r', 'R',
    'lua',
    'pl', 'pm',
    'ex', 'exs',
    'clj', 'cljs',
    'dart',
    'hs',
    'erl', 'hrl',
    'ml', 'mli',
    'fs', 'fsx',
    'groovy', 'gradle'
];
// Tipo de decoración para destacar código encontrado
let highlightDecoration;
function activate(context) {
    console.log('Clipboard Code Finder está activo');
    // Crear decoración para destacar el código encontrado
    highlightDecoration = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(255, 255, 0, 0.4)',
        border: '2px solid #FFD700',
        borderRadius: '3px',
        isWholeLine: false
    });
    // Registrar el comando principal
    const findCodeCommand = vscode.commands.registerCommand('clipboard-code-finder.findCode', findClipboardCode);
    // Registrar el proveedor de vista del panel lateral
    const provider = new ClipboardFinderViewProvider(context.extensionUri);
    const webviewProvider = vscode.window.registerWebviewViewProvider('clipboardFinderView', provider);
    context.subscriptions.push(findCodeCommand, webviewProvider, highlightDecoration);
}
async function findClipboardCode() {
    try {
        // 1. Leer el contenido del portapapeles
        const clipboardContent = await vscode.env.clipboard.readText();
        if (!clipboardContent || clipboardContent.trim().length === 0) {
            vscode.window.showWarningMessage('El portapapeles está vacío. Copia un fragmento de código primero.');
            return;
        }
        const searchText = clipboardContent.trim();
        // Mostrar progreso mientras busca
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Buscando código en el workspace...',
            cancellable: true
        }, async (progress, token) => {
            // 2. Construir el patrón glob para archivos de código
            const globPattern = `**/*.{${CODE_EXTENSIONS.join(',')}}`;
            // 3. Buscar archivos en el workspace
            const files = await vscode.workspace.findFiles(globPattern, '**/node_modules/**', // Excluir node_modules
            5000 // Máximo de archivos a buscar
            );
            if (token.isCancellationRequested) {
                return;
            }
            progress.report({ message: `Analizando ${files.length} archivos...` });
            // 4. Buscar coincidencias en cada archivo
            const results = [];
            let processedFiles = 0;
            for (const file of files) {
                if (token.isCancellationRequested) {
                    return;
                }
                try {
                    const document = await vscode.workspace.openTextDocument(file);
                    const text = document.getText();
                    // Búsqueda exacta
                    const index = text.indexOf(searchText);
                    if (index !== -1) {
                        const position = document.positionAt(index);
                        const endPosition = document.positionAt(index + searchText.length);
                        results.push({
                            uri: file,
                            startPosition: position,
                            endPosition: endPosition,
                            matchType: 'exact',
                            similarity: 100
                        });
                    }
                    else {
                        // Búsqueda por similitud (sin espacios en blanco)
                        const normalizedSearch = normalizeCode(searchText);
                        const normalizedText = normalizeCode(text);
                        const similarIndex = normalizedText.indexOf(normalizedSearch);
                        if (similarIndex !== -1 && normalizedSearch.length > 10) {
                            // Encontrar la posición real en el texto original
                            const realPosition = findRealPosition(text, searchText);
                            if (realPosition !== -1) {
                                const position = document.positionAt(realPosition);
                                const endPosition = document.positionAt(realPosition + findMatchLength(text, realPosition, searchText));
                                results.push({
                                    uri: file,
                                    startPosition: position,
                                    endPosition: endPosition,
                                    matchType: 'similar',
                                    similarity: calculateSimilarity(searchText, text.substring(realPosition, realPosition + searchText.length * 2))
                                });
                            }
                        }
                    }
                }
                catch (err) {
                    // Ignorar archivos que no se pueden leer
                }
                processedFiles++;
                if (processedFiles % 100 === 0) {
                    progress.report({
                        message: `Analizando ${processedFiles}/${files.length} archivos...`,
                        increment: (100 / files.length) * 100
                    });
                }
            }
            // 5. Procesar resultados
            if (results.length === 0) {
                vscode.window.showInformationMessage('No se encontró ninguna coincidencia para el código del portapapeles.');
                return;
            }
            // Ordenar por similitud (mayor primero)
            results.sort((a, b) => b.similarity - a.similarity);
            if (results.length === 1) {
                // Solo un resultado: navegar directamente
                await navigateToResult(results[0]);
            }
            else {
                // Múltiples resultados: mostrar lista de selección
                const items = results.map(r => ({
                    label: `$(file-code) ${path.basename(r.uri.fsPath)}`,
                    description: `Línea ${r.startPosition.line + 1} - ${r.matchType === 'exact' ? 'Coincidencia exacta' : `Similitud: ${r.similarity}%`}`,
                    detail: r.uri.fsPath,
                    result: r
                }));
                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: `Se encontraron ${results.length} coincidencias. Selecciona una:`,
                    matchOnDescription: true,
                    matchOnDetail: true
                });
                if (selected) {
                    await navigateToResult(selected.result);
                }
            }
        });
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error al buscar: ${error}`);
    }
}
async function navigateToResult(result) {
    // Abrir el documento
    const document = await vscode.workspace.openTextDocument(result.uri);
    const editor = await vscode.window.showTextDocument(document, {
        preview: false,
        selection: new vscode.Range(result.startPosition, result.endPosition)
    });
    // Centrar la vista en el código encontrado
    editor.revealRange(new vscode.Range(result.startPosition, result.endPosition), vscode.TextEditorRevealType.InCenter);
    // Aplicar destacado temporal
    const range = new vscode.Range(result.startPosition, result.endPosition);
    editor.setDecorations(highlightDecoration, [range]);
    // Remover el destacado después de 3 segundos
    setTimeout(() => {
        editor.setDecorations(highlightDecoration, []);
    }, 3000);
    vscode.window.showInformationMessage(`✓ Código encontrado en ${path.basename(result.uri.fsPath)}, línea ${result.startPosition.line + 1}`);
}
function normalizeCode(code) {
    // Eliminar todo lo que no sea alfanumérico para comparación "fuzzy" agresiva
    return code.replace(/[^a-z0-9]/gi, '').toLowerCase();
}
function findRealPosition(fullText, searchText) {
    // Buscar línea por línea para encontrar coincidencia aproximada
    const searchLines = searchText.trim().split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (searchLines.length === 0)
        return -1;
    const firstLine = searchLines[0];
    const lines = fullText.split('\n');
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].includes(firstLine) ||
            normalizeCode(lines[i]).includes(normalizeCode(firstLine))) {
            // Calcular el índice en el texto completo
            let position = 0;
            for (let j = 0; j < i; j++) {
                position += lines[j].length + 1; // +1 por el \n
            }
            return position;
        }
    }
    return -1;
}
function findMatchLength(text, startPos, searchText) {
    // Estimar la longitud de la coincidencia
    const searchLines = searchText.split('\n').length;
    const textLines = text.substring(startPos).split('\n');
    let length = 0;
    for (let i = 0; i < Math.min(searchLines, textLines.length); i++) {
        length += textLines[i].length + 1;
    }
    return Math.max(length - 1, searchText.length);
}
function calculateSimilarity(str1, str2) {
    const s1 = normalizeCode(str1);
    const s2 = normalizeCode(str2.substring(0, str1.length * 2));
    if (s1.length === 0 || s2.length === 0)
        return 0;
    // Contar caracteres comunes
    let common = 0;
    const s2Chars = s2.split('');
    for (const char of s1) {
        const index = s2Chars.indexOf(char);
        if (index !== -1) {
            common++;
            s2Chars.splice(index, 1);
        }
    }
    return Math.round((common / s1.length) * 100);
}
// Proveedor de vista para el panel lateral
class ClipboardFinderViewProvider {
    extensionUri;
    constructor(extensionUri) {
        this.extensionUri = extensionUri;
    }
    resolveWebviewView(webviewView, _context, _token) {
        webviewView.webview.options = {
            enableScripts: true
        };
        webviewView.webview.html = this.getHtmlContent();
        // Manejar mensajes del webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'findCode') {
                await vscode.commands.executeCommand('clipboard-code-finder.findCode');
            }
        });
        // Disparar búsqueda cada vez que la vista se hace visible
        webviewView.onDidChangeVisibility(() => {
            if (webviewView.visible) {
                // Pequeño retardo para asegurar que VS Code procesa la visibilidad y el comando no se corta
                setTimeout(() => {
                    vscode.commands.executeCommand('clipboard-code-finder.findCode');
                    vscode.commands.executeCommand('workbench.action.closeSidebar');
                }, 200);
            }
        });
    }
    getHtmlContent() {
        return `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            padding: 10px;
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            font-weight: 600;
        }
        p {
            margin: 0;
            font-size: 12px;
            opacity: 0.8;
            line-height: 1.5;
        }
        .search-button {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        .search-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        .search-button:active {
            transform: scale(0.98);
        }
        .icon {
            width: 16px;
            height: 16px;
        }
        .instructions {
            background-color: var(--vscode-textBlockQuote-background);
            border-left: 3px solid var(--vscode-textLink-foreground);
            padding: 10px;
            border-radius: 0 4px 4px 0;
            margin-top: 10px;
        }
        .instructions ol {
            margin: 5px 0 0 0;
            padding-left: 20px;
        }
        .instructions li {
            font-size: 11px;
            margin-bottom: 5px;
            opacity: 0.9;
        }
        .shortcut {
            margin-top: 15px;
            font-size: 11px;
            opacity: 0.7;
            text-align: center;
        }
        kbd {
            background-color: var(--vscode-keybindingLabel-background);
            border: 1px solid var(--vscode-keybindingLabel-border);
            border-radius: 3px;
            padding: 2px 5px;
            font-size: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div>
            <h3>🔍 Clipboard Code Finder</h3>
            <p>Buscando automáticamente código del portapapeles...</p>
        </div>

        <button class="search-button" onclick="findCode()">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
            </svg>
            Reintentar Búsqueda
        </button>

        <div class="instructions">
            <strong>Instrucciones:</strong>
            <ol>
                <li>Copia un fragmento de código (Ctrl+C)</li>
                <li>Abre este panel o pulsa el botón de arriba</li>
                <li>El código será encontrado y destacado</li>
            </ol>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function findCode() {
            vscode.postMessage({ command: 'findCode' });
        }

        // Auto-iniciar búsqueda al cargar la vista
        window.addEventListener('load', () => {
             findCode();
        });
    </script>
</body>
</html>`;
    }
}
function deactivate() {
    if (highlightDecoration) {
        highlightDecoration.dispose();
    }
}
//# sourceMappingURL=extension.js.map