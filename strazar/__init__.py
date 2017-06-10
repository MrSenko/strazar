# pylint: disable=missing-docstring,invalid-name
from __future__ import print_function

import os
import json
import base64
try:
    import httplib
except ImportError:
    import http.client as httplib
from datetime import datetime
from itertools import product
from xml.dom.minidom import parseString

import yaml


# todo: this goes away once we port to
# the Github module and don't use the API directly
def get_url(url, post_data=None):
    # GitHub requires a valid UA string
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0.5) \
Gecko/20120601 Firefox/10.0.5',
    }

    # shortcut for GitHub API calls
    if url.find("://") == -1:
        url = "https://api.github.com%s" % url

    if url.find('api.github.com') > -1:
        if "GITHUB_TOKEN" not in os.environ:
            raise Exception("Set the GITHUB_TOKEN variable")
        else:
            headers.update({
                'Authorization': 'token %s' % os.environ['GITHUB_TOKEN']
            })

    (_, host_path) = url.split('//')
    (host_port, path) = host_path.split('/', 1)
    path = '/' + path

    if url.startswith('https'):
        conn = httplib.HTTPSConnection(host_port)
    else:
        conn = httplib.HTTPConnection(host_port)

    method = 'GET'
    if post_data:
        method = 'POST'
        post_data = json.dumps(post_data)

    conn.request(method, path, body=post_data, headers=headers)
    response = conn.getresponse()

    if response.status == 404:
        raise Exception("404 - %s not found" % url)

    result = response.read().decode('UTF-8', 'replace')
    try:
        return json.loads(result)
    except ValueError:
        # not a JSON response
        return result


def post_url(url, data):
    return get_url(url, data)


def monitor_pypi_rss(config):
    """
        Scan the PyPI RSS feeds to look for new packages.
        If name is found in config then execute the specified callback.

        @config is a dict with keys matching package names and values
        are lists of dicts
            {
                'cb' : a_callback,
                'args' : dict
            }
    """
    print("fetching RSS info from PyPI")
    rss = get_url("https://pypi.python.org/pypi?:action=rss")
    rss = rss.encode('ascii', 'ignore')

    dom = parseString(rss)
    for item in dom.getElementsByTagName("item"):
        try:
            title = item.getElementsByTagName("title")[0]
            pub_date = item.getElementsByTagName("pubDate")[0]

            (name, version) = title.firstChild.wholeText.split(" ")
            released_on = datetime.strptime(pub_date.firstChild.wholeText,
                                            '%d %b %Y %H:%M:%S GMT')

            if name in config.keys():
                print("package %s was found in config ..." % name)

                for cfg in config[name]:
                    try:
                        args = cfg['args']
                        args.update({
                            'name': name,
                            'version': version,
                            'released_on': released_on,
                        })

                        # execute the call back
                        cfg['cb'](**args)
                    except Exception as e:  # pylint: disable=broad-except
                        print(e)
                        continue
            else:
                print("package %s not found in config. continuing ..." % name)
        except Exception as e:  # pylint: disable=broad-except
            print(e.message)
            continue


def build_travis_env(travis, package, new_version):
    """
        Given a YAML object returns an environment
        dict containing all packages and versions including the
        new one.

        NOTE: the result is groupped by package names which appear
        on the same line!
    """
    groups = {}
    pkg_versions = {}

    for line in travis['env']:
        packages_on_this_line = ()
        for variable in line.split(' '):
            p_name, p_version = variable.split('=')
            packages_on_this_line += (p_name,)
            if p_name in pkg_versions:
                pkg_versions[p_name].add(p_version)
            else:
                pkg_versions[p_name] = set([p_version])
        groups[packages_on_this_line] = {}

    # add the new version to the list
    new_pkg_name = '_' + package.upper().replace('-', '_')
    if new_pkg_name in pkg_versions:
        pkg_versions[new_pkg_name].add(new_version)

    # for each group of packages, assign the versions which
    # apply to it
    for pkgs in groups:
        for p_name in pkgs:
            groups[pkgs][p_name] = pkg_versions[p_name]

    return groups


def calculate_new_travis_env(groups):
    """
        Rebuilds the environment matrix as Cartesian product of all
        environment variables (aka packages) and their values (aka versions)

        NOTE: only takes into account variables which are listed on that
        particular line!
    """
    # each element of new_env is single combination of all packages and
    # versions. this represents one line in the travis environment
    new_env = []

    for pkgs in groups:
        # each element of intermediate is the product (aka combinations) of
        # all versions for a particular package
        _keys = groups[pkgs].keys()
        _keys = sorted(_keys)
        intermediate = [product([key], groups[pkgs][key]) for key in _keys]

        # add the new env lines to the list
        for p in list(product(*intermediate)):
            new_env.append(' '.join(["%s=%s" % (k, v) for k, v in list(p)]))
        new_env.sort()

    return new_env


def update_travis(travis, package, new_version):
    """
        Parses .travis.yml, builds a list of package==version
        from the environment and updates the environment if
        the new version is not listed there.

        @travis - YAML object of a .travis.yml file
        @package - string - package name
        @new_version - string - the version string

        @return - string - the new contents of the file
    """
    # build the environment list incl. the latest version
    env_vars = build_travis_env(travis, package, new_version)
    # and rebuild all combinations
    new_travis = travis.copy()
    new_travis['env'] = calculate_new_travis_env(env_vars)
    return new_travis


def update_github(**kwargs):
    """
        Update GitHub via API
    """
    if "GITHUB_TOKEN" not in os.environ:
        raise RuntimeError("Set the GITHUB_TOKEN variable")

    GITHUB_REPO = kwargs.get('GITHUB_REPO')
    GITHUB_BRANCH = kwargs.get('GITHUB_BRANCH')
    GITHUB_FILE = kwargs.get('GITHUB_FILE')

    # step 1: Get a reference to HEAD
    data = get_url("/repos/%s/git/refs/heads/%s" %
                   (GITHUB_REPO, GITHUB_BRANCH))
    HEAD = {
        'sha': data['object']['sha'],
        'url': data['object']['url'],
    }

    # step 2: Grab the commit that HEAD points to
    data = get_url(HEAD['url'])
    HEAD['commit'] = data

    # step 4: Get a hold of the tree that the commit points to
    data = get_url(HEAD['commit']['tree']['url'])
    HEAD['tree'] = {'sha': data['sha']}

    # intermediate step: get the latest content from GitHub
    # and make an updated version of .travis.yml
    github_file_found = False
    for obj in data['tree']:
        if obj['path'] == GITHUB_FILE:
            data = get_url(obj['url'])  # get the blob from the tree
            data = base64.b64decode(data['content'])
            github_file_found = True
            break

    if not github_file_found:
        raise RuntimeError("Repository %s doesn't contain a file named '%s'!" %
                           (GITHUB_REPO, GITHUB_FILE))

    old_travis = yaml.load(data.rstrip())
    new_travis = update_travis(old_travis,
                               kwargs.get('name'),
                               kwargs.get('version'))

    # bail out if nothing changed
    if new_travis == old_travis:
        print("new == old, bailing out", kwargs)
        return True
    else:
        new_travis = yaml.dump(new_travis, default_flow_style=False)

    # ------------------------------------
    # !!! WARNING WRITE OPERATIONS BELOW
    # ------------------------------------

    # step 3: Post your new file to the server
    data = post_url(
        "/repos/%s/git/blobs" % GITHUB_REPO,
        {
            'content': new_travis,
            'encoding': 'utf-8'
        }
    )
    HEAD['UPDATE'] = {'sha': data['sha']}

    # step 5: Create a tree containing your new file
    data = post_url(
        "/repos/%s/git/trees" % GITHUB_REPO,
        {
            "base_tree": HEAD['tree']['sha'],
            "tree": [{
                "path": GITHUB_FILE,
                "mode": "100644",
                "type": "blob",
                "sha": HEAD['UPDATE']['sha']
            }]
        }
    )
    HEAD['UPDATE']['tree'] = {'sha': data['sha']}

    # step 6: Create a new commit
    data = post_url(
        "/repos/%s/git/commits" % GITHUB_REPO,
        {
            "message": "New dependency %s %s found! \
Auto update %s" % (kwargs.get('name'), kwargs.get('version'), GITHUB_FILE),
            "parents": [HEAD['commit']['sha']],
            "tree": HEAD['UPDATE']['tree']['sha']
            }
    )
    HEAD['UPDATE']['commit'] = {'sha': data['sha']}

    # step 7: Update HEAD, but don't force it!
    data = post_url(
        "/repos/%s/git/refs/heads/%s" % (GITHUB_REPO, GITHUB_BRANCH),
        {
            "sha": HEAD['UPDATE']['commit']['sha']
        }
    )

    if 'object' in data:  # PASS
        return True

    # FAIL
    return data['message']
