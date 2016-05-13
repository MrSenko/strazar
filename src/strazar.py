import os
import sys
import json
import yaml
import base64
import httplib
from pprint import pprint
from datetime import datetime
from itertools import product
from xml.dom.minidom import parseString

def get_url(url, post_data = None):
    # GitHub requires a valid UA string
    headers = {
        'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0.5) Gecko/20120601 Firefox/10.0.5',
    }

    # shortcut for GitHub API calls
    if url.find("://") == -1:
        url = "https://api.github.com%s" % url

    if url.find('api.github.com') > -1:
        if not os.environ.has_key("GITHUB_TOKEN"):
            raise Exception("Set the GITHUB_TOKEN variable")
        else:
            headers.update({
                'Authorization': 'token %s' % os.environ['GITHUB_TOKEN']
            })

    (proto, host_path) = url.split('//')
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

    if (response.status == 404):
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
    rss = get_url("https://pypi.python.org/pypi?:action=rss")
    dom = parseString(rss)
    for item in dom.getElementsByTagName("item"):
        try:
            title = item.getElementsByTagName("title")[0]
            pub_date = item.getElementsByTagName("pubDate")[0]

            (name, version) = title.firstChild.wholeText.split(" ")
            released_on = datetime.strptime(pub_date.firstChild.wholeText, '%d %b %Y %H:%M:%S GMT')

            if name in config.keys():
                for cfg in config[name]:
                    try:
                        args = cfg['args']
                        args.update({
                            'name' : name,
                            'version' : version,
                            'released_on' : released_on
                        })

                        # execute the call back
                        cfg['cb'](**args)
                    except Exception, e:
                        print e
                        continue
        except Exception, e:
            print e
            continue

def build_travis_env(travis, package, new_version):
    """
        Given a parsed YAML object returns an environment
        dict containing all packages and versions including the
        new one.
    """
    env_vars = {}
    for line in travis['env']:
        for item in line.split(' '):
            k, v = item.split('=')
            if k in env_vars:
                env_vars[k].add(v)
            else:
                env_vars[k] = set([v])

    # add the new version to the list
    pkg_name = '_' + package.upper().replace('-', '_')
    env_vars[pkg_name].add(new_version)
    return env_vars


def calculate_new_travis_env(env_vars):
    """
        Rebuilds the environment matrix as Cartesian product of all
        environment variables (aka packages) and their values (aka versions)
    """
    # each element of intermediate is the product (aka combinations) of
    # all versions for a particular package
    _keys = env_vars.keys()
    _keys.sort()
    intermediate = [product([key], env_vars[key]) for key in _keys]

    # each element of new_env is single combination of all packages and
    # versions. this represents one line in the travis environment
    new_env = []
    for p in list(product(*intermediate)):
        new_env.append(' '.join(["%s=%s" % (k, v) for k, v in list(p)]))
    return new_env

def update_travis(data, package, new_version):
    """
        Parses .travis.yml, builds a list of package==version
        from the environment and updates the environment if
        the new version is not listed there.

        @data - string - the text contents of a .travis.yml file
        @package - string - package name
        @new_version - string - the version string

        @return - string - the new contents of the file
    """
    # parse the yaml first
    travis = yaml.load(data)

    # build the environment list incl. the latest version
    env_vars = build_travis_env(travis, package, new_version)
    # and rebuild all combinations
    travis['env'] = calculate_new_travis_env(env_vars)

    return yaml.dump(travis, default_flow_style=False)


def update_github(commit_mode=True, **kwargs):
    """
        Update GitHub via API
    """
    if not os.environ.has_key("GITHUB_TOKEN"):
        raise Exception("Set the GITHUB_TOKEN variable")

    hub = Github(os.environ["GITHUB_TOKEN"])

    GITHUB_REPO = kwargs.get('GITHUB_REPO')
    GITHUB_BRANCH = kwargs.get('GITHUB_BRANCH')
    GITHUB_FILE = kwargs.get('GITHUB_FILE')

    # step 1: Get a reference to HEAD
    data = get_url("/repos/%s/git/refs/heads/%s" % (GITHUB_REPO, GITHUB_BRANCH))
    HEAD = {
        'sha' : data['object']['sha'],
        'url' : data['object']['url'],
    }

    # step 2: Grab the commit that HEAD points to
    data = get_url(HEAD['url'])

    # remove what we don't need for clarity
    for key in data.keys():
        if key not in ['sha', 'tree']:
            del data[key]
    HEAD['commit'] = data


    # step 4: Get a hold of the tree that the commit points to
    data = get_url(HEAD['commit']['tree']['url'])
    HEAD['tree'] = { 'sha' : data['sha'] }

    # intermediate step: get the latest content from GitHub and make an updated version
    for obj in data['tree']:
        if obj['path'] == GITHUB_FILE:
            data = get_url(obj['url']) # get the blob from the tree
            data = base64.b64decode(data['content'])
            break

    old_travis = data.rstrip()
    new_travis = update_travis(old_travis, kwargs.get('package'), kwargs.get('version'))

    # bail out if nothing changed
    if new_travis == old_travis:
        print "new == old, bailing out", kwargs
        return


    ####
    #### WARNING WRITE OPERATIONS BELOW
    ####

    if not commit_mode:
        return

    # step 3: Post your new file to the server
    data = post_url(
                "/repos/%s/git/blobs" % GITHUB_REPO,
                {
                    'content' : new_travis,
                    'encoding' : 'utf-8'
                }
            )
    HEAD['UPDATE'] = { 'sha' : data['sha'] }

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
    HEAD['UPDATE']['tree'] = { 'sha' : data['sha'] }

    # step 6: Create a new commit
    data = post_url(
                "/repos/%s/git/commits" % GITHUB_REPO,
                {
                    "message": "New upstream dependency found! Auto update .travis.yml",
                    "parents": [HEAD['commit']['sha']],
                    "tree": HEAD['UPDATE']['tree']['sha']
                }
            )
    HEAD['UPDATE']['commit'] = { 'sha' : data['sha'] }

    # step 7: Update HEAD, but don't force it!
    data = post_url(
                "/repos/%s/git/refs/heads/%s" % (GITHUB_REPO, GITHUB_BRANCH),
                {
                    "sha": HEAD['UPDATE']['commit']['sha']
                }
            )

    if data.has_key('object'): # PASS
        pass
    else: # FAIL
        print data['message']
