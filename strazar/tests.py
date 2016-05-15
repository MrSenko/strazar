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
