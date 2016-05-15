# -*- coding: utf-8 -*-

import os
import yaml
import strazar
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
from datetime import datetime

_url_mock_values = {
    False: {
        '/repos/MrSenko/strazar/git/refs/heads/master': {
            "ref": "refs/heads/master",
            "object": {
                "sha": "2c00076236089e8713afb69799205e043d0068d8",
                "type": "commit",
                "url": "/repos/MrSenko/strazar/git/commits/2c00076236089e8713afb69799205e043d0068d8"
            }
        },
        '/repos/MrSenko/strazar/git/commits/2c00076236089e8713afb69799205e043d0068d8': {
            "sha": "2c00076236089e8713afb69799205e043d0068d8",
            "tree": {
                "sha": "175b571e84ae67a54a3fb46ae0be9ccc39c8efb6",
                "url": "/repos/MrSenko/strazar/git/trees/175b571e84ae67a54a3fb46ae0be9ccc39c8efb6"
            },
            "message": "Added .travis.yml",
        },
        '/repos/MrSenko/strazar/git/trees/175b571e84ae67a54a3fb46ae0be9ccc39c8efb6': {
            "sha": "175b571e84ae67a54a3fb46ae0be9ccc39c8efb6",
            "tree": [
                {
                    "path": ".gitignore",
                    "url": "/repos/MrSenko/strazar/git/blobs/004a8d7a778d7fda2a8f409d72ba517cb8325fa3"
                },
                {
                    "path": ".travis.yml",
                    "url": "/repos/MrSenko/strazar/git/blobs/c7a421dc1d3d7124e21a49dfcfac9be3e926cd89"
                }
              ],
        },
        '/repos/MrSenko/strazar/git/blobs/c7a421dc1d3d7124e21a49dfcfac9be3e926cd89': {
            "content": "bGFuZ3VhZ2U6IHB5dGhvbgpweXRob246CiAgLSAyLjcKICAtIDMuNQppbnN0YWxsOgogIC0gcGlwIGluc3RhbGwgY292ZXJhZ2UgZmxha2U4IG1vY2sgUHlZQU1MPT0kX1BZWUFNTCBQeUdpdGh1Yj09JF9QWUdJVEhVQgpzY3JpcHQ6CiAgLSAuL3Rlc3Quc2gKZW52OgogIC0gX1BZR0lUSFVCPTEuMjYuMCBfUFlZQU1MPTMuMTEK",
            "encoding": "base64"
        },
    },
    True: {
        '/repos/MrSenko/strazar/git/blobs': {
            "sha": 'new-blob'
        },
        '/repos/MrSenko/strazar/git/trees': {
            "sha": 'new-tree'
        },
        '/repos/MrSenko/strazar/git/commits': {
            "sha": 'new-commit'
        },
        '/repos/MrSenko/strazar/git/refs/heads/master': {
            "ref": "refs/heads/master",
            "url": "https://api.github.com/repos/MrSenko/strazar/git/refs/heads/master",
            "object": {
                "type": "commit",
                "sha": "new-commit",
                "url": "https://api.github.com/repos/MrSenko/strazar/git/commits/new-commit"
            }
        },
    }
}

def _get_url_mock(url, push_data=None):
    request = _url_mock_values[push_data is not None]

    if url in request:
        return request[url]
    else:
        raise RuntimeError("I don't know how to mock '%s' yet!" % url)



class StrazarGitHubTestCase(unittest.TestCase):
    """
        Tests related to GitHub functionality
    """

    def test_no_github_token_raises_exception(self):
        """
            WHEN no GITHUB_TOKEN is configured in os.environ
            THEN update_github() raises an exception
        """
        with self.assertRaises(RuntimeError):
            strazar.update_github()

    def test_update_github(self):
        """
            WHEN there's a new package version
            THEN .travis.yml is updated
            AND change is pushed to GitHub
        """
        kwargs = {
                'GITHUB_REPO' : 'MrSenko/strazar',
                'GITHUB_BRANCH' : 'master',
                'GITHUB_FILE' : '.travis.yml',
                'name': 'PyYAML',
                'version': '3.12',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(side_effect=_get_url_mock)
        os.environ['GITHUB_TOKEN'] = 'testing'
        try:
            ret = strazar.update_github(**kwargs)
            self.assertTrue(ret)
        finally:
            strazar.get_url = _orig_get_url
            del os.environ['GITHUB_TOKEN']

    def test_update_github_github_returning_error_on_push(self):
        """
            WHEN GitHub returns an error on push
            THEN it is handled correctly
        """
        def _return_values(*args, **kwargs):
            url = list(args)[0]
            try:
                post_data = list(args)[1]
            except IndexError:
                post_data = None
            if post_data and url == '/repos/MrSenko/strazar/git/refs/heads/master':
                return {
                        "message": "Push to GitHub failed",
                    }
            else:
                return _get_url_mock(*args)

        kwargs = {
                'GITHUB_REPO' : 'MrSenko/strazar',
                'GITHUB_BRANCH' : 'master',
                'GITHUB_FILE' : '.travis.yml',
                'name': 'PyYAML',
                'version': '3.12',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(side_effect=_return_values)
        os.environ['GITHUB_TOKEN'] = 'testing'
        try:
            ret = strazar.update_github(**kwargs)
            self.assertNotEquals(ret, True)
            self.assertEquals(ret, "Push to GitHub failed")
        finally:
            strazar.get_url = _orig_get_url
            del os.environ['GITHUB_TOKEN']


    def test_update_github_travis_not_updated(self):
        """
            WHEN .travis.yml is not updated
            THEN the functions exits and returns True
            AND no git write operations were performed
        """
        kwargs = {
                'GITHUB_REPO' : 'MrSenko/strazar',
                'GITHUB_BRANCH' : 'master',
                'GITHUB_FILE' : '.travis.yml',
                'name': 'PyYAML',
                'version': '3.11',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
        }

        _orig_get_url = strazar.get_url
        _orig_post_url = strazar.post_url
        strazar.get_url = mock.MagicMock(side_effect=_get_url_mock)
        strazar.post_url = mock.MagicMock(side_effect=Exception('Boom!'))
        os.environ['GITHUB_TOKEN'] = 'testing'
        try:
            ret = strazar.update_github(**kwargs)
            self.assertTrue(ret)
            # no write operations performed
            strazar.post_url.assert_not_called()
        finally:
            strazar.get_url = _orig_get_url
            strazar.post_url = _orig_post_url
            del os.environ['GITHUB_TOKEN']


    def test_update_github_no_travis_yml_in_repository(self):
        """
            GIVEN there is no .travis.yml file in the repository
            WHEN we call update_github()
            THEN exception is Raised
        """
        def _return_values(*args, **kwargs):
            url = list(args)[0]

            if url == '/repos/MrSenko/strazar/git/trees/175b571e84ae67a54a3fb46ae0be9ccc39c8efb6':
                return {
                        "sha": "175b571e84ae67a54a3fb46ae0be9ccc39c8efb6",
                        "tree": [],
                    }
            else:
                return _get_url_mock(*args)

        kwargs = {
                'GITHUB_REPO' : 'MrSenko/strazar',
                'GITHUB_BRANCH' : 'master',
                'GITHUB_FILE' : '.travis.yml',
                'name': 'PyYAML',
                'version': '3.11',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
        }

        _orig_get_url = strazar.get_url
        _orig_post_url = strazar.post_url
        strazar.get_url = mock.MagicMock(side_effect=_return_values)
        strazar.post_url = mock.MagicMock(side_effect=Exception('Boom!'))
        os.environ['GITHUB_TOKEN'] = 'testing'
        try:
            with self.assertRaises(RuntimeError):
                strazar.update_github(**kwargs)
            # no write operations performed
            strazar.post_url.assert_not_called()
        finally:
            strazar.get_url = _orig_get_url
            strazar.post_url = _orig_post_url
            del os.environ['GITHUB_TOKEN']

class StrazarPypiMonitorTestCase(unittest.TestCase):
    """
        Tests for monitor_pypi_rss()
    """

    def test_pkg_from_config_not_in_rss(self):
        """
            WHEN the package(s) we're looking for are not in the RSS feed
            THEN the callback method is not executed
        """
        _test_callback = mock.MagicMock()
        config = {
            "PyYAML" : [
                {
                    'cb' : _test_callback,
                    'args': {},
                }
            ],
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(return_value="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/formats/rss-0.91.dtd">
<rss version="0.91">
 <channel>
  <item>
    <title>bkheatmap 0.1.1</title>
    <link>http://pypi.python.org/pypi/bkheatmap/0.1.1</link>
    <description>A Bokeh heatmap for Python</description>
    <pubDate>12 May 2016 21:45:48 GMT</pubDate>
   </item>
  <item>
    <title>fleece 0.4.0</title>
    <link>http://pypi.python.org/pypi/fleece/0.4.0</link>
    <description>Wrap the lamb...da</description>
    <pubDate>12 May 2016 21:45:18 GMT</pubDate>
   </item>
  </channel>
</rss>
""".strip())
        try:
            strazar.monitor_pypi_rss(config)
        finally:
            strazar.get_url = _orig_get_url
        _test_callback.assert_not_called()

    def test_pkg_from_config_in_rss(self):
        """
            WHEN the package(s) we're looking for are in the RSS feed
            THEN the callback method is executed for every repo that is listed
                under this package name
        """
        _test_callback = mock.MagicMock()
        config = {
            "PyYAML" : [
                {
                    'cb' : _test_callback,
                    'args': {
                        'GITHUB_REPO' : 'MrSenko/strazar',
                        'GITHUB_BRANCH' : 'master',
                        'GITHUB_FILE' : '.travis.yml'
                    }
                },
                {
                    'cb' : _test_callback,
                    'args': {
                        'GITHUB_REPO' : 'MrSenko/strazar2',
                        'GITHUB_BRANCH' : 'master',
                        'GITHUB_FILE' : '.travis.yml'
                    }
                },
            ],
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(return_value="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/formats/rss-0.91.dtd">
<rss version="0.91">
 <channel>
  <item>
    <title>PyYAML 3.12</title>
    <link>http://pypi.python.org/pypi/PyYAML/3.12</link>
    <pubDate>12 May 2016 21:45:18 GMT</pubDate>
   </item>
  </channel>
</rss>
""".strip())
        try:
            strazar.monitor_pypi_rss(config)
        finally:
            strazar.get_url = _orig_get_url

        # build the expected call list
        call_list = []
        for repo in config['PyYAML']:
            args = repo['args']
            args.update({
                'name': 'PyYAML',
                'version': '3.12',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
            })
            call_list.append(mock.call(**args))

        # assert we've been called twice
        _test_callback.assert_has_calls(call_list)

    def test_pkg_in_rss_and_callback_raises_exception(self):
        """
            WHEN the package(s) we're looking for are in the RSS feed
            AND the callback method raises an exception
            THEN the exception is caught and doesn't propagate outside
        """
        _test_callback = mock.MagicMock(side_effect=Exception('Boom!'))
        config = {
            "PyYAML" : [
                {
                    'cb' : _test_callback,
                    'args': {
                        'GITHUB_REPO' : 'MrSenko/strazar',
                        'GITHUB_BRANCH' : 'master',
                        'GITHUB_FILE' : '.travis.yml'
                    }
                },
                {
                    'cb' : _test_callback,
                    'args': {
                        'GITHUB_REPO' : 'MrSenko/strazar2',
                        'GITHUB_BRANCH' : 'master',
                        'GITHUB_FILE' : '.travis.yml'
                    }
                },
            ],
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(return_value="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/formats/rss-0.91.dtd">
<rss version="0.91">
 <channel>
  <item>
    <title>PyYAML 3.12</title>
    <link>http://pypi.python.org/pypi/PyYAML/3.12</link>
    <pubDate>12 May 2016 21:45:18 GMT</pubDate>
   </item>
  </channel>
</rss>
""".strip())
        try:
            try:
                strazar.monitor_pypi_rss(config)
            except:
                self.fail('monitor_pypi_rss() did not catch internal exception!')
        finally:
            strazar.get_url = _orig_get_url

        # build the expected call list
        call_list = []
        for repo in config['PyYAML']:
            args = repo['args']
            args.update({
                'name': 'PyYAML',
                'version': '3.12',
                'released_on': datetime.strptime('12 May 2016 21:45:18 GMT', '%d %b %Y %H:%M:%S GMT'),
            })
            call_list.append(mock.call(**args))

        # assert we've been called twice
        _test_callback.assert_has_calls(call_list)


    def test_rss_fields_fail_to_parse(self):
        """
            WHEN the RSS feed is valid
            BUT the data inside fails to parse (e.g. wrong data format)
            THEN the exception is caught and doesn't propagate outside
            AND the callback method is not executed
        """
        _test_callback = mock.MagicMock()
        config = {
            "PyYAML" : [
                {
                    'cb' : _test_callback,
                    'args': {},
                },
            ],
        }

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(return_value="""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/formats/rss-0.91.dtd">
<rss version="0.91">
 <channel>
  <item>
    <title>PyYAML 3.12</title>
    <link>http://pypi.python.org/pypi/PyYAML/3.12</link>
    <pubDate>12 May 2016 99:45:18 GMT</pubDate>
   </item>
  </channel>
</rss>
""".strip())
        try:
            try:
                strazar.monitor_pypi_rss(config)
            except:
                self.fail('monitor_pypi_rss() did not catch internal exception!')
        finally:
            strazar.get_url = _orig_get_url

        # assert callback has not been executed
        _test_callback.assert_not_called()


    def test_parse_rss_with_non_latin_chars(self):
        """
            WHEN RSS feed contains non-latin chars in pacakge description
            THEN we should still be able to parse it
            AND not raise an exception
        """
        _test_callback = mock.MagicMock()
        config = {}

        _orig_get_url = strazar.get_url
        strazar.get_url = mock.MagicMock(return_value=u"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss PUBLIC "-//Netscape Communications//DTD RSS 0.91//EN" "http://my.netscape.com/publish/formats/rss-0.91.dtd">
<rss version="0.91">
 <channel>
  <title>PyPI Recent Updates</title>
  <link>https://pypi.python.org/pypi</link>
  <description>Recent updates to the Python Package Index</description>
  <language>en</language>

  <item>
    <title>gitvtag 0.1</title>
    <link>http://pypi.python.org/pypi/gitvtag/0.1</link>
    <description>A git subcommand for simple and straightforward version tagging</description>
    <pubDate>15 May 2016 04:51:28 GMT</pubDate>
   </item>
  <item>
    <title>python-socketio 1.3</title>
    <link>http://pypi.python.org/pypi/python-socketio/1.3</link>
    <description>Socket.IO server</description>
    <pubDate>15 May 2016 04:42:24 GMT</pubDate>
   </item>
  <item>
    <title>strazar 0.2.1</title>
    <link>http://pypi.python.org/pypi/strazar/0.2.1</link>
    <description>Automatic upstream dependency testing</description>
    <pubDate>15 May 2016 04:39:02 GMT</pubDate>
   </item>
  <item>
    <title>pyKevo 1.0.0</title>
    <link>http://pypi.python.org/pypi/pyKevo/1.0.0</link>
    <description>A simple Python project for people with Kevo smartlocks.</description>
    <pubDate>15 May 2016 04:24:46 GMT</pubDate>
   </item>
  <item>
    <title>ak-androguard 3.2.1</title>
    <link>http://pypi.python.org/pypi/ak-androguard/3.2.1</link>
    <description>A fork of official Androguard project</description>
    <pubDate>15 May 2016 04:22:56 GMT</pubDate>
   </item>
  <item>
    <title>ovation 1.0.1</title>
    <link>http://pypi.python.org/pypi/ovation/1.0.1</link>
    <description>Ovation Python API</description>
    <pubDate>15 May 2016 04:19:30 GMT</pubDate>
   </item>
  <item>
    <title>trimesh 1.14.1</title>
    <link>http://pypi.python.org/pypi/trimesh/1.14.1</link>
    <description>Import, export, process, analyze and view triangular meshes.</description>
    <pubDate>15 May 2016 04:03:26 GMT</pubDate>
   </item>
  <item>
    <title>metonic 0.01</title>
    <link>http://pypi.python.org/pypi/metonic/0.01</link>
    <description></description>
    <pubDate>15 May 2016 04:02:50 GMT</pubDate>
   </item>
  <item>
    <title>sappho 0.9.0</title>
    <link>http://pypi.python.org/pypi/sappho/0.9.0</link>
    <description>2D game engine (pygame)</description>
    <pubDate>15 May 2016 03:34:06 GMT</pubDate>
   </item>
  <item>
    <title>nester_bigbooa 1.0.0</title>
    <link>http://pypi.python.org/pypi/nester_bigbooa/1.0.0</link>
    <description>UNKNOWN</description>
    <pubDate>15 May 2016 03:07:54 GMT</pubDate>
   </item>
  <item>
    <title>TerminalPrinter 1.1.6</title>
    <link>http://pypi.python.org/pypi/TerminalPrinter/1.1.6</link>
    <description>文字,字符,图片终端打印, print something in terminal</description>
    <pubDate>15 May 2016 02:59:12 GMT</pubDate>
   </item>
  <item>
    <title>ufs_tools 0.5.0</title>
    <link>http://pypi.python.org/pypi/ufs_tools/0.5.0</link>
    <description>Some functions can be used during python development</description>
    <pubDate>15 May 2016 02:57:15 GMT</pubDate>
   </item>
  <item>
    <title>PyRIC 0.0.7</title>
    <link>http://pypi.python.org/pypi/PyRIC/0.0.7</link>
    <description>Pythonic iw</description>
    <pubDate>15 May 2016 02:52:10 GMT</pubDate>
   </item>
  <item>
    <title>async_notifications 0.0.2</title>
    <link>http://pypi.python.org/pypi/async_notifications/0.0.2</link>
    <description>Email async notifications with celery.</description>
    <pubDate>15 May 2016 02:45:27 GMT</pubDate>
   </item>
  <item>
    <title>scspell3k 1.2</title>
    <link>http://pypi.python.org/pypi/scspell3k/1.2</link>
    <description>A conservative interactive spell checker for source code.</description>
    <pubDate>15 May 2016 02:40:37 GMT</pubDate>
   </item>
  <item>
    <title>django-system-globals 0.0.5</title>
    <link>http://pypi.python.org/pypi/django-system-globals/0.0.5</link>
    <description>A Django App to manage any system globals from a DB table.</description>
    <pubDate>15 May 2016 02:33:46 GMT</pubDate>
   </item>
  <item>
    <title>colorclass 2.2.0</title>
    <link>http://pypi.python.org/pypi/colorclass/2.2.0</link>
    <description>Colorful worry-free console applications for Linux, Mac OS X, and Windows.</description>
    <pubDate>15 May 2016 02:23:21 GMT</pubDate>
   </item>
  <item>
    <title>guano 0.0.3</title>
    <link>http://pypi.python.org/pypi/guano/0.0.3</link>
    <description>GUANO, the "Grand Unified" bat acoustics metadata format</description>
    <pubDate>15 May 2016 02:11:49 GMT</pubDate>
   </item>
  <item>
    <title>pyservice_django 1.1.19</title>
    <link>http://pypi.python.org/pypi/pyservice_django/1.1.19</link>
    <description>UNKNOWN</description>
    <pubDate>15 May 2016 02:06:19 GMT</pubDate>
   </item>
  <item>
    <title>documenteer 0.1.2</title>
    <link>http://pypi.python.org/pypi/documenteer/0.1.2</link>
    <description>Tools for LSST DM documentation projects</description>
    <pubDate>15 May 2016 01:49:02 GMT</pubDate>
   </item>
  <item>
    <title>temporary 1.1.0</title>
    <link>http://pypi.python.org/pypi/temporary/1.1.0</link>
    <description>Context managers for managing temporary files and directories.</description>
    <pubDate>15 May 2016 01:47:42 GMT</pubDate>
   </item>
  <item>
    <title>PyPrind 2.9.8</title>
    <link>http://pypi.python.org/pypi/PyPrind/2.9.8</link>
    <description>Python Progress Bar and Percent Indicator Utility</description>
    <pubDate>15 May 2016 01:31:09 GMT</pubDate>
   </item>
  <item>
    <title>discon 0.0.12</title>
    <link>http://pypi.python.org/pypi/discon/0.0.12</link>
    <description>distribution to pypi and conda</description>
    <pubDate>15 May 2016 01:22:09 GMT</pubDate>
   </item>
  <item>
    <title>update-conf.py 0.4.5</title>
    <link>http://pypi.python.org/pypi/update-conf.py/0.4.5</link>
    <description>Generate config files from 'conf.d' like directories</description>
    <pubDate>15 May 2016 01:12:07 GMT</pubDate>
   </item>
  <item>
    <title>django-db-file-storage 0.4.1</title>
    <link>http://pypi.python.org/pypi/django-db-file-storage/0.4.1</link>
    <description>Custom FILE_STORAGE for Django. Saves files in your database instead of your file system.</description>
    <pubDate>15 May 2016 01:06:54 GMT</pubDate>
   </item>
  <item>
    <title>callee 0.2.1</title>
    <link>http://pypi.python.org/pypi/callee/0.2.1</link>
    <description>Argument matchers for unittest.mock</description>
    <pubDate>15 May 2016 01:04:57 GMT</pubDate>
   </item>
  <item>
    <title>practic_e 1.3.1</title>
    <link>http://pypi.python.org/pypi/practic_e/1.3.1</link>
    <description>UNKNOWN</description>
    <pubDate>15 May 2016 00:58:22 GMT</pubDate>
   </item>
  <item>
    <title>nester_qk 1.4.0</title>
    <link>http://pypi.python.org/pypi/nester_qk/1.4.0</link>
    <description>A simple printer of nested lists</description>
    <pubDate>15 May 2016 00:55:51 GMT</pubDate>
   </item>
  <item>
    <title>cdmetro 1.0.10</title>
    <link>http://pypi.python.org/pypi/cdmetro/1.0.10</link>
    <description>Un admin de django diferente</description>
    <pubDate>15 May 2016 00:52:53 GMT</pubDate>
   </item>
  <item>
    <title>graphmachine 3.0.0.42</title>
    <link>http://pypi.python.org/pypi/graphmachine/3.0.0.42</link>
    <description>Graph Machine application</description>
    <pubDate>15 May 2016 00:30:14 GMT</pubDate>
   </item>
  <item>
    <title>mongoelector 0.1.1</title>
    <link>http://pypi.python.org/pypi/mongoelector/0.1.1</link>
    <description>Distributed master election and locking in mongodb</description>
    <pubDate>15 May 2016 00:04:32 GMT</pubDate>
   </item>
  <item>
    <title>psychic_disco 0.7.0</title>
    <link>http://pypi.python.org/pypi/psychic_disco/0.7.0</link>
    <description>Pythonic Microservices on AWS Lambda</description>
    <pubDate>15 May 2016 00:03:27 GMT</pubDate>
   </item>
  <item>
    <title>blockstack-proofs 0.0.5</title>
    <link>http://pypi.python.org/pypi/blockstack-proofs/0.0.5</link>
    <description>Python library for verifying proofs (twitter, github, domains etc) linked to a blockchain ID</description>
    <pubDate>15 May 2016 00:01:21 GMT</pubDate>
   </item>
  <item>
    <title>supra 1.0.16</title>
    <link>http://pypi.python.org/pypi/supra/1.0.16</link>
    <description>It's an easy JSON services generator</description>
    <pubDate>14 May 2016 23:59:35 GMT</pubDate>
   </item>
  <item>
    <title>otree-core 0.5.0.dev18</title>
    <link>http://pypi.python.org/pypi/otree-core/0.5.0.dev18</link>
    <description>oTree is a toolset that makes it easy to create and administer web-based social science experiments.</description>
    <pubDate>14 May 2016 23:58:44 GMT</pubDate>
   </item>
  <item>
    <title>wdom 0.1.1</title>
    <link>http://pypi.python.org/pypi/wdom/0.1.1</link>
    <description>GUI library for browser-based desktop applications</description>
    <pubDate>14 May 2016 23:58:38 GMT</pubDate>
   </item>
  <item>
    <title>ajenti-panel 2.1.14</title>
    <link>http://pypi.python.org/pypi/ajenti-panel/2.1.14</link>
    <description>Ajenti core based panel</description>
    <pubDate>14 May 2016 23:56:45 GMT</pubDate>
   </item>
  <item>
    <title>aj 2.1.14</title>
    <link>http://pypi.python.org/pypi/aj/2.1.14</link>
    <description>Web UI base toolkit</description>
    <pubDate>14 May 2016 23:56:35 GMT</pubDate>
   </item>
  <item>
    <title>plonetheme.barceloneta 1.6.19</title>
    <link>http://pypi.python.org/pypi/plonetheme.barceloneta/1.6.19</link>
    <description>The default theme for Plone 5.</description>
    <pubDate>14 May 2016 23:50:25 GMT</pubDate>
   </item>
  <item>
    <title>mdsplus-alpha 7.0.280</title>
    <link>http://pypi.python.org/pypi/mdsplus-alpha/7.0.280</link>
    <description>MDSplus Python Objects</description>
    <pubDate>14 May 2016 23:49:47 GMT</pubDate>
   </item>
  </channel>
</rss>
""".strip())
        try:
            strazar.monitor_pypi_rss(config)
        finally:
            strazar.get_url = _orig_get_url
        _test_callback.assert_not_called()


class StrazarTravisTestCase(unittest.TestCase):
    """
        Tests related to Travis-CI functionality.
    """
    def test_build_travis_env_new_version_already_present(self):
        """
            WHEN new package version is already present in environment
            THEN it is not included twice
        """
        old_travis = yaml.load("""
language: python
env:
  - _PYYAML=3.11
""")
        env = strazar.build_travis_env(old_travis, 'PyYAML', '3.11')
        self.assertEquals(len(env.keys()), 1)
        self.assertTrue('_PYYAML' in env)
        self.assertEquals(env['_PYYAML'], set(['3.11']))

    def test_build_travis_env_new_version_added(self):
        """
            WHEN new package version is not present in environment
            THEN it is included
        """
        old_travis = yaml.load("""
language: python
env:
  - _PYYAML=3.11
""")
        env = strazar.build_travis_env(old_travis, 'PyYAML', '4.11')
        self.assertEquals(len(env.keys()), 1)
        self.assertTrue('_PYYAML' in env)
        self.assertEquals(env['_PYYAML'], set(['3.11', '4.11']))

    def test_build_travis_env_2_older_versions_and_new_version(self):
        """
            WHEN there are 2 older versions in environment
            THEN the new one is included as well
        """
        old_travis = yaml.load("""
language: python
env:
  - _PYYAML=3.11
  - _PYYAML=3.12
""")
        env = strazar.build_travis_env(old_travis, 'PyYAML', '4.11')
        self.assertEquals(len(env.keys()), 1)
        self.assertTrue('_PYYAML' in env)
        self.assertEquals(env['_PYYAML'], set(['3.11', '3.12', '4.11']))

    def test_calculate_new_travis_env_2_pkgs_2_vers_each(self):
        """
            WHEN we have A=1, A=2 and B=3, B=4
            THEN the combinations are:
                A=1 B=3
                A=1 B=4
                A=2 B=3
                A=2 B=4
        """
        env_vars = {
            'A': set([1, 2]),
            'B': set([3, 4]),
        }
        new_env = strazar.calculate_new_travis_env(env_vars)
        self.assertEquals(len(new_env), 4)
        self.assertTrue('A=1 B=3' in new_env)
        self.assertTrue('A=1 B=4' in new_env)
        self.assertTrue('A=2 B=3' in new_env)
        self.assertTrue('A=2 B=4' in new_env)


    def test_calculate_new_travis_env_3_pkgs_2_vers_each(self):
        """
            WHEN we have A=1, A=2 and B=3, B=4 and C=5, C=6
            THEN the combinations are:
                A=1 B=3 C=5
                A=1 B=3 C=6
                A=1 B=4 C=5
                A=1 B=4 C=6
                A=2 B=3 C=5
                A=2 B=3 C=6
                A=2 B=4 C=5
                A=2 B=4 C=6
        """
        env_vars = {
            'A': set([1, 2]),
            'B': set([3, 4]),
            'C': set([5, 6]),
        }
        new_env = strazar.calculate_new_travis_env(env_vars)
        self.assertEquals(len(new_env), 8)
        self.assertTrue('A=1 B=3 C=5' in new_env)
        self.assertTrue('A=1 B=3 C=6' in new_env)
        self.assertTrue('A=1 B=4 C=5' in new_env)
        self.assertTrue('A=1 B=4 C=6' in new_env)
        self.assertTrue('A=2 B=3 C=5' in new_env)
        self.assertTrue('A=2 B=3 C=6' in new_env)
        self.assertTrue('A=2 B=4 C=5' in new_env)
        self.assertTrue('A=2 B=4 C=6' in new_env)


    def test_update_travis_no_new_version(self):
        """
            WHEN there is no new version
            THEN .travis.yml should not change
        """
        old_travis = yaml.load("""
env:
- _PYYAML=3.11
language: python
""")
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.11')
        self.assertEquals(new_travis, old_travis)


    def test_update_travis_no_new_version_but_different_sort(self):
        """
            WHEN there is no new version
            BUT the input file is not sorted
            THEN .travis.yml should change
        """
        old_travis = yaml.load("""
env:
  - _PYYAML=3.11 _PYGITHUB=1.26.0
""")
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.11')
        self.assertNotEquals(new_travis, old_travis)
        # note: the order has been changed due to sorting
        self.assertEquals(new_travis['env'], ['_PYGITHUB=1.26.0 _PYYAML=3.11'])


    def test_update_travis_1_pkg_new_version(self):
        """
            WHEN there is a new version for a single package
            THEN .travis.yml should change accordingly
        """

        old_travis = yaml.load("""
env:
- _PYYAML=3.11
language: python
""")
        expected_travis = yaml.load("""
env:
- _PYYAML=3.11
- _PYYAML=3.12
language: python
""")
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.12')
        self.assertEquals(new_travis, expected_travis)

    def test_update_travis_2_pkgs_new_version(self):
        """
            WHEN there is a new version
            AND there are two packages listed
            THEN .travis.yml should change accordingly
        """

        old_travis = yaml.load("""
env:
- _JINJA_AB=0.3.0 _PYYAML=3.11
language: python
""")
        expected_travis = yaml.load("""
env:
- _JINJA_AB=0.3.0 _PYYAML=3.11
- _JINJA_AB=0.3.0 _PYYAML=3.12
language: python
""")
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.12')
        self.assertEquals(new_travis, expected_travis)
