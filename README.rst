autopip
===========

Easily install apps from PyPI and automatically keep them updated.

FYI Currently supports Python 3.x apps only, but 2.x is coming soon.

To install `autopip` to `/usr/local/bin` for all users (recommended)::

    sudo pip3 install autopip

No need to worry about tainting system Python install as autopip has no install dependencies and never will.
Alternatively, you can install it in a virtual environment and obviously that is not available to other users::

    python3 -m venv ~/.virtualenvs/autopip
    source ~/.virtualenvs/autopip/bin/activate
    pip3 install autopip

Now, you can easily install any apps from PyPI without having to manage virtualenvs or re-run ``pip`` again to update as
``autopip`` does all that for you automatically -- one virtualenv per app version and auto-updated atomically and hourly
via cron service whenever a new version is released:

.. code-block:: console

    $ autopip install workspace-tools
    Installing workspace-tools to /usr/local/opt/apps/workspace-tools/3.2.2
    Auto-update enabled via cron service
    Updating symlinks in /usr/local/bin
    + wst

Install paths are selected based on your user's permission to write to `/opt` or `/usr/local/opt`. If you do not have
permission for either, then autopip will install to your user home at `~/.apps`, therefore you will need to add
`~/.apps/bin` to your PATH env var to easily run scripts from installed apps.  To install script symlinks to
`/usr/local/bin`, either chmod/chown dirs in `/usr/local/*` to be writeable by your user or run `autopip` using `sudo`.
To see why a particular path is selected, append ``--debug`` after ``autopip`` when running it.

To save typing a few letters, you can also use the ``app`` alias -- short for **a**\ uto\ **p**\ i\ **p** -- instead of
``autopip``. It is the same as ``autopip`` except it does not auto-update unless you provide a value to ``--update``
option (e.g. hourly (same as ``autopip``), daily, weekly, monthly)

.. code-block:: console

    $ app install ansible-hostmanager
    Installing ansible-hostmanager to /usr/local/opt/apps/ansible-hostmanager/0.2.3
    Updating script symlinks in /usr/local/bin
    + ah

To show currently installed apps and their scripts:

.. code-block:: console

    $ app list --scripts
    ansible-hostmanager  0.2.3   /usr/local/opt/apps/ansible-hostmanager/0.2.3
                                 /usr/local/bin/ah
    workspace-tools      3.2.2   /usr/local/opt/apps/workspace-tools/3.2.2      [updates hourly]
                                 /usr/local/bin/wst

To uninstall::

    app uninstall workspace-tools

And you can even keep `autopip` updated automatically by installing itself:

.. code-block:: console

    $ sudo autopip install autopip
    Installing autopip to /opt/apps/autopip/0.2.4
    Updating symlinks in /usr/local/bin
    * app (updated)
    * autopip (updated)

Now, that's convenience! ;)

To control versioning and uniform installations across multiple hosts/users, you can also define an `autopip`
installation group using entry points. See example in `developer-tools <https://pypi.org/project/developer-tools/>`_
package.

If you need to use a private PyPI index, just configure `index-url` in `~/.pip/pip.conf
<https://pip.pypa.io/en/stable/user_guide/#configuration>`_ as `autopip` simply uses `pip` under the hood.

Links & Contact Info
====================

| PyPI Package: https://pypi.python.org/pypi/autopip
| GitHub Source: https://github.com/maxzheng/autopip
| Report Issues/Bugs: https://github.com/maxzheng/autopip/issues
|
| Follow: https://twitter.com/MaxZhengX
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
