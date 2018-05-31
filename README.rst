autopip
===========

Easily install apps from PyPI and automatically keep them updated.

FYI Currently supports Python 3.x apps only, but 2.x is coming soon.

To install::

    # For all users -- this is safe as autopip has no install dependencies and never will.
    sudo pip install autopip

Now, you can easily install any apps from PyPI without having to manage virtualenvs or re-run pip again to update as
autopip does all that for you automatically -- one virtualenv per app and auto-updated atomically and hourly via cron
service whenever a new version is released::

    sudo autopip install workspace-tools

To show currently installed apps and their scripts:

.. code-block:: shell

    $ sudo autopip list --scripts
    ansible-hostmanager  0.2.3   /opt/apps/ansible-hostmanager/0.2.3
                                 /usr/local/bin/ah
    workspace-tools      3.2.2   /opt/apps/workspace-tools/3.2.2
                                 /usr/local/bin/wst

To uninstall::

    sudo autopip uninstall workspace-tools

If you need to use a private PyPI index, just configure `index-url` in `~/.pip/pip.conf`

Links & Contact Info
====================

| PyPI Package: https://pypi.python.org/pypi/autopip
| GitHub Source: https://github.com/maxzheng/autopip
| Report Issues/Bugs: https://github.com/maxzheng/autopip/issues
|
| Follow: https://twitter.com/MaxZhengX
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
