EXTENSION_ID := gnomad@local
EXTENSION_INSTALL_DIR ?= $(HOME)/.local/share/gnome-shell/extensions/$(EXTENSION_ID)
TARGET_DIR := $(DESTDIR)$(EXTENSION_INSTALL_DIR)

INSTALL_FILES := extension.js metadata.json prefs.js
INSTALL_DIRS := schemas tblock

GLIB_COMPILE_SCHEMAS ?= glib-compile-schemas
ZIP ?= zip

BUILD_DIR := build
STAGING_DIR := $(BUILD_DIR)/$(EXTENSION_ID)
PACKAGE := $(BUILD_DIR)/gnomad.zip

.PHONY: install install-now uninstall pack clean

install:
	@echo "Installing extension to $(TARGET_DIR)"
	@set -e; \
	rm -rf "$(TARGET_DIR)"; \
	install -d "$(TARGET_DIR)"; \
	for file in $(INSTALL_FILES); do \
		install -Dm644 "$$file" "$(TARGET_DIR)/$$file"; \
	done; \
	for dir in $(INSTALL_DIRS); do \
		cp -R "$$dir" "$(TARGET_DIR)/"; \
	done; \
	if ! command -v "$(GLIB_COMPILE_SCHEMAS)" >/dev/null 2>&1; then \
		echo "Error: glib-compile-schemas not found in PATH." >&2; \
		exit 1; \
	fi; \
	"$(GLIB_COMPILE_SCHEMAS)" "$(TARGET_DIR)/schemas"

install-now: install
	@echo "Restarting GNOME Shell"
	@if command -v busctl >/dev/null 2>&1; then \
		result="$$(busctl --user call org.gnome.Shell /org/gnome/Shell org.gnome.Shell Eval s 'global.reexec_self();')" || exit $$?; \
		if printf '%s\n' "$$result" | grep -q ' true '; then \
			printf '%s\n' "$$result"; \
		else \
			printf 'GNOME Shell declined to restart (likely Wayland). Please log out/in or restart the session manually.\n' >&2; \
		fi; \
	elif command -v dbus-send >/dev/null 2>&1; then \
		if dbus-send --session --type=method_call --dest=org.gnome.Shell /org/gnome/Shell org.gnome.Shell.Eval string:'global.reexec_self();'; then \
			:; \
		else \
			printf 'GNOME Shell declined to restart. Please log out/in or restart the session manually.\n' >&2; \
		fi; \
	else \
		echo "Error: unable to restart GNOME Shell (busctl or dbus-send not found)." >&2; \
		exit 1; \
	fi

uninstall:
	@echo "Removing extension from $(TARGET_DIR)"
	@rm -rf "$(TARGET_DIR)"

pack: $(PACKAGE)

$(PACKAGE): $(STAGING_DIR)
	@echo "Creating package $(PACKAGE)"
	@cd "$(BUILD_DIR)" && "$(ZIP)" -rq "$(notdir $(PACKAGE))" "$(EXTENSION_ID)"

$(STAGING_DIR):
	@echo "Staging extension in $(STAGING_DIR)"
	@$(MAKE) install DESTDIR= EXTENSION_INSTALL_DIR="$(STAGING_DIR)"

clean:
	@echo "Cleaning build artifacts"
	@rm -rf "$(BUILD_DIR)"
