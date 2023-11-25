#!/usr/bin/python3

import os
import re
import logging

from github import Github, Auth

# Constants
full_repo_name = "danibachar/HomebrewAutoDeplyment"
repo_url = f'https://github.com/{full_repo_name}'
branch_prefix = 'release'
template_name = "../tuist-formula-template.rb"

def _set_logging():
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    print("LOG_LEVEL = {}".format(LOG_LEVEL))

    if LOG_LEVEL == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)\

def _get_tag():
    # fetch all tags
    tags = os.popen('git ls-remote --tags').read()
    logging.debug('tags {}'.format(tags))

    # parse tags and get the latest one
    tag_list = re.findall(r'refs/tags/(\d+\.\d+\.\d+)', tags)
    logging.debug('tag_list {}'.format(tag_list))

    latest_tag = tag_list[-1] if tag_list else None
    if latest_tag is None:
        raise Exception("Could not find a tag")
    return latest_tag

def _prepare_repo_locally():
    # clone the git repo
    logging.debug('cloning {}'.format(repo_url))
    os.system(f'git clone {repo_url}')
    # navigate into the cloned repo (given the default clone command, the folder name would be the repository name)
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    os.chdir(repo_name)

def _checkout_branch_by(tag):
    # create branch name from the latest tag
    branch = "{}_{}".format(branch_prefix, tag)
    # create and checkout new branch
    os.system(f'git checkout -b {branch}')
    logging.debug('new branch {}'.format(branch))
    return branch
    
def _create_formula_file_by(tag):
    # create a new file
    # TuistAT3260
    new_formula_file_name = f"tuist@{tag}.rb"
    os.system(f'mv {template_name} ./{new_formula_file_name}')
    logging.debug('new homebrew formula {}'.format(new_formula_file_name))
    return new_formula_file_name

def _commit_and_push(branch, message):
    # stage changes
    os.system('git add .')
    # commit changes
    os.system(f'git commit -m {message}')
    # push changes
    os.system(f'git push --set-upstream origin {branch}')

def _github_auth():
    logging.debug('Starting Authentication')
    access_token = os.environ.get("DANIEL_GITHUB_ACCESS_TOKEN", None)
    if access_token is None:
        raise Exception("No access token, cannot authenticate with GitHub")
    # using an access token
    auth = Auth.Token(access_token)
    # Public Web Github
    g = Github(auth=auth)
    logging.debug('Authentication Done')
    return g

def _create_pr_with(g, branch, title):
    logging.debug('Creating PR')
    # get the repo by name
    repo = g.get_repo(full_repo_name)
    # create a GitHub pull request
    pr = repo.create_pull(
        title=title,
        body='Created from automated script',
        head=branch,
        base='main'
    )
    logging.info(f"created new PR {pr}")

###############
# MAIN SCRIPT #
###############

_set_logging()
tag = _get_tag()
_prepare_repo_locally()
branch = _checkout_branch_by(tag)
formula_file_name = _create_formula_file_by(tag)
_commit_and_push(branch=branch, message=f"New Formula {formula_file_name}")
g = _github_auth()
_create_pr(g, branch=branch, title=f'Release {tag}')

