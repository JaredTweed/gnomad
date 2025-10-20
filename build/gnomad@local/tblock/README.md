<p align="center">
<img align="center" width="120px" height="120px" src="https://codeberg.org/tblock/tblock/raw/commit/268dfede8ce8382bb906adb954203c92ce0c877d/extra/icons/tblock.svg" alt="TBlock icon">
</p>
<p align="center">
<h1 align="center">TBlock</h1>
</p>
<p align="center">TBlock is a free and open-source system-wide ad-blocker that uses the hosts file.</p>
<p align="center">
<a href="https://codeberg.org/teaserbot-labs/delightful-humane-design"><img src="https://codeberg.org/tblock/tblock/raw/branch/main/extra/icons/humane-tech-badge.svg" alt="Awesome Humane Tech"></a>
<img src="https://codeberg.org/tblock/tblock/raw/commit/452ce14991661b25434011fe18558ec2557fb741/extra/icons/trans-rights-badge.svg" alt="Trans rights now!">
<a href="https://nogithub.codeberg.page"><img src="https://nogithub.codeberg.page/badge.svg" alt="Please don't upload to GitHub"></a>
</p>

> To view the repository for the graphical user interface, [click here](https://codeberg.org/tblock/tblock-gui).

## Installation

### In a Python environment

You can easily install TBlock with:

```sh
pipx install tblock
```

### On Arch Linux/Arch-based distributions

TBlock is available in the Arch User Repository (AUR), and it can be installed with the AUR-helper of your choice. For example with paru:

```sh
paru -S tblock
```

### On Ubuntu

An official PPA provides packages for TBlock and TBlock GUI. It can be added with:

```sh
sudo add-apt-repository ppa:twann4/tblock
```

Then TBlock can be installed with:

```sh
sudo apt update
sudo apt install tblock
```

### On Debian

Unfortunately, we do not yet provide a repository for the Debian packages. However, such packages are available on the [releases page](https://codeberg.org/tblock/tblock/releases).

### On Fedora

A COPR repository is available for Fedora. It provides both TBlock and TBlock GUI, and can be enabled with:

```sh
sudo dnf copr enable twann/tblock
```

Then, TBlock can be installed with:

```sh
sudo dnf install tblock
```

### Windows & macOS

Due to a lack of time, I am currently unable to provide updates for the Windows and macOS builds. I am deeply sorry about this and hope to find the time to do so again as soon as possible. If you would like to help, please feel welcome to do so!

### Other systems

More installation methods — such as Windows installer and packages for Linux distributions — can be found [on the website](https://tblock.me/get).

## Usage

After installing, you need to setup TBlock in order to enable protection against ads and trackers:

```sh
tblock --init
```

You can learn more by reading [the documentation](https://docs.tblock.me/).

## Demo

[![asciicast](https://asciinema.org/a/589465.svg)](https://asciinema.org/a/589465)

## Roadmap

Here is a list of the upcoming changes in TBlock code. Suggestions are, of course, welcome.

- [x] Implement [a GUI for TBlock](https://codeberg.org/tblock/tblock-gui)
- [ ] Rewrite the entire code, make a clearer public API and publish release 3.0.0

## Contributing

Everyone is welcome to contribute to TBlock in different ways. Bug reports can be made directly from the [issue tracker](https://codeberg.org/tblock/tblock/issues), by sending an email to the team or in [our Matrix room](https://matrix.to/#/#tblock:envs.net).

If you want to suggest a modification in the code, you can [open a pull request](https://codeberg.org/tblock/tblock/pulls) or send your patch using email or Matrix.

If you want to be a beta-tester, you can install the latest beta version from our [release page](https://codeberg.org/tblock/tblock/releases) and contact us to give a feedback.

You can find more information on how to contribute [here](https://codeberg.org/tblock/tblock/src/branch/main/CONTRIBUTING.md).

## Support

The best way to support is to [contribute](#contributing). Currently, we no longer accept donations.

## Authors and acknowledgment

TBlock is currently mainained by [Camelia](https://codeberg.org/camelia), who is also its creator.
A big thank you to all the people [who contribute(d) to the project](https://codeberg.org/tblock/tblock/src/branch/main/CONTRIBUTORS.md).

## Credits

Here is a list of all libraries used in the project:

| Name                                                         | Author           | License    |
| ------------------------------------------------------------ | ---------------- | ---------- |
| [colorama](https://github.com/tartley/colorama)              | Jonathan Hartley | BSD        |
| [requests](https://requests.readthedocs.io/)                 | Kenneth Reitz    | Apache 2.0 |
| [urllib3](https://urllib3.readthedocs.io/)                   | Andrey Petrov    | MIT        |
| [argumentor](https://codeberg.org/camelia/python-argumentor) | Camelia Lavender | LGPLv3     |

It is also worth mentioning [pacman](https://archlinux.org/pacman/), from which TBlock's command-line design is highly inspired.

## Contact

- [Mastodon](https://floss.social/@tblock)
- [Matrix](https://matrix.to/#/#tblock:matrix.org)
- [XMPP](xmpp:tblockproject@chat.disroot.org?join)

## License

[![GPLv3](https://www.gnu.org/graphics/gplv3-with-text-136x68.png)](https://www.gnu.org/licenses/gpl-3.0)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
