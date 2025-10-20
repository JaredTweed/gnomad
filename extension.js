/*
 * Ads / No Ads Toggle — GNOME Shell 45+
 * Places a tiny text indicator in the top bar that reads "No Ads" (when ON)
 * or "Ads" (when OFF). Clicking opens a minimal menu with a single toggle and
 * a Settings button. State is persisted in GSettings and mirrored to TBlock.
 */

import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GObject from 'gi://GObject';
import St from 'gi://St';

import {Extension as ExtensionBase} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const INDICATOR_STYLE = 'no-ads-toggle-label';
const TBLOCK_BASE_ARGS = ['--quiet', '--no-prompt'];

class TBlockCommandRunner {
    constructor(extensionDir) {
        const tblockDir = extensionDir?.get_child('tblock');

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
    constructor(extensionDir) {
        this._runner = new TBlockCommandRunner(extensionDir);
    }

    async setEnabled(enabled) {
        const op = enabled ? '--enable' : '--disable';
        return await this._runner.runQueued([...TBLOCK_BASE_ARGS, op]);
    }

    async buildHosts() {
        return await this._runner.runQueued([...TBLOCK_BASE_ARGS, '--build']);
    }

    async getStatus() {
        const result = await this._runner.runQueued(['--status', '--quiet'], {requireRoot: false});
        if (!result.success) {
            return {...result, active: null};
        }

        const match = result.stdout?.match(/Protection:\s*(active|inactive)/i);
        if (!match) {
            return {...result, success: false, active: null};
        }

        return {...result, active: match[1].toLowerCase() === 'active'};
    }
}

const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, 'Ads / No Ads Toggle');

        this._extension = extension;
        this._settings = extension.getSettings();
        this._tblock = new TBlockClient(extension.dir);
        this._ignoreSetting = false;
        this._isBusy = false;
        this._pendingState = null;
        this._lastStatusErrorDetail = null;

        this._label = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
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

        this._settingsItem.connect('activate', () => this._extension.openPreferences());

        this._initializeState();
    }

    async _initializeState() {
        try {
            const status = await this._tblock.getStatus();
            if (!status.success) {
                this._handleStatusError('during initialization', status, {notify: false});
                this._syncFromSettings();
                return;
            }

            this._lastStatusErrorDetail = null;

            const active = status.active ?? false;
            if (active !== this._settings.get_boolean('block-ads')) {
                this._updateSettingSilently(active);
            } else {
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

    _updateSettingSilently(value) {
        const current = this._settings.get_boolean('block-ads');
        if (current === value) {
            this._syncFromSettings();
            return;
        }

        this._withSettingsBlocked(() => this._settings.set_boolean('block-ads', value));
        this._syncFromSettings();
    }

    _getResultDetail(result) {
        const stderr = result?.stderr?.trim();
        const stdout = result?.stdout?.trim();
        return stderr || stdout || 'No additional details provided.';
    }

    _handleStatusError(context, result, {notify = true} = {}) {
        const detail = this._getResultDetail(result);
        if (notify) {
            if (this._lastStatusErrorDetail === detail) {
                return;
            }
            this._lastStatusErrorDetail = detail;
        }
        if (notify) {
            const location = context ? ` ${context}` : '';
            Main.notify(
                'gnoMAD',
                `Unable to determine TBlock status${location}.\n${detail}\nInitialise TBlock (for example by running "tblock --build" with administrator privileges) and try again.`
            );
        } else {
            log(`Unable to determine TBlock status ${context ?? ''}: ${detail}`);
        }
    }

    _notifyStatusMismatch(requestedEnabled, actualActive) {
        const action = requestedEnabled ? 'enable TBlock' : 'disable TBlock';
        const stateText = actualActive ? 'active' : 'inactive';
        const suggestion = requestedEnabled
            ? 'Try running "tblock --build" with administrator privileges, then toggle the switch again.'
            : 'Try running "tblock --disable" with administrator privileges, then toggle the switch again.';

        Main.notify(
            'gnoMAD',
            `TBlock still reports protection as ${stateText} after attempting to ${action}.\n${suggestion}`
        );
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

            if (!result.success) {
                this._notifyFailure(enabled, result);
                this._updateSettingSilently(!enabled);
                return;
            }

            let status = await this._tblock.getStatus();
            if (!status.success) {
                this._handleStatusError('while checking status', status);
                return;
            }

            this._lastStatusErrorDetail = null;

            if (status.active !== enabled) {
                if (enabled) {
                    const buildResult = await this._tblock.buildHosts();
                    if (!buildResult.success) {
                        this._notifyFailure(
                            enabled,
                            buildResult,
                            'TBlock protection stayed inactive. Rebuilding the hosts file failed.'
                        );
                        this._updateSettingSilently(false);
                        return;
                    }

                    status = await this._tblock.getStatus();
                    if (!status.success) {
                        this._handleStatusError('after rebuilding the hosts file', status);
                        return;
                    }

                    this._lastStatusErrorDetail = null;

                    if (!status.active) {
                        this._notifyStatusMismatch(true, status.active);
                        this._updateSettingSilently(status.active ?? false);
                        return;
                    }
                } else {
                    this._notifyStatusMismatch(false, status.active);
                    this._updateSettingSilently(status.active ?? false);
                    return;
                }
            }

            this._updateSettingSilently(enabled);
        } catch (error) {
            this._notifyFailure(enabled, {stderr: error.message, stdout: '', exitCode: -1});
            this._updateSettingSilently(!enabled);
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

    _notifyFailure(enabled, result, message = null) {
        const action = enabled ? 'enable TBlock' : 'disable TBlock';
        const detail = message ?? this._getResultDetail(result);
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

export default class Extension extends ExtensionBase {
    constructor(metadata) {
        super(metadata);
        this._indicator = null;
    }

    enable() {
        this._indicator = new Indicator(this);
        Main.panel.addToStatusArea('no-ads-toggle', this._indicator, 0, 'right');
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
