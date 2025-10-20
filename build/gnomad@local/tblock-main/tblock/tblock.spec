Name:           tblock
Version:        2.7.5
Release:        1%{?dist}
Summary:        An anti-capitalist ad-blocker that uses the hosts file

License:        GPLv3
URL:            https://tblock.codeberg.page
Source0:        https://codeberg.org/tblock/tblock/archive/%{version}.tar.gz

BuildRequires:  make
BuildRequires:  gzip
BuildRequires:  python
BuildRequires:	python-setuptools
BuildRequires:  python-colorama
BuildRequires:  python-requests
BuildRequires:  python-urllib3
Requires:       python
Requires:       python-colorama
Requires:       python-requests
Requires:       python-urllib3

%description
TBlock is a system-wide, platform independent ad-blocker written in Python and released under GPLv3.

%global debug_package %{nil}

%prep
%autosetup

%build
python3 setup.py build
make build-files

%install
rm -rf %{buildroot}
python3 setup.py install --root=%{buildroot} --optimize=1 --skip-build
install -Dm644 ./extra/scripts/zsh_completion.zsh %{buildroot}/usr/share/zsh/site-functions/_tblock
install -Dm644 ./extra/manuals/tblock.1.gz %{buildroot}/usr/share/man/man1/tblock.1.gz
install -Dm644 ./extra/manuals/tblockc.1.gz %{buildroot}/usr/share/man/man1/tblockc.1.gz
install -Dm644 ./extra/manuals/tblockd.1.gz %{buildroot}/usr/share/man/man1/tblockd.1.gz
install -Dm644 LICENSE %{buildroot}/usr/share/licenses/tblock/LICENSE.txt
install -Dm644 extra/services/systemd/tblockd.service %{buildroot}/usr/lib/systemd/system/tblockd.service
make install-config ROOT=%{buildroot}

%files
%license LICENSE.txt
%config(noreplace) /etc/tblock.conf
/usr/bin/tblock
/usr/bin/tblockc
/usr/bin/tblockd
/usr/share/zsh/site-functions/_tblock
/usr/lib/python3.*/site-packages/tblock/
/usr/lib/python3.*/site-packages/tblock-*-py3.*.egg-info/
/usr/lib/systemd/system/tblockd.service
/usr/share/man/man1/tblock.1.gz
/usr/share/man/man1/tblockc.1.gz
/usr/share/man/man1/tblockd.1.gz

%changelog
* Fri Mar 21 13:57:00 CEST 2025 Twann <tw4nn@disroot.org>
- Release 2.7.5. Consult the changelog here: https://codeberg.org/tblock/tblock/src/branch/main/CHANGELOG.md
