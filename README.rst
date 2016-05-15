Automatic upstream dependency testing
-------------------------------------

.. image:: https://img.shields.io/travis/MrSenko/strazar/master.svg
   :target: https://travis-ci.org/MrSenko/strazar
   :alt: Build status

Strazar (from Bulgarian for sentinel) helps you pro-actively monitor for new
versions of upstream packages. Once a package is found it is added to your test
matrix to ensure your software works with the latest upstream dependencies!

Strazar works by updating the ``.travis.yml`` environment and uses the GitHub
API to pull and push changes automatically to your repositories. The actual
environment setup and testing is performed by the CI server, while Strazar
acts as a trigger for new builds!


To install::

    pip install strazar


Supported upstream package repositories
=======================================

Currently only `PyPI <http://pypi.python.org>`_ is supported. We have plans for
adding `RubyGems <http://rubygems.org>`_ and `NPM <https://www.npmjs.com/>`_
very soon! Others will come later.


Supported CI environments
=========================

At the moment only `Travis-CI <https://travis-ci.org>`_ is supported!


Supported source code repositories
==================================

At the moment only `GitHub <https://github.com>`_ is supported as we use their
API, not git directly!

* ``GITHUB_TOKEN`` environment variable allows authenticated API access. This
  token needs the ``public_repo`` or ``repo`` permission.


Monitor PyPI
============

PyPI doesn't provide web-hooks so we examine the RSS feed for packages of
interest based on configuration settings. To start monitoring PyPI execute
the following code from a cron job (at `Mr. Senko <http://MrSenko.com>`_
we do it every hour)::

    import os
    import strazar

    os.environ['GITHUB_TOKEN'] = 'xxxxxxxxx'
    config = {
        "PyYAML" : [
            {
                'cb' : strazar.update_github,
                'args': {
                    'GITHUB_REPO' : 'MrSenko/strazar',
                    'GITHUB_BRANCH' : 'master',
                    'GITHUB_FILE' : '.travis.yml'
                }
            },
        ],
    }
    
    strazar.monitor_pypi_rss(config)

The ``config`` dict uses package names as 1st level keys. If you are interested
in a particular package add it here. All other packages detected from the RSS
feed will be ignored. If your project depends on multiple packages you have to
list all of them as 1st level keys in ``config`` and duplicate the key values.

The key value is a list of call-back methods and arguments to execute once a
new package has been published online. If two or more repositories depend on
the same package then add them as values to this list.

The ``strazar.update_github`` call-back knows how to commit to your source repo
which will automatically trigger a new CI build.

Contributing
============

Source code and issue tracker are at https://github.com/MrSenko/strazar


Commercial support
==================

`Mr. Senko <http://MrSenko.com>`_ provides commercial support for open source
libraries, should you need it!
