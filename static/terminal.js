// Terminal emulator
const Terminal = window.Terminal;
const FitAddon = window.FitAddon.FitAddon;

const terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontFamily: "'Courier New', monospace",
    fontSize: 14,
    theme: {
        background: '#0a0e27',
        foreground: '#00ff00',
        cursor: '#00ff00',
        selection: 'rgba(0, 255, 0, 0.2)',
        black: '#000000',
        red: '#ff0000',
        green: '#00ff00',
        yellow: '#ffff00',
        blue: '#0000ff',
        magenta: '#ff00ff',
        cyan: '#00ffff',
        white: '#ffffff'
    }
});

const fitAddon = new FitAddon();
terminal.loadAddon(fitAddon);

const terminalElement = document.getElementById('terminal');
terminal.open(terminalElement);

// Fit terminal to container
fitAddon.fit();
window.addEventListener('resize', () => {
    try {
        fitAddon.fit();
    } catch (e) {
        // Ignore fit errors
    }
});

// State
let currentPath = '/home/user';
let commandHistory = [];
let historyIndex = 0;
let sessionId = 'session-' + Date.now();
let inputBuffer = '';

// Initialize
terminal.writeln('\x1b[32m╔════════════════════════════════════════╗\x1b[0m');
terminal.writeln('\x1b[32m║    Arch Linux Browser Terminal        ║\x1b[0m');
terminal.writeln('\x1b[32m║    Type "help" for available commands ║\x1b[0m');
terminal.writeln('\x1b[32m╚════════════════════════════════════════╝\x1b[0m\n');

showPrompt();

// Keyboard input
terminal.onData((data) => {
    // Handle special keys
    if (data === '\u0003') { // Ctrl+C
        inputBuffer = '';
        terminal.write('\n');
        showPrompt();
        return;
    }
    
    if (data === '\r') { // Enter
        terminal.write('\n');
        if (inputBuffer.trim()) {
            executeCommand(inputBuffer);
        } else {
            showPrompt();
        }
        inputBuffer = '';
        historyIndex = 0;
        return;
    }
    
    if (data === '\u007f') { // Backspace
        if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1);
            terminal.write('\b \b');
        }
        return;
    }
    
    if (data === '\u001b[A') { // Up arrow
        if (historyIndex < commandHistory.length) {
            historyIndex++;
            const cmd = commandHistory[commandHistory.length - historyIndex];
            clearInputLine();
            inputBuffer = cmd;
            terminal.write(inputBuffer);
        }
        return;
    }
    
    if (data === '\u001b[B') { // Down arrow
        if (historyIndex > 0) {
            historyIndex--;
            const cmd = historyIndex > 0 ? commandHistory[commandHistory.length - historyIndex] : '';
            clearInputLine();
            inputBuffer = cmd;
            terminal.write(inputBuffer);
        }
        return;
    }
    
    // Regular character input
    if (data.match(/[\x20-\x7E]/)) { // Printable ASCII
        inputBuffer += data;
        terminal.write(data);
    }
});

function clearInputLine() {
    for (let i = 0; i < inputBuffer.length; i++) {
        terminal.write('\b \b');
    }
}

function showPrompt() {
    terminal.write(`\x1b[32m[user@arch \x1b[33m${currentPath}\x1b[32m]$\x1b[0m `);
}

async function executeCommand(command) {
    commandHistory.push(command);
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                command: command
            })
        });
        
        const data = await response.json();
        const output = data.output;
        const newPath = data.cwd;
        
        // Update path
        if (newPath) {
            currentPath = newPath;
        }
        
        // Handle special commands
        if (output === '__CLEAR__') {
            terminal.clear();
        } else if (output === '__EXIT__') {
            terminal.writeln('\x1b[31mGoodbye!\x1b[0m');
            terminal.write('\nReload the page to start a new session.');
            return;
        } else if (output) {
            terminal.writeln(output);
        }
    } catch (error) {
        terminal.writeln(`\x1b[31mError: ${error.message}\x1b[0m`);
    }
    
    terminal.write('\n');
    showPrompt();
}
