autopip
===========

Easily install apps from PyPI and automatically keep them updated.

FYI Currently supports Python 3.x apps only, but 2.x is coming soon.

To install `autopip` to `/usr/local/bin` for all users (recommended):

.. code-block:: console

    $ sudo pip3 install autopip

    # No need to worry about tainting system Python install as autopip has no install dependencies and never will.
    #
    # If you are concerned about using `sudo`, then you can install it in a virtual environment and obviously
    # that is more steps and not available to other users:
    # 1) python3 -m venv ~/.virtualenvs/autopip
    # 2) source ~/.virtualenvs/autopip/bin/activate
    # 3) pip3 install autopip

Now, you can easily install any apps from PyPI without having to manage virtualenvs or re-run ``pip`` again to update as
``autopip`` does all that for you automatically -- one virtualenv per app version and auto-updated atomically and hourly
via cron service whenever a new version is released:

.. code-block:: console

    $ autopip install workspace-tools
    Installing workspace-tools to /usr/local/opt/apps/workspace-tools/3.2.2
    Updating symlinks in /usr/local/bin
    + wst

    # Install paths are selected based on your user's permission to write to /opt or /usr/local/opt.
    # If you do not have permission for either, then autopip will install to your user home at ~/.apps,
    # therefore you will need to add ~/.apps/bin to your PATH env var to easily run scripts from installed apps.
    # To install script symlinks to /usr/local/bin, either chmod/chown dirs in /usr/local/* to be writeable by
    # your user or run `autopip` using `sudo`.

To show currently installed apps and their scripts:

.. code-block:: console

    $ autopip list --scripts
    ansible-hostmanager  0.2.3   /usr/local/opt/apps/ansible-hostmanager/0.2.3
                                 /usr/local/bin/ah
    workspace-tools      3.2.2   /usr/local/opt/apps/workspace-tools/3.2.2
                                 /usr/local/bin/wst

To uninstall::

    autopip uninstall workspace-tools

To save typing a few letters, you can also use the ``app`` alias -- short for **a**\ uto\ **p**\ i\ **p** -- instead of
``autopip``. And you can even keep `autopip` updated automatically by installing itself:

.. code-block:: console

    $ sudo app install autopip
    Installing autopip to /opt/apps/autopip/0.2.4
    Updating symlinks in /usr/local/bin
    * app (updated)
    * autopip (updated)

Now, that's convenience! ;)

To control versioning and uniform installations across multiple hosts/users, you can also define an `autopip`
installation group using entry points. See example in `developer-tools https://pypi.org/project/developer-tools/`_
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
