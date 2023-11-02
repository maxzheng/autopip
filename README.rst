autopip
===========

Easily install apps from PyPI and automatically keep them updated.

`autopip` automates the creation of a virtual environment using `venv <https://docs.python.org/3/library/venv.html>`_,
installs any Python package with scripts (i.e. app) from PyPI using `pip <https://pypi.org/project/pip/>`_, and
atomically creates symlinks for installed scripts in `/usr/local/bin` so you can easily use them. Each app version is
installed cleanly into its own virtual environment. Optionally, it can set up crontab entries to update apps
automatically (may require admin permission on macOS).

Before starting, make sure your Python installation meets all the requirements -- while `autopip` can install Python
apps that run on any Python version, it requires Python 3.6+ to run::

    curl -s https://raw.githubusercontent.com/maxzheng/autopip/master/etc/check-python.py | python3

To install `autopip` to `/usr/local/bin`::

    sudo pip3 install autopip

No need to worry about tainting system Python install as `autopip` has no install dependencies and never will.

Alternatively, you can install it in a virtual environment -- the last one that you will ever create manually for
installing Python apps::

    python3 -m venv ~/.virtualenvs/autopip
    source ~/.virtualenvs/autopip/bin/activate
    pip3 install autopip

Optionally, create installation directories and chown to your user so that ``autopip`` can create symlinks in
`/usr/local/bin`::

    sudo mkdir /usr/local/opt /usr/local/var
    sudo chown -R $(whoami) /usr/local/*

Now, you can easily install any apps from PyPI:

.. code-block:: console

    $ autopip install workspace-tools
    Installing workspace-tools to /usr/local/opt/apps/workspace-tools/3.2.2
    Updating symlinks in /usr/local/bin
    + wst

Optionally use the ``--update`` option to update it daily via cron (may require admin permission on macOS):

.. code-block:: console

    $ autopip install workspace-tools --update daily
    workspace-tools is up-to-date
    Adding to crontab (may require admin permission)
    Daily auto-update enabled via cron service
    Scripts are in /usr/local/bin: wst

Install paths are selected based on your user's permission to write to `/opt` or `/usr/local/opt`. If you do not have
permission for either, then ``autopip`` will install apps to your user home at `~/.apps` with script symlinks in `~/bin`
therefore you will need to add `~/bin` to your PATH env var to easily run scripts from installed apps.  To install
script symlinks to `/usr/local/bin`, either chown/chmod dirs in `/usr/local/*` to be writeable by your user as suggested
above or run ``autopip`` using ``sudo`` (i.e. as root). To see why a particular path is selected, append ``--debug``
after ``autopip`` when running it.

To save typing a few letters, you can also use the ``app`` alias -- short for **a**\ uto\ **p**\ i\ **p**.

.. code-block:: console

    $ app install ansible-hostmanager
    Installing ansible-hostmanager to /usr/local/opt/apps/ansible-hostmanager/0.2.3
    Updating script symlinks in /usr/local/bin
    + ah

To install an app for a specific Python version, use the ``--python`` option:

.. code-block:: console

    $ app install ducktape --python 3.7
    Installing ducktape to /usr/local/opt/apps/ducktape/0.7.3
    Updating script symlinks in /usr/local/bin
    + ducktape

To show currently installed apps and their scripts:

.. code-block:: console

    $ app list --scripts
    ansible-hostmanager  0.2.3   /usr/local/opt/apps/ansible-hostmanager/0.2.3
                                 /usr/local/bin/ah
    ducktape             0.7.3   /usr/local/opt/apps/ducktape/0.7.3
                                 /usr/local/bin/ducktape
    workspace-tools      3.2.2   /usr/local/opt/apps/workspace-tools/3.2.2      [updates daily]
                                 /usr/local/bin/wst

To manually update all apps:

.. code-block:: console

    $ app update
    ansible-hostmanager is up-to-date
    ducktape is up-to-date
    workspace-tools is up-to-date

To uninstall::

    app uninstall ducktape

If you need to use a private PyPI index, just configure `index-url` in `pip.conf
<https://pip.pypa.io/en/stable/user_guide/#configuration>`_ as `autopip` uses `pip` to install apps.

To control versioning and uniform installations across multiple hosts/users, you can also define an `autopip`
installation group using entry points. See example in `developer-tools <https://pypi.org/project/developer-tools/>`_
package.

FAQ
===

1. Cron jobs have a random minute set during install and runs hourly for all intervals.
2. Up to two versions of an app is kept at a time.

Links & Contact Info
====================

| PyPI Package: https://pypi.python.org/pypi/autopip
| GitHub Source: https://github.com/maxzheng/autopip
| Report Issues/Bugs: https://github.com/maxzheng/autopip/issues
|
| Follow: https://twitter.com/MaxZhengX
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
