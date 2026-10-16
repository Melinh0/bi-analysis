#!/usr/bin/env node






const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT_DIR = __dirname;
const BACKEND_DIR = path.join(ROOT_DIR, 'backend');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');
const PYTHON_EXE = path.join(ROOT_DIR, '.venv', 'Scripts', 'python.exe');

const args = process.argv.slice(2);
const mode = args.includes('--production') ? 'production' : 'development';
const backendOnly = args.includes('--backend-only');
const frontendOnly = args.includes('--frontend-only');


const colors = {
    reset: '\x1b[0m',
    cyan: '\x1b[36m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    red: '\x1b[31m',
    gray: '\x1b[90m',
    bold: '\x1b[1m'
};

function colorize(text, color) {
    return `${color}${text}${colors.reset}`;
}

function log(prefix, message, color = colors.gray) {
    const timestamp = new Date().toLocaleTimeString('pt-BR', { hour12: false });
    console.log(`${colorize(`[${timestamp}]`, colors.gray)} ${colorize(`[${prefix}]`, color)} ${message}`);
}

function logSystem(message) { log('SYSTEM', message, colors.yellow); }
function logBackend(message) { log('BACKEND', message, colors.cyan); }
function logFrontend(message) { log('FRONTEND', message, colors.green); }
function logError(message) { log('ERROR', message, colors.red); }

function spawnWithLogging(name, command, args, cwd, color) {
    return new Promise((resolve) => {
        const proc = spawn(command, args, {
            cwd,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { 
                ...process.env, 
                PYTHONPATH: BACKEND_DIR,
                FORCE_COLOR: '1',
                TERM: 'xterm-256color'
            },
            shell: true
        });

        const processOutput = (stream, prefix) => {
            stream.on('data', (data) => {
                const output = data.toString();
                const lines = output.trim().split('\n');
                lines.forEach(line => {
                    if (line.trim()) log(prefix, line, color);
                });
            });
        };

        processOutput(proc.stdout, name.toUpperCase());
        processOutput(proc.stderr, name.toUpperCase());

        proc.on('error', (err) => {
            logError(`${name} failed to start: ${err.message}`);
        });

        proc.on('close', (code) => {
            if (code !== 0 && code !== null) {
                logError(`${name} exited with code ${code}`);
            }
            resolve({ name, code, proc });
        });
    });
}

async function runCommand(command, args, cwd, description) {
    return new Promise((resolve, reject) => {
        logSystem(description);
        const proc = spawn(command, args, { cwd, stdio: 'inherit', shell: true });
        proc.on('close', (code) => code === 0 ? resolve() : reject(new Error(`${command} exited with code ${code}`)));
        proc.on('error', reject);
    });
}

async function main() {
    logSystem('=== BI Analysis Full Stack ===');
    logSystem(`Mode: ${mode}`);
    logSystem(`Root: ${ROOT_DIR}`);
    console.log('');

    const processes = [];

    
    if (!frontendOnly) {
        if (!fs.existsSync(PYTHON_EXE)) {
            logError(`Python not found at ${PYTHON_EXE}. Run 'uv sync' first.`);
            process.exit(1);
        }

        logSystem('Starting Backend (FastAPI on http://localhost:8000)...');
        
        const backendProc = spawn(PYTHON_EXE, ['-m', 'uvicorn', 'web.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], {
            cwd: BACKEND_DIR,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, PYTHONPATH: BACKEND_DIR, FORCE_COLOR: '1' }
        });

        backendProc.stdout.on('data', (data) => {
            data.toString().trim().split('\n').forEach(line => line && logBackend(line));
        });
        backendProc.stderr.on('data', (data) => {
            data.toString().trim().split('\n').forEach(line => line && logBackend(`ERROR: ${line}`));
        });
        backendProc.on('close', (code) => logSystem(`Backend exited with code ${code}`));
        processes.push(backendProc);
    }

    
    if (!backendOnly) {
        const nodeModulesPath = path.join(FRONTEND_DIR, 'node_modules');
        if (!fs.existsSync(nodeModulesPath)) {
            await runCommand('npm', ['install'], FRONTEND_DIR, 'Installing frontend dependencies...');
        }

        logSystem('Starting Frontend (Vite on http://localhost:5173)...');
        
        const frontendProc = spawn('npm', ['run', 'dev'], {
            cwd: FRONTEND_DIR,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, FORCE_COLOR: '1' },
            shell: true
        });

        frontendProc.stdout.on('data', (data) => {
            data.toString().trim().split('\n').forEach(line => line && logFrontend(line));
        });
        frontendProc.stderr.on('data', (data) => {
            data.toString().trim().split('\n').forEach(line => line && logFrontend(`ERROR: ${line}`));
        });
        frontendProc.on('close', (code) => logSystem(`Frontend exited with code ${code}`));
        processes.push(frontendProc);
    }

    console.log('');
    logSystem('All services started!');
    if (!frontendOnly) logSystem('Backend:  http://localhost:8000 (API: http://localhost:8000/api)');
    if (!backendOnly) logSystem('Frontend: http://localhost:5173');
    logSystem('Press Ctrl+C to stop all services.');
    console.log('');

    
    const shutdown = () => {
        console.log('');
        logSystem('Shutdown signal received...');
        processes.forEach(p => {
            if (!p.killed) {
                p.kill('SIGTERM');
                setTimeout(() => { if (!p.killed) p.kill('SIGKILL'); }, 3000);
            }
        });
        setTimeout(() => process.exit(0), 1000);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
    process.on('exit', () => processes.forEach(p => !p.killed && p.kill()));
    
    
    await new Promise(() => {}); 
}

main().catch(err => {
    logError(`Fatal error: ${err.message}`);
    process.exit(1);
});