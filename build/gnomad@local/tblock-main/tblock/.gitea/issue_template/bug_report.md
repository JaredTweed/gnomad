---

name: "Bug Report"
about: "There is a bug in the software!"
title: "BUG: A clear and short title"
ref: "main"
labels:
- "Kind: Bug"
- "Status: Needs triage"
- "Priority: High"

---

<!--
First of all, thanks for reporting the bug that you found!

To avoid losing some precious time, we ask that you read this carefully before opening the issue.

Before opening, please ensure that:
- This issue is not duplicated.
- You are running the latest STABLE version of TBlock (if unsure, visit https://codeberg.org/tblock/tblock/releases/latest).
- The issue is related to the command-line version of TBlock (either the 'tblock', 'tblockc' or 'tblockd' command).
- If the issue is related to TBlock GUI, please report it at: https://codeberg.org/tblock/tblock-gui/issues.
- If unsure whether the issue is related to TBlock or TBlock GUI, you can report it here.
-->

<!--
BUG DESCRIPTION

Please write a clear and concise description below this comment.
What we are trying to know here is what you were trying to do, and what went wrong.
The more details you provide, the faster we will be able to help.

BAD examples are (please don't do that, there is not enough relevant information to do anything):

- "The software crashes."
- "It does not work."

A GOOD example would be (it is entirely fictional though):

- "The software crashes when trying to subscribe to a filter list (for the first time on a new installation), right after finishing downloading it."
-->

### Steps to reproduce

- This issue is repoducible: `yes/no`
<!-- 
If it is reproducible, enter the steps to reproduce it below
-->

1. Do something
2. Do something else
3. See error


### Error code

- This issue results in TBlock to crash: `yes/no`
<!-- 
If so, please enter the output of your terminal emulator below
-->

```

```

### Possible solutions or causes
<!--
If you think that you found out the cause, you can write your ideas about it or how to fix it in this section.
Otherwise, you leave it blank or delete it.
-->


### System information
<!--
This section is not mandatory, but they can be really helpful in some cases.
If, however, you don't wish to disclose such information, you are free to delete this section.
-->

I am running TBlock on:
- [ ] GNU/Linux, Linux: `distribution`, `init` <!-- If you don't know which init system you use, it is probably "systemd" -->
- [ ] macOS: `version`
- [ ] Microsoft Windows: `version`
- [ ] *BSD
- [ ] Android: `version`, using Termux: `version`
- [ ] Other: `name`, `version`

I installed TBlock on my machine with:
- [ ] My distribution's official package repository
- [ ] AUR/Chaotic-AUR
- [ ] Fedora COPR
- [ ] Ubuntu PPA
- [ ] Debian package
- [ ] Homebrew
- [ ] Scoop
- [ ] Windows EXE installer
- [ ] Python pip
- [ ] Manually (with `make`) from the latest tag
- [ ] Manually (with `make`) from the main branch


The output of `tblock -Lk` is the following:

```

```

The output of `tblock -s` is the following:

```

```

### Logs
<!-- 
If you want, you can attach TBlock's log file for more information.
This is not required, but it can be useful for some bugs.
Feel free to delete this section if you don't want to provide your log file.

Under UNIX-like systems, you can find the log file under:
-> /var/log/tblock.log

Under Android with Termux, you can find the log file under:
-> /data/data/com.termux/files/usr/var/log/tblock.log

Under Windows, you can find the log file under:
-> %ALLUSERSPROFILE%\TBlock\tblock.log
-->
