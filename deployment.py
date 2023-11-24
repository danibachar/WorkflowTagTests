#!/usr/bin/python3

import os
import re
import logging

if os.environ["LOG_LEVEL"] == "DEBUG":
    logging.basicConfig(filename='deploy.log', level=logging.DEBUG)
else:
    logging.basicConfig(filename='deploy.log', level=logging.INFO)

# parameters
repo_url = 'https://github.com/danibachar/BreFormoulaDeployment'
branch_prefix = 'release_'

# fetch all tags
tags = os.popen('git ls-remote --tags').read()
logging.debug('tags {}'.format(tags))

# parse tags and get the latest one
tag_list = re.findall(r'refs/tags/(.+)', tags)
logging.debug('tag_list {}'.format(tag_list))

latest_tag = tag_list[-1] if tag_list else None
if latest_tag is None:
    raise Exception("Could not find a tag")

# create branch name from the latest tag
branch = latest_tag.replace('.', branch_prefix)
logging.debug('branch {}'.format(branch))

# clone the git repo
os.system(f'git clone {repo_url}')

# navigate into the cloned repo (given the default clone command, the folder name would be the repository name)
repo_name = repo_url.split('/')[-1].replace('.git', '')
os.chdir(repo_name)

# create and checkout new branch
os.system(f'git checkout -b {branch}')

# create a new file
new_formula_file_name = f"tuist@{latest_tag}.rb"
os.system(f'touch {new_formula_file_name}')

# stage changes
os.system('git add .')

# commit changes
os.system(f'git commit -m "New Formula {new_formula_file_name}"')

# push changes
os.system('git push origin {branch}')