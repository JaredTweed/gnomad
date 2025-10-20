/*
 * Ads / No Ads Toggle — GNOME Shell 45+
 * Places a tiny text indicator in the top bar that reads "No Ads" (when ON)
 * or "Ads" (when OFF). Clicking opens a minimal menu with a single toggle and
 * a Settings button. State is persisted in GSettings and mirrored to TBlock.
 */

import Gio from 'gi://Gio';
import GObject from 'gi://GObject';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as ExtensionUtils from 'resource:///org/gnome/shell/extensions/extensionUtils.js';

const INDICATOR_STYLE = 'no-ads-toggle-label';
const SETTINGS_SCHEMA = 'org.gnome.shell.extensions.gnomad';
const TBLOCK_BASE_ARGS = ['--quiet', '--no-prompt'];

function getSettings() {
    return ExtensionUtils.getSettings(SETTINGS_SCHEMA);
}

class TBlockCommandRunner {
    constructor() {
        const extension = ExtensionUtils.getCurrentExtension();
        const tblockDir = extension?.dir?.get_child('tblock');

        if (!tblockDir || !tblockDir.query_exists(null)) {
            throw new Error('TBlock sources are missing; expected tblock/ inside the extension.');
        }

        this._modulePath = tblockDir.get_path();
        this._queue = Promise.resolve();
    }

    runQueued(args, {requireRoot = true} = {}) {
        this._queue = this._queue.catch(() => {}).then(() => this._execute(args, {requireRoot}));
        return this._queue;
    }

    async _execute(args, {requireRoot = true} = {}) {
        const argv = requireRoot
            ? ['pkexec', 'env', `PYTHONPATH=${this._modulePath}`, 'python3', '-m', 'tblock', ...args]
            : ['env', `PYTHONPATH=${this._modulePath}`, 'python3', '-m', 'tblock', ...args];

        const subprocess = new Gio.Subprocess({
            argv,
            flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
        });

        return await new Promise((resolve, reject) => {
            subprocess.communicate_utf8_async(null, null, (_proc, res) => {
                try {
                    const [, stdout, stderr] = subprocess.communicate_utf8_finish(res);
                    const exitCode = subprocess.get_exit_status();
                    resolve({
                        success: exitCode === 0,
                        stdout,
                        stderr,
                        exitCode,
                        argv,
                    });
                } catch (error) {
                    reject(error);
                }
            });
        });
    }
}

class TBlockClient {
    constructor() {
        this._runner = new TBlockCommandRunner();
    }

    async setEnabled(enabled) {
        const op = enabled ? '--enable' : '--disable';
        return await this._runner.runQueued([...TBLOCK_BASE_ARGS, op]);
    }

    async getStatus() {
        const result = await this._runner.runQueued(['--status', '--quiet'], {requireRoot: false});
        if (!result.success) {
            return null;
        }

        const match = result.stdout.match(/Protection:\s*(active|inactive)/i);
        if (!match) {
            return null;
        }

        return match[1].toLowerCase() === 'active';
    }
}

const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'Ads / No Ads Toggle');

        this._settings = getSettings();
        this._tblock = new TBlockClient();
        this._ignoreSetting = false;
        this._isBusy = false;
        this._pendingState = null;

        this._label = new St.Label({
            text: '',
            y_align: St.Align.MIDDLE,
            style_class: INDICATOR_STYLE,
        });
        this.add_child(this._label);

        this._switchItem = new PopupMenu.PopupSwitchMenuItem(
            'Block ads',
            this._settings.get_boolean('block-ads')
        );
        this.menu.addMenuItem(this._switchItem);

        this._settingsItem = new PopupMenu.PopupMenuItem('Settings…');
        this.menu.addMenuItem(this._settingsItem);

        this._syncFromSettings();

        this._switchChangedId = this._switchItem.connect('toggled', (_item, state) => {
            this._settings.set_boolean('block-ads', state);
        });

        this._settingsChangedId = this._settings.connect('changed::block-ads', () => {
            if (this._ignoreSetting) {
                return;
            }
            this._syncFromSettings();
            const enabled = this._settings.get_boolean('block-ads');
            this._applyBlockState(enabled).catch(error => logError(error, 'Failed to apply TBlock state'));
        });

        this._settingsItem.connect('activate', () => ExtensionUtils.openPrefs());

        this._initializeState();
    }

    async _initializeState() {
        try {
            const active = await this._tblock.getStatus();
            if (active === null) {
                return;
            }

            if (active !== this._settings.get_boolean('block-ads')) {
                this._withSettingsBlocked(() => this._settings.set_boolean('block-ads', active));
                this._syncFromSettings();
            }
        } catch (error) {
            logError(error, 'Unable to query current TBlock status');
        }
    }

    _withSettingsBlocked(fn) {
        this._ignoreSetting = true;
        try {
            fn();
        } finally {
            this._ignoreSetting = false;
        }
    }

    _setBusy(busy) {
        this._isBusy = busy;
        this._switchItem.setSensitive(!busy);
    }

    async _applyBlockState(enabled) {
        if (this._isBusy) {
            this._pendingState = enabled;
            return;
        }

        this._setBusy(true);
        this._pendingState = null;

        try {
            const result = await this._tblock.setEnabled(enabled);

            if (result.success) {
                return;
            }

            this._notifyFailure(enabled, result);
            this._withSettingsBlocked(() => this._settings.set_boolean('block-ads', !enabled));
            this._syncFromSettings();
        } catch (error) {
            this._notifyFailure(enabled, {stderr: error.message, stdout: '', exitCode: -1});
            this._withSettingsBlocked(() => this._settings.set_boolean('block-ads', !enabled));
            this._syncFromSettings();
            throw error;
        } finally {
            this._setBusy(false);
            if (this._pendingState !== null) {
                const nextState = this._pendingState;
                this._pendingState = null;
                this._applyBlockState(nextState).catch(err =>
                    logError(err, 'Failed to apply queued TBlock state'));
            }
        }
    }

    _notifyFailure(enabled, result) {
        const action = enabled ? 'enable TBlock' : 'disable TBlock';
        const detail = result?.stderr || result?.stdout || 'No additional details provided.';
        Main.notify('gnoMAD', `Failed to ${action}.\n${detail}`);
    }

    _syncFromSettings() {
        const enabled = this._settings.get_boolean('block-ads');
        this._switchItem.setToggleState(enabled);
        this._label.text = enabled ? 'No Ads' : 'Ads';
    }

    destroy() {
        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = 0;
        }

        if (this._switchChangedId) {
            this._switchItem.disconnect(this._switchChangedId);
            this._switchChangedId = 0;
        }

        super.destroy();
    }
});

let indicator;

export default class Extension {
    constructor(metadata) {
        this.metadata = metadata;
    }

    enable() {
        indicator = new Indicator();
        Main.panel.addToStatusArea('no-ads-toggle', indicator, 0, 'right');
    }

    disable() {
        if (indicator) {
            indicator.destroy();
            indicator = null;
        }
    }
}
