// Run with `node --test tests/jupyter_link.test.cjs` (also run by pytest).
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = readFileSync(path.join(__dirname, '../.devx/_static/js/jupyter-link.js'), 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
const plain = value => JSON.parse(JSON.stringify(value));

function editor(source) {
    const lines = source.split('\n');
    return {
        lineCount: lines.length,
        getLine: line => lines[line],
        setSelection(selection) { this.selection = plain(selection); },
        focus() { this.focused = true; },
        revealSelection(selection) { this.revealed = plain(selection); }
    };
}

function notebook(sources) {
    const widgets = sources.map(([type, source]) => ({
        model: { type, sharedModel: { getSource: () => source } },
        rendered: type === 'markdown',
        // Like a windowed notebook, editors only exist after scrolling/rendering.
        editor: null
    }));
    return {
        model: { cells: { length: widgets.length, get: i => widgets[i].model } },
        widgets,
        activeCellIndex: 0,
        mode: 'edit',
        deselectAll() { this.deselected = true; },
        activate() { this.activated = true; },
        async scrollToItem(index) {
            this.scrolled = index;
            widgets[index].ready = tick().then(() => {
                widgets[index].editor = editor(sources[index][1]);
            });
        }
    };
}

function bridge(widget) {
    const messages = { error: [], warn: [] };
    const opened = [];
    const app = {
        // Focus can still be on the lesson iframe or a different document.
        shell: { currentWidget: { content: { editor: editor('unrelated') } } },
        serviceManager: { contents: { get: async () => ({}) } },
        commands: {
            async execute(command, args) {
                assert.equal(command, 'docmanager:open');
                opened.push(plain(args));
                return widget;
            }
        }
    };
    const context = vm.createContext({
        window: { parent: { jupyterapp: app } },
        console: {
            log() {},
            error: (...args) => messages.error.push(args.join(' ')),
            warn: (...args) => messages.warn.push(args.join(' '))
        }
    });
    vm.runInContext(script, context);
    return { context, app, messages, opened };
}

function panel(content) {
    return { content, context: { ready: Promise.resolve() }, revealed: Promise.resolve() };
}

test('a notebook link waits for loading and selects an off-screen code cell', async () => {
    const content = notebook([
        ['markdown', '# Introduction'],
        ['markdown', '<details>Hint: class CLIToolCall(BaseModel): ...</details>'],
        ['code', '# Exercise\nclass CLIToolCall(BaseModel):\n    pass']
    ]);
    const widget = panel(null);
    let load;
    widget.context.ready = new Promise(resolve => { load = resolve; });
    const { context, app, opened, messages } = bridge(widget);
    const navigation = context.goToLineAndSelect('example.ipynb', 'class CLIToolCall');
    await tick();
    assert.equal(content.scrolled, undefined);
    widget.content = content;
    load();
    await navigation;

    assert.deepEqual(opened, [{ path: 'example.ipynb' }]);
    assert.equal(content.activeCellIndex, 2);
    assert.equal(content.scrolled, 2);
    assert.equal(content.deselected, true);
    assert.equal(content.widgets[2].editor.selection.start.line, 1);
    assert.equal(content.widgets[2].editor.focused, true);
    assert.equal(app.shell.currentWidget.content.editor.selection, undefined);
    assert.deepEqual(messages, { error: [], warn: [] });
});

test('heading links keep Markdown rendered and support repeated navigation', async () => {
    const content = notebook([
        ['markdown', '# Introduction'],
        ['code', 'run_agent()'],
        ['markdown', '## Evaluate with a rubric-based judge']
    ]);
    const { context, messages } = bridge(panel(content));
    await context.goToLineAndSelect('example.ipynb', '## Evaluate');
    assert.equal(content.activeCellIndex, 2);
    assert.equal(content.scrolled, 2);
    assert.equal(content.mode, 'command');
    assert.equal(content.activated, true);
    assert.equal(content.widgets[2].rendered, true);
    assert.equal(content.widgets[2].editor.focused, undefined);

    await context.goToLineAndSelect('example.ipynb', '# Introduction');
    assert.equal(content.activeCellIndex, 0);
    assert.equal(content.scrolled, 0);
    assert.deepEqual(messages, { error: [], warn: [] });
});

test('non-windowed notebooks use the cell DOM to scroll', async () => {
    const content = notebook([['code', 'setup()'], ['code', 'target()']]);
    delete content.scrollToItem;
    const cell = content.widgets[1];
    cell.editor = editor('target()');
    cell.node = { scrollIntoView() { cell.scrolled = true; } };
    const { context } = bridge(panel(content));
    await context.goToLineAndSelect('example.ipynb', 'target');
    assert.equal(content.activeCellIndex, 1);
    assert.equal(cell.scrolled, true);
    assert.equal(cell.editor.selection.start.line, 0);
});

for (const [label, source, target, line] of [
    ['first line', '# TODO: first\nrest', '# TODO: first', 0],
    ['last line', 'start\n\n# TODO: last', '# TODO: last', 2],
    ['first occurrence', 'start\nmatch\nmatch', 'match', 1]
]) {
    test(`file links select the ${label} through public editor APIs`, async () => {
        const fileEditor = editor(source);
        const { context, messages } = bridge(panel({ editor: fileEditor }));
        await context.goToLineAndSelect('exercise.py', target);
        assert.deepEqual(fileEditor.selection, {
            start: { line, column: 0 },
            end: { line, column: source.split('\n')[line].length }
        });
        assert.deepEqual(fileEditor.revealed, fileEditor.selection);
        assert.equal(fileEditor.focused, true);
        assert.deepEqual(messages, { error: [], warn: [] });
    });
}

test('a missing notebook target preserves the active cell and reports no match', async () => {
    const content = notebook([['markdown', '# Introduction'], ['code', 'setup()']]);
    content.activeCellIndex = 1;
    const { context, messages } = bridge(panel(content));
    await context.goToLineAndSelect('example.ipynb', 'missing target');
    assert.equal(content.activeCellIndex, 1);
    assert.equal(content.scrolled, undefined);
    assert.deepEqual(messages, { error: [], warn: ['"missing target" not found.'] });
});

test('an unsuccessful open never selects text in another document', async () => {
    const { context, app } = bridge(undefined);
    await context.goToLineAndSelect('example.ipynb', 'unrelated');
    assert.equal(app.shell.currentWidget.content.editor.selection, undefined);
});

for (const [lesson, label, cellIndex] of [
    ['sdg', 'template sampler', 9],
    ['run_customized', 'HuggingFaceLLM', 12],
    ['run_customized', 'Messages', 16]
]) {
    test(`the shipped ${label} button targets its editable exercise`, async () => {
        const root = path.join(__dirname, '..');
        const markdown = readFileSync(path.join(root, `.devx/4-agent-customization/${lesson}.md`), 'utf8');
        const buttons = [...markdown.matchAll(/<button onclick="goToLineAndSelect\('([^']+)',\s*'([^']*)'\);">.*?<\/button>/g)];
        const button = buttons.find(match => match[0].endsWith(` ${label}</button>`));
        assert.ok(button, `No ${label} button found`);
        const [, filename, search] = button;
        const data = JSON.parse(readFileSync(path.join(root, filename), 'utf8'));
        const content = notebook(data.cells.map(cell => [
            cell.cell_type, Array.isArray(cell.source) ? cell.source.join('') : cell.source
        ]));
        const { context, messages } = bridge(panel(content));
        await context.goToLineAndSelect(filename, search);
        assert.equal(content.activeCellIndex, cellIndex);
        assert.equal(content.widgets[cellIndex].model.type, 'code');
        assert.equal(content.widgets[cellIndex].editor.focused, true);
        assert.deepEqual(messages, { error: [], warn: [] });
    });
}
