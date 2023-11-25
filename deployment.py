#!/usr/bin/python3

import os
import re
import logging

from github import Github, Auth

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
print("LOG_LEVEL = {}".format(LOG_LEVEL))

if LOG_LEVEL == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# parameters
full_repo_name = "danibachar/HomebrewAutoDeplyment"
repo_url = f'https://github.com/{full_repo_name}'
branch_prefix = 'release'

# fetch all tags
tags = os.popen('git ls-remote --tags').read()
logging.debug('tags {}'.format(tags))

# parse tags and get the latest one
tag_list = re.findall(r'refs/tags/(\d+\.\d+\.\d+)', tags)
logging.debug('tag_list {}'.format(tag_list))

latest_tag = tag_list[-1] if tag_list else None
if latest_tag is None:
    raise Exception("Could not find a tag")

# clone the git repo
os.system(f'git clone {repo_url}')
logging.debug('cloning {}'.format(repo_url))

# navigate into the cloned repo (given the default clone command, the folder name would be the repository name)
repo_name = repo_url.split('/')[-1].replace('.git', '')
os.chdir(repo_name)

# create branch name from the latest tag
branch = "{}_{}".format(branch_prefix, latest_tag)
# create and checkout new branch
os.system(f'git checkout -b {branch}')
logging.debug('new branch {}'.format(branch))

# create a new file
new_formula_file_name = f"tuist@{latest_tag}.rb"
os.system(f'touch {new_formula_file_name}')
logging.debug('new homebrew formula {}'.format(new_formula_file_name))

# stage changes
os.system('git add .')

# commit changes
os.system(f'git commit -m "New Formula {new_formula_file_name}"')

# push changes
os.system(f'git push --set-upstream origin {branch}')

logging.debug('Starting Authentication')
access_token = os.environ.get("DANIEL_GITHUB_ACCESS_TOKEN", None)

if access_token is None:
    raise Exception("No access token, cannot authenticate with GitHub")

# using an access token
auth = Auth.Token(access_token)
# Public Web Github
g = Github(auth=auth)
logging.debug('Authentication Done')

# get the repo by name
repo = g.get_repo(full_repo_name)
# create a GitHub pull request
logging.debug('Creating PR')

pr = repo.create_pull(
    title=f'Release {latest_tag}',
    body='Created from automated script',
    head=branch,
    base='main'
)
logging.info(f"created new PR {pr}")
