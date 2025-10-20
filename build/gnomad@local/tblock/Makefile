#!/usr/bin/make -j2

PYTHON ?= /usr/bin/python3
ROOT ?= /
DESTDIR ?= $(ROOT)/usr

.PHONY: all
all: build build-files

.PHONY: clean
clean:
	rm -rf build dist ./extra/manuals/*.1.gz *.egg-info tblock/__pycache__ tblock/*/__pycache__ test/__pycache__ test/fake_root *.bin

# Build rules

build:
	$(PYTHON) -m build --wheel --no-isolation

dist:
	$(PYTHON) -m build

.PHONY: build-files
build-files: extra/manuals/tblock.1.gz extra/manuals/tblockc.1.gz extra/manuals/tblockd.1.gz

extra/manuals/tblock.1.gz:
	gzip -k9 ./extra/manuals/tblock.1

extra/manuals/tblockc.1.gz:
	gzip -k9 ./extra/manuals/tblockc.1

extra/manuals/tblockd.1.gz:
	gzip -k9 ./extra/manuals/tblockd.1

# Test rules

.PHONY: test
test:
	$(PYTHON) -V
	+make test-unit test-security test-lint

.PHONY: test-unit
test-unit:
	/bin/sh test/server.sh --restart
	$(PYTHON) -m pytest -v
	/bin/sh test/server.sh --stop

.PHONY: test-security
test-security:
	$(PYTHON) -m bandit -r tblock -c .bandit.yml

.PHONY: test-lint
test-lint:
	$(PYTHON) -m flake8 tblock

# Installation rules

.PHONY: install
install: all install-files install-python

.PHONY: install-files
install-files: build-files
	install -Dm644 ./extra/scripts/zsh_completion.zsh $(DESTDIR)/share/zsh/site-functions/_tblock
	install -Dm644 ./extra/manuals/tblock.1.gz $(DESTDIR)/share/man/man1/tblock.1.gz
	install -Dm644 ./extra/manuals/tblockc.1.gz $(DESTDIR)/share/man/man1/tblockc.1.gz
	install -Dm644 ./extra/manuals/tblockd.1.gz $(DESTDIR)/share/man/man1/tblockd.1.gz
	install -Dm644 LICENSE $(DESTDIR)/share/licenses/tblock/LICENSE.txt
	install -Dm644 extra/services/systemd/tblockd.service $(DESTDIR)/lib/systemd/system/tblockd.service
	install -Dm755 extra/services/openrc/tblockd.initd $(ROOT)/etc/init.d/tblockd
	install -Dm755 extra/services/runit/tblockd.run $(ROOT)/etc/runit/sv/tblockd/run
	install -Dm644 extra/services/dinit/tblockd $(ROOT)/etc/dinit.d/tblockd

.PHONY: install-python
install-python: 
	$(PYTHON) -m installer --destdir="$(ROOT)" dist/*.whl

.PHONY: install-config
install-config:
	install -Dm644 extra/config/tblock.conf $(ROOT)/etc/tblock.conf

# Uninstallation rules

.PHONY: uninstall
uninstall:
	rm -f $(DESTDIR)/bin/tblock
	rm -f $(DESTDIR)/bin/tblockc
	rm -f $(DESTDIR)/bin/tblockd
	rm -f $(DESTDIR)/share/zsh/site-functions/_tblock
	rm -rf $(DESTDIR)/lib/python3.*/site-packages/tblock
	rm -rf $(DESTDIR)/lib/python3.*/site-packages/tblock-*.dist-info
	rm -rf $(DESTDIR)/lib/python3.*/site-packages/tblock-*.egg-info
	rm -f $(DESTDIR)/share/man/man1/tblock.1.gz
	rm -f $(DESTDIR)/share/man/man1/tblockc.1.gz
	rm -f $(DESTDIR)/share/man/man1/tblockd.1.gz
	rm -f $(DESTDIR)/share/man/man5/tblock.conf.5.gz
	rm -f $(DESTDIR)/share/licenses/tblock/LICENSE.txt
	rm -f $(DESTDIR)/lib/systemd/system/tblockd.service
	rm -f $(ROOT)/etc/init.d/tblockd
	rm -f $(ROOT)/etc/runit/sv/tblockd/run
	rm -f $(ROOT)/etc/dinit.d/tblockd

.PHONY: uninstall-config
uninstall-config:
	rm -f $(ROOT)/etc/tblock.conf

# Help rules

.PHONY: help
help:
	@echo -e  "usage: make [command]\n\n[commands]\n" \
			  "all\t\t\tBuild everything\n" \
			  "build\t\t\tBuild python package\n" \
			  "build-files\t\tBuild manual pages\n" \
			  "clean\t\t\tClean workspace\n" \
			  "dist\t\t\tBuild distribution package\n" \
			  "help\t\t\tShow this help\n" \
			  "install\t\tInstall everything\n" \
			  "install-config\t\tInstall config template\n" \
			  "install-files\t\tInstall manuals, scripts and services\n" \
			  "install-python\t\tInstall python package\n" \
			  "test\t\t\tExecute all tests\n" \
			  "test-lint\t\tExecute linter tests\n" \
			  "test-security\t\tExecute security tests\n" \
			  "test-unit\t\tExecute unit tests\n" \
			  "uninstall\t\tUninstall everything\n" \
			  "uninstall-config\tDelete configuration\n" \
			  "\n---\n\nIf you are packaging this software for personal use, you will typically use:\n" \
			  "> make\n > make install\n" \
			  "\nAnd alternatively install a config template with:\n" \
			  "> make install-config"
