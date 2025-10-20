#!/bin/sh

__update_006__ ()
{
    echo "=== STARTING UPGRADE TEST ==="
    echo "-> Installing tblock 0.0.6"
    pip install tblock==0.0.6
    tblock -v
    pip uninstall tblock -y
    echo "-> Upgrading to tblock 1.2.0"
    pip install tblock==1.2.0
    tblock -v
    pip uninstall tblock -y
    echo "-> Upgrading to tblock 1.3.2"
    pip install tblock==1.3.2
    tblock -v
    pip uninstall tblock -y
    echo "-> Upgrading to tblock 2.3.0"
    pip install tblock==2.3.0
    tblock -Hn
    pip uninstall tblock -y
    echo "-> Upgrading to tblock 2.4.1"
    pip install tblock==2.4.1
    tblock -Hn
    pip uninstall tblock -y
    echo "-> Upgrading to latest commit on current branch"
    python3 setup.py install
    tblock -Hn
    tblock -Dn
    rm -rf /var/lib/tblock /var/log/tblock /tmp/tblock
    echo "=== END UPGRADE TEST ==="
}


__install_now__ ()
{
    echo "=== STARTING INSTALLATION TEST ==="
    python3 setup.py install
    tblock -Syn tblock-base
    echo "=== END INSTALLATION TEST ==="
}

__update_006__
__install_now__
