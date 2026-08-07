/**
 * Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * LicenseRef-NvidiaProprietary
 *
 * NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
 * property and proprietary rights in and to this material, related
 * documentation and any modifications thereto. Any use, reproduction,
 * disclosure or distribution of this material and related documentation
 * without an express license agreement from NVIDIA CORPORATION or
 * its affiliates is strictly prohibited
 */

// Helper functions used for jupyter interactions //

async function openOrCreateFileInJupyterLab(path, factory = null, initialContent = '') {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }

    // Resolve tilde paths by creating a symlink in the corresponding code/<module>/ directory
    if (path.startsWith('~/')) {
        path = await resolveTildePath(app, path);
        if (!path) return;
    }

    const contentsManager = app.serviceManager.contents;

    const fileExists = await checkFileExists(contentsManager, path);

    if (!fileExists) {
        // Ensure parent directories exist
        const dirPath = getParentDirectory(path);
        if (dirPath) {
            await ensureDirectoryExists(contentsManager, dirPath);
        }

        if (path.endsWith('.ipynb')) {
            await createNewNotebook(contentsManager, path);
        } else {
            await createNewFile(contentsManager, path, initialContent);
        }
    }

    await openFile(app, path, factory);
}

async function checkFileExists(contentsManager, path) {
    try {
        await contentsManager.get(path);
        console.log(`File ${path} already exists.`);
        return true;
    } catch (err) {
        if (err.response && err.response.status === 404) {
            console.log(`File ${path} does not exist.`);
            return false;
        } else {
            console.error(`Error checking file ${path}:`, err);
            throw err;
        }
    }
}

async function ensureDirectoryExists(contentsManager, dirPath) {
    const parts = dirPath.split('/');
    let currentPath = '';

    for (const part of parts) {
        currentPath = currentPath ? `${currentPath}/${part}` : part;

        try {
            await contentsManager.get(currentPath);
            console.log(`Directory ${currentPath} exists.`);
        } catch (err) {
            if (err.response && err.response.status === 404) {
                console.log(`Creating directory: ${currentPath}`);
                await contentsManager.newUntitled({
                    path: getParentDirectory(currentPath),
                    type: 'directory'
                });

                // Rename the untitled folder to the target name
                const untitledFolder = `${getParentDirectory(currentPath) ? getParentDirectory(currentPath) + '/' : ''}Untitled Folder`;
                await contentsManager.rename(untitledFolder, currentPath);
            } else {
                console.error(`Error checking/creating directory ${currentPath}:`, err);
                throw err;
            }
        }
    }
}

async function createNewNotebook(contentsManager, path) {
    const notebookContent = {
        cells: [],
        metadata: {},
        nbformat: 4,
        nbformat_minor: 5
    };

    await contentsManager.save(path, {
        type: 'notebook',
        format: 'json',
        content: notebookContent
    });

    console.log(`Created new notebook at ${path} (no kernel assigned)`);
}

async function createNewFile(contentsManager, path, initialContent = '') {
    await contentsManager.save(path, {
        type: 'file',
        format: 'text',
        content: initialContent
    });

    console.log(`Created new file at ${path}`);
}

async function openFile(app, path, factory = null) {
    const command = 'docmanager:open';
    const args = { path };
    if (factory) {
        args.factory = factory;
    }

    try {
        const widget = await app.commands.execute(command, args);
        console.log(`Opened ${path} successfully`, widget);
    } catch (error) {
        console.error(`Failed to open ${path}:`, error);
    }
}

async function openVoila(path) {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }

    try {
        await openFile(app, path, "Voila Preview");
        console.log(`Opened ${path} with Voila Preview successfully`);
    } catch (error) {
        console.error(`Failed to open ${path} with Voila Preview:`, error);
    }
}

function getParentDirectory(path) {
    const parts = path.split('/');
    parts.pop(); // remove the file name
    return parts.join('/');
}


async function goToLine(filename, lineno) {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }
    await openOrCreateFileInJupyterLab(filename);
    app.commands.execute('fileeditor:go-to-line', { line: lineno });
}


async function goToLineAndSelect(filename, searchString, retry=true) {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }
    await openOrCreateFileInJupyterLab(filename);

    const widget = app.shell.currentWidget;
    const editor = widget?.content?.editor;
    const blocks = editor?.doc?.children;

    if (!editor || !blocks || !Array.isArray(blocks)) {
        if (retry) {
            // retry with a delay
            await new Promise(resolve => setTimeout(resolve, 1000));
            return await goToLineAndSelect(filename, searchString, retry=false);
        }
        console.error("No suitable editor or document found.");
        return;
    }

    // Flatten all lines across all blocks, tracking line numbers
    let totalLine = 0;

    // Get current cursor position
    const currentCursorPosition = editor.getCursorPosition();
    const currentLine = currentCursorPosition ? currentCursorPosition.line : 0;

    for (const block of blocks) {
        const lines = block.text;
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].includes(searchString)) {
                const matchLine = totalLine;

                // Only add padding if matchLine > currentLine
                const linePadding = matchLine > currentLine ? Math.min(lines.length - i, 5) : 0;
                const targetLine = matchLine + linePadding;
                await app.commands.execute('fileeditor:go-to-line', { line: targetLine });

                // Select and scroll to the matched line
                const selection = {
                    start: { line: matchLine, column: 0 },
                    end: { line: matchLine, column: lines[i].length }
                }
                editor.setSelection(selection);

                return;
            }
            totalLine++;
        }
    }

    console.warn(`"${searchString}" not found.`);
}


async function openNewTerminal() {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }

    try {
        const widget = await app.commands.execute('terminal:create-new');
        console.log('New terminal opened successfully', widget);
        return widget;
    } catch (error) {
        console.error('Failed to open new terminal:', error);
    }
}


/**
 * Resolves a launcher tile (by its displayed title + catalog) to the command id
 * that opens it.
 *
 * Matching is done against the command registry, NOT the launcher DOM. The
 * earlier DOM-based version located the tile's position within its rendered
 * section and compared that to `item.rank` — but jupyter-app-launcher assigns
 * rank as the tile's index in the whole jp_app_launcher.yaml array
 * (`configs.forEach((config, i) => launcher.add({category: config.catalog, rank: i}))`),
 * which is global, not per-catalog. The two only agree for the catalog that
 * starts at index 0, so every button in a second catalog silently resolved to
 * null. Each tile is registered with `label: <title>` and `category: <catalog>`,
 * so matching on those is both correct and independent of how it renders.
 */
async function findLauncherCommand(itemLabel = "Secrets Manager", sectionName = "NVIDIA DevX Learning Path") {
    // Access the global JupyterLab app object
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return null;
    }

    const findLaunchers = () => Array.from(app.shell.widgets('main')).filter(w =>
        w.id && w.id.includes('launcher')
    );

    let launchers = findLaunchers();

    if (launchers.length == 0) {
        console.log("No launchers found, creating one");
        // Must be awaited — the widget is not in the shell until this resolves.
        await app.commands.execute("launcher:create");
        launchers = findLaunchers();
    }

    // Search through all launchers for the target item
    for (const launcher of launchers) {
        const items = launcher.content?.model?.itemsList;
        if (!items) continue;

        const item = items.find(entry =>
            entry.category === sectionName &&
            app.commands.label(entry.command, entry.args) === itemLabel
        );

        if (item) {
            return item.command;
        }
    }

    console.error(`Launcher item "${itemLabel}" not found in section "${sectionName}"`);
    return null;
}


async function launch(itemLabel = "Secrets Manager", sectionName = "NVIDIA DevX Learning Path") {
    const app = window.parent.jupyterapp;
    if (!app) {
        console.error('JupyterLab app is not available on window.jupyterapp');
        return;
    }

    const command = await findLauncherCommand(itemLabel, sectionName);
    if (!command) {
        console.error('No DevX workshop command found');
        return;
    }

    app.commands.execute(command);
}


// --- Tilde path resolution for files outside the JupyterLab server root ---

/**
 * Identifies the current module by fetching the .devx-module marker file.
 * Each module directory contains a .devx-module file with the module name
 * (e.g., "6-agent-safety"). Since the local HTTP server's root is the module
 * directory, this file is directly fetchable.
 * Returns "code/<module>" or empty string if not found.
 */
async function getModuleDir() {
    try {
        const resp = await fetch('.devx-module');
        if (resp.ok) {
            const module = (await resp.text()).trim();
            if (module) return 'code/' + module;
        }
    } catch {}
    return '';
}

/**
 * Resolves a tilde path (e.g., "~/.openclaw/workspace/SOUL.md") to a project-relative
 * path by creating a symlink in the corresponding code/<module>/ directory.
 * The symlink is created via a hidden terminal session if it doesn't already exist.
 */
async function resolveTildePath(app, tildePath) {
    const withoutTilde = tildePath.slice(2); // ".openclaw/workspace/SOUL.md"
    const parts = withoutTilde.split('/');
    const fileName = parts.pop(); // "SOUL.md"
    const dirPath = parts.join('/'); // ".openclaw/workspace"
    const symlinkName = parts[parts.length - 1] || dirPath.replace(/[\/\.]/g, '-'); // "workspace"

    const moduleDir = await getModuleDir(); // "code/6-agent-safety"
    const symlinkBase = moduleDir ? moduleDir + '/' + symlinkName : symlinkName;
    const resolvedPath = symlinkBase + '/' + fileName; // "code/6-agent-safety/workspace/SOUL.md"

    // Check if the file is already accessible through an existing symlink
    const contentsManager = app.serviceManager.contents;
    try {
        await contentsManager.get(resolvedPath);
        console.log(`Tilde path resolved via existing symlink: ${resolvedPath}`);
        return resolvedPath;
    } catch {
        // Symlink doesn't exist yet — create it
    }

    console.log(`Creating symlink: /project/${symlinkBase} → ~/${dirPath}`);
    try {
        await runShellCommand(app, `ln -sfn ~/${dirPath} /project/${symlinkBase}`);
    } catch (err) {
        console.error('Failed to create symlink for tilde path:', err);
        return null;
    }

    return resolvedPath;
}

/**
 * Executes a shell command via a hidden JupyterLab terminal session.
 * Uses app.serviceManager.terminals (from the parent JupyterLab frame)
 * which handles authentication automatically — avoids 403 errors from
 * cross-frame fetch calls.
 */
async function runShellCommand(app, command) {
    const session = await app.serviceManager.terminals.startNew();

    return new Promise((resolve, reject) => {
        let done = false;

        const onMessage = (_, msg) => {
            if (msg.type === 'stdout' && msg.content.some(s => s.includes('__SYMLINK_DONE__'))) {
                done = true;
                session.messageReceived.disconnect(onMessage);
                session.shutdown();
                resolve();
            }
        };

        session.messageReceived.connect(onMessage);
        session.send({ type: 'stdin', content: [`${command} && echo __SYMLINK_DONE__\r`] });

        // Timeout safety net
        setTimeout(() => {
            if (!done) {
                done = true;
                session.messageReceived.disconnect(onMessage);
                session.shutdown();
                resolve(); // Resolve anyway — symlink may still have been created
            }
        }, 10000);
    });
}
