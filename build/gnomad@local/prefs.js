/* Simple preferences for Ads / No Ads Toggle — GNOME Shell 45+ */

import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';
import * as ExtensionUtils from 'resource:///org/gnome/shell/misc/extensionUtils.js';

function getSettings() {
    return ExtensionUtils.getSettings('org.gnome.shell.extensions.gnomad');
}

export default class NoAdsPrefs {
    constructor(metadata) {
        this.metadata = metadata;
    }

    fillPreferencesWindow(window) {
        const settings = getSettings();

        const page = new Adw.PreferencesPage();
        const group = new Adw.PreferencesGroup({ title: 'General' });

        const row = new Adw.ActionRow({
            title: 'Block ads',
            subtitle: 'Controls whether the panel shows “No Ads” (on) or “Ads” (off).',
        });
        const sw = new Gtk.Switch({ valign: Gtk.Align.CENTER });

        settings.bind('block-ads', sw, 'active', Gio.SettingsBindFlags.DEFAULT);

        row.add_suffix(sw);
        row.activatable_widget = sw;

        group.add(row);
        page.add(group);
        window.add(page);
    }
}

export function init(metadata) {
    return new NoAdsPrefs(metadata);
}
