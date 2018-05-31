autopip
===========

Easily install apps from PyPI and automatically keep them updated.

FYI Currently supports Python 3.x apps only, but 2.x is coming soon.

To install `autopip` to `/usr/local/bin` for all users (recommended)::

    sudo pip3 install autopip

    # NOTE: You should only use sudo to install packages that you trust, therefore you are welcome to skip sudo.
    # If you do skip sudo, then I suggest installing it in a virtual environment.
    #
    # And no need to worry about tainting system Python install as autopip has no install dependencies and never will.

Now, you can easily install any apps from PyPI without having to manage virtualenvs or re-run ``pip`` again to update as
``autopip`` does all that for you automatically -- one virtualenv per app version and auto-updated atomically and hourly
via cron service whenever a new version is released:

.. code-block:: console

    $ autopip install workspace-tools
    Installing workspace-tools to /usr/local/opt/apps/workspace-tools/3.2.2
    Updating symlinks in /usr/local/bin
    + wst

    # NOTE: If you do not have permission to write to /usr/local/[bin|opt|var/log], then autopip will install to your
    # user home at ~/.apps instead of /usr/local, therefore you will need to add ~/.apps/bin to your PATH env var to
    # easily run scripts from installed apps.

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
    Installing autopip to /usr/local/opt/apps/autopip/0.0.5
    Updating symlinks in /usr/local/bin
    * app (updated)
    * autopip (updated)

Now, that's convenience! ;)

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
