import yaml
import strazar
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock
from datetime import datetime

class StrazarGitHubTestCase(unittest.TestCase):
    """
        Tests related to GitHub functionality
    """

    pass
#    def test_update_github(self):
#        kwargs = {
#                    'GITHUB_REPO' : 'atodorov/bztest',
#                    'GITHUB_BRANCH' : 'master',
#                    'GITHUB_FILE' : '.travis.yml'
#        }
#        strazar.update_github(commit_mode=False, **kwargs)

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
        old_travis = """
language: python
env:
  - _PYYAML=3.11
"""
        env = strazar.build_travis_env(yaml.load(old_travis), 'PyYAML', '3.11')
        self.assertEquals(len(env.keys()), 1)
        self.assertTrue('_PYYAML' in env)
        self.assertEquals(env['_PYYAML'], set(['3.11']))

    def test_build_travis_env_new_version_added(self):
        """
            WHEN new package version is not present in environment
            THEN it is included
        """
        old_travis = """
language: python
env:
  - _PYYAML=3.11
"""
        env = strazar.build_travis_env(yaml.load(old_travis), 'PyYAML', '4.11')
        self.assertEquals(len(env.keys()), 1)
        self.assertTrue('_PYYAML' in env)
        self.assertEquals(env['_PYYAML'], set(['3.11', '4.11']))

    def test_build_travis_env_2_older_versions_and_new_version(self):
        """
            WHEN there are 2 older versions in environment
            THEN the new one is included as well
        """
        old_travis = """
language: python
env:
  - _PYYAML=3.11
  - _PYYAML=3.12
"""
        env = strazar.build_travis_env(yaml.load(old_travis), 'PyYAML', '4.11')
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
        old_travis = """
env:
- _PYYAML=3.11
language: python
"""
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.11')
        self.assertEquals(new_travis.strip(), old_travis.strip())


    def test_update_travis_1_pkg_new_version(self):
        """
            WHEN there is a new version for a single package
            THEN .travis.yml should change accordingly
        """

        old_travis = """
env:
- _PYYAML=3.11
language: python
"""
        expected_travis = """
env:
- _PYYAML=3.11
- _PYYAML=3.12
language: python
"""
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.12')
        self.assertEquals(new_travis.strip(), expected_travis.strip())

    def test_update_travis_2_pkgs_new_version(self):
        """
            WHEN there is a new version
            AND there are two packages listed
            THEN .travis.yml should change accordingly
        """

        old_travis = """
env:
- _JINJA_AB=0.3.0 _PYYAML=3.11
language: python
"""
        expected_travis = """
env:
- _JINJA_AB=0.3.0 _PYYAML=3.11
- _JINJA_AB=0.3.0 _PYYAML=3.12
language: python
"""
        new_travis = strazar.update_travis(old_travis, 'PyYAML', '3.12')
        self.assertEquals(new_travis.strip(), expected_travis.strip())
