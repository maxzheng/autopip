Version 1.6.0
================================================================================

* Skip blank/invalid lines

Version 1.5.9
================================================================================

* Support reading credentials from .netrc
* Fix style issues
* Update pythonpackage.yml
* Trigger job
* Update pythonpackage.yml

Version 1.5.8
--------------------------------------------------------------------------------

* Add app to check if waiting

Version 1.5.7
--------------------------------------------------------------------------------

* Always check for update when waiting and sort available versions list

Version 1.5.6
--------------------------------------------------------------------------------

* Change failure to get package to debug as previous version may fail

Version 1.5.5
--------------------------------------------------------------------------------

* Show help when no command is provided

Version 1.5.4
--------------------------------------------------------------------------------

* Raise error when failing to read from package index url

Version 1.5.3
--------------------------------------------------------------------------------

* Skip cron check for macOS as it might not start cron until there is a crontab entry

Version 1.5.2
--------------------------------------------------------------------------------

* Update readme

Version 1.5.1
--------------------------------------------------------------------------------

* Remove default update so autopip is the same as app command
* Remove use of platform.dist() as it is deprecated in 3.7

Version 1.5.0
--------------------------------------------------------------------------------

* Only show hint when --version was not used
* Add another hint for checking different Python version
* State supported Python versions
* Add hint about checking different Python version
* Support Python 3.7
* Raise error when failed to get version for setuptools and wheel

Version 1.4.9
================================================================================

* Check other paths for pip.conf and also restore setuptools as flake8 pkg depends on it
* Increase run test parallel to 10
* Show system install root instead of symlink root

Version 1.4.8
--------------------------------------------------------------------------------

* Skip bytecode compile when installing for non-root install

Version 1.4.7
--------------------------------------------------------------------------------

* Keep wheel as some packages (pantsbuild) depend on it and only remove pyc for non-root

Version 1.4.6
--------------------------------------------------------------------------------

* Remove pyc files after install
* Remove pyc files after install is done
* Manually remove setuptools so we can keep pkg-resources

Version 1.4.5
--------------------------------------------------------------------------------

* Keep setuptools as we need pkg_resources from it and there is no whl on macOS

Version 1.4.4
--------------------------------------------------------------------------------

* Remove wheel/setuptools/pip after install as they will not be used anymore
* Add more tests

Version 1.4.3
--------------------------------------------------------------------------------

* Remove PYTHONPATH before installing

Version 1.4.2
--------------------------------------------------------------------------------

* Fix another bug with update in interactive mode

Version 1.4.1
--------------------------------------------------------------------------------

* Fix update not running in cron

Version 1.4.0
--------------------------------------------------------------------------------

* Use ~/bin instead of ~/.apps/bin for user install

Version 1.3.5
================================================================================

* Suggest different command to start cron for macOS
* Use a specific Python version

Version 1.3.4
--------------------------------------------------------------------------------

* Detect python2 version before using

Version 1.3.3
--------------------------------------------------------------------------------

* Unique scripts are unique and fix regex

Version 1.3.2
--------------------------------------------------------------------------------

* Convert update value to correct type

Version 1.3.1
--------------------------------------------------------------------------------

* Only display --python hint for normal exceptions

Version 1.3.0
--------------------------------------------------------------------------------

* Support installing for different versions of Python using --python option
* Remove condition that can never be true
* Hide stacktrace for KeyboardInterrupt
* Yes to add apt repo
* Decode using utf8
* Use tuple for printing autofix cmds
* Add --autofix option to fix Python installation issues automatically

Version 1.2.9
================================================================================

* Use MissingError instead of RuntimeError for missing cron service
* Ensure pip3 has correct path before checking version
* Check Python dev package
* Check setuptools and wheel
* Optionally show sudo
* Add sudo and show output before error

Version 1.2.8
--------------------------------------------------------------------------------

* Raise on error
* Fix typos
* Check for Python 3.6 instead
* Test check script
* Convert to str if bytes

Version 1.2.7
--------------------------------------------------------------------------------

* Ensure wheel is installed
* Move check_venv

Version 1.2.6
--------------------------------------------------------------------------------

* Add sudo for ln
* Provide suggestion for updating symlink
* Add script to help check Python installation

Version 1.2.5
--------------------------------------------------------------------------------

* Pin to python3.6 when creating venv

Version 1.2.4
--------------------------------------------------------------------------------

* Switch to use ps as pgrep does not work in cron for macOS

Version 1.2.3
--------------------------------------------------------------------------------

* Add update to readme and fix duplicate updates

Version 1.2.2
--------------------------------------------------------------------------------

* Remove spec in list command output

Version 1.2.1
--------------------------------------------------------------------------------

* Remove crontab entry when there are no more auto-update apps

Version 1.2.0
--------------------------------------------------------------------------------

* Switch to a single crontab entry and add update command.
  Moved --wait option from install to update command

Version 1.1.5
================================================================================

* Remove cron entry when pinning to a specific version
* Add --wait option for install to wait until new version is published

Version 1.1.4
--------------------------------------------------------------------------------

* Change suggested update frequency to monthly for autopip and pin to major

Version 1.1.3
--------------------------------------------------------------------------------

* Update readme

Version 1.1.2
--------------------------------------------------------------------------------

* Update wording for alternative

Version 1.1.1
--------------------------------------------------------------------------------

* Add FAQ

Version 1.1.0
--------------------------------------------------------------------------------

* Update readme

Version 1.0.9
================================================================================

* Fix local install access check and update README with chown instruction

Version 1.0.8
--------------------------------------------------------------------------------

* Use pip to upgrade pip instead of curl as speed seems to be about the same

Version 1.0.7
--------------------------------------------------------------------------------

* Ignore missing crontab/cron when uninstalling
* Add wheel to setup_requires

Version 1.0.6
--------------------------------------------------------------------------------

* Switch to use # for permission issue

Version 1.0.5
--------------------------------------------------------------------------------

* Update readme

Version 1.0.4
--------------------------------------------------------------------------------

* Remove sudo warning as it should be obvious

Version 1.0.3
--------------------------------------------------------------------------------

* Uninstall autopip last when doing a group

Version 1.0.2
--------------------------------------------------------------------------------

* Update readme

Version 1.0.1
--------------------------------------------------------------------------------

* Update readme

Version 1.0.0
--------------------------------------------------------------------------------

* Set status to prod/stable
* Support update frequency from autopip entry group
* Save/show update frequency
* Add update frequency info
* Terminate autopip if running for longer than an hour
* Add --update option to specify how often to update an app

Version 0.3.4
================================================================================

* Set keywords

Version 0.3.3
--------------------------------------------------------------------------------

* Fix link

Version 0.3.2
--------------------------------------------------------------------------------

* Add info about autopip entry points
* Support autopip entry points to install other apps

Version 0.3.1
--------------------------------------------------------------------------------

* Prevent autopip from being uninstalled when there are other apps

Version 0.3.0
--------------------------------------------------------------------------------

* Deactivate virtualenv after getting distribution

Version 0.2.9
================================================================================

* Skip script info in non-tty

Version 0.2.8
--------------------------------------------------------------------------------

* Soft fail for auto-update via cron

Version 0.2.7
--------------------------------------------------------------------------------

* Fall back to installed-files.txt if RECORD is not found

Version 0.2.6
--------------------------------------------------------------------------------

* Get scripts via entry point or installed file record

Version 0.2.5
--------------------------------------------------------------------------------

* Add optional name filter for list command
* Fix duplicate crontab entries and provide more info when already installed
* Update readme

Version 0.2.4
--------------------------------------------------------------------------------

* Use different system vs local install paths based on permission

Version 0.2.3
--------------------------------------------------------------------------------

* Override links to /opt/apps as our apps used to be there

Version 0.2.2
--------------------------------------------------------------------------------

* Check system base for permissions

Version 0.2.1
--------------------------------------------------------------------------------

* Check log parents for system permission

Version 0.2.0
--------------------------------------------------------------------------------

* Better words for sudo use and alternative to use virtual env

Version 0.1.2
================================================================================

* Switch to use /usr/local for system installs
  
  And also add note about using sudo and security

Version 0.1.1
--------------------------------------------------------------------------------

* Sort pkg versions from PyPI index
* Update readme

Version 0.1.0
--------------------------------------------------------------------------------

* Add note to use sudo to see apps installs in /usr/local/bin
* Prepend /usr/local/bin to PATH in crontab as brew installs python3 there

Version 0.0.9
================================================================================

* Move install comment to below the sudo command

Version 0.0.8
--------------------------------------------------------------------------------

* Redirect stderr for crontab calls
* Update readme

Version 0.0.7
--------------------------------------------------------------------------------

* Add notice to use sudo on first user install

Version 0.0.6
--------------------------------------------------------------------------------

* Add example using app and installing autopip itself

Version 0.0.5
--------------------------------------------------------------------------------

* Bump version
* Always override links for autopip

Version 0.0.4
--------------------------------------------------------------------------------

* Update readme
* Add link to pip conf
* Add note on doing user install

Version 0.0.3
--------------------------------------------------------------------------------

* Update description

Version 0.0.2
--------------------------------------------------------------------------------

* Add README and set status to Beta
* Add more tests
* Add tests
* Switch to use logging to show timestamp
* Support version requirements to pin version
* Add cron job when installing
* Failure of one install should not impact the rest
* Add app alias and implement uninstall
* Implement list packages

Version 0.0.1
--------------------------------------------------------------------------------

* Add package manager and crontab
* Initial commit

Version 0.0.1
--------------------------------------------------------------------------------

* Setup project and add crontab support
* Initial commit

Version 0.0.1
--------------------------------------------------------------------------------

* Setup project
* Initial commit
