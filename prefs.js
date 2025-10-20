/* Simple preferences for Ads / No Ads Toggle — GNOME Shell 45+ */

import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';

const DEFAULT_SCHEMA = 'org.gnome.shell.extensions.gnomad';

function resolveExtensionDir(metadata) {
    if (!metadata)
        return null;

    if (metadata.dir?.get_child)
        return metadata.dir;

    if (metadata.path)
        return Gio.File.new_for_path(metadata.path);

    return null;
}

function getSettings(metadata, schemaId = metadata?.['settings-schema'] ?? DEFAULT_SCHEMA) {
    const defaultSource = Gio.SettingsSchemaSource.get_default();
    let schemaSource = defaultSource;

    const extensionDir = resolveExtensionDir(metadata);
    const schemaDir = extensionDir?.get_child?.('schemas');
    if (schemaDir?.query_exists(null)) {
        schemaSource = Gio.SettingsSchemaSource.new_from_directory(
            schemaDir.get_path(), defaultSource, false);
    }

    const schema = schemaSource.lookup(schemaId, true);
    if (!schema)
        throw new Error(`Schema ${schemaId} could not be found for extension ${metadata?.uuid ?? 'unknown'}`);

    return new Gio.Settings({settings_schema: schema});
}

export default class NoAdsPrefs {
    constructor(metadata) {
        this._metadata = metadata;
    }

    fillPreferencesWindow(window) {
        const settings = getSettings(this._metadata);

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
