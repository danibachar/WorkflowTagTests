#!/usr/bin/python3

import os, re, logging, subprocess
from github import Github, Auth
from sys import platform

# Constants
full_repo_name = "danibachar/HomebrewAutoDeplyment"
repo_url = f'https://github.com/{full_repo_name}'
branch_prefix = 'release'

# MARK: - Helpers

def _run_command(command):
    logging.debug(f"Running command {command}")
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

def _set_logging():
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    print("LOG_LEVEL = {}".format(LOG_LEVEL))

    if LOG_LEVEL == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)\

# MARK: - Formula builder

def _create_new_formula(
    template_name, 
    new_formula_file_name, 
    formula_placeholder,
    sha_placeholder,
    url_placeholder
):
    logging.debug(f'''
        Creating formula from {template_name}
        New formula file {new_formula_file_name}
        Formula rb name {formula_placeholder}
        Formula SHA {sha_placeholder}
        Formula URL {url_placeholder}
        ''')
    
    _run_command(f'cp {template_name} ./{new_formula_file_name}')

    if platform == "linux" or platform == "linux2":
        _run_command(f"sed -i 's|_FORMULA_|{formula_placeholder}|g' {new_formula_file_name}")
        _run_command(f"sed -i 's|_SHA_|\"{sha_placeholder}\"|g' {new_formula_file_name}")
        _run_command(f"sed -i 's|_URL_|\"{url_placeholder}\"|g' {new_formula_file_name}")
    elif platform == "darwin":
        _run_command(f"sed -i '' 's|_FORMULA_|{formula_placeholder}|g' {new_formula_file_name}")
        _run_command(f"sed -i '' 's|_SHA_|\"{sha_placeholder}\"|g' {new_formula_file_name}")
        _run_command(f"sed -i '' 's|_URL_|\"{url_placeholder}\"|g' {new_formula_file_name}")
    else:
        raise Exception(f"Not supported platform {platform}")

    logging.debug(f'New Homebrew formula created successfully at {new_formula_file_name}')

def _create_new_tuistenv_formula_by(tag, sha, url):
    _create_new_formula(
        template_name="../tuistenv_template.rb",
        new_formula_file_name=f"tuistenv@{tag}.rb",
        formula_placeholder=f"TuistenvAt{tag}".replace(".", ""),
        sha_placeholder=sha,
        url_placeholder=url
    )

def _create_new_tuist_formula_by(tag, sha, url):
    _create_new_formula(
        template_name="../tuist_template.rb",
        new_formula_file_name=f"tuist@{tag}.rb",
        formula_placeholder=f"TuistAt{tag}".replace(".", ""),
        sha_placeholder=sha,
        url_placeholder=url
    )

def _create_new_formulas_by(tag):
    # package_url = f"https://github.com/danibachar/tuist/archive/refs/tags/{tag}.tar.gz" #
    package_url = f"https://github.com/danibachar/WorkflowTagTests/archive/refs/tags/{tag}.tar.gz" # 
    _run_command(f"curl {package_url} -o package.zip -s")
    new_sha = _run_command("shasum -a 256 package.zip | cut -d ' ' -f 1").strip()

    _create_new_tuist_formula_by(tag, new_sha, package_url)
    _create_new_tuistenv_formula_by(tag, new_sha, package_url)

# MARK: - Git operations

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
    _run_command(f'git clone {repo_url}')
    # navigate into the cloned repo (given the default clone command, the folder name would be the repository name)
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    os.chdir(repo_name)
    _run_command(f"git config --local user.email \"{os.environ.get("GIT_AUTHOR_EMAIL")}\"")
    _run_command(f"git config --local user.name \"{os.environ.get("GITLAB_USER_ID")}\"") 

def _checkout_branch_by(tag):
    # create branch name from the latest tag
    branch = "{}_{}".format(branch_prefix, tag)
    # create and checkout new branch
    _run_command(f'git checkout -b {branch}')
    logging.debug('new branch {}'.format(branch))
    return branch

def _commit_and_push(branch, message):
    # stage changes
    _run_command('git add .')
    # commit changes
    _run_command(f'git commit -m \"{message}\"')
    # push changes
    _run_command(f'git push --set-upstream origin {branch}')

# MARK: - GitHub Operations

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
    logging.debug(f'Creating PR from branch {branch}')
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
_create_new_formulas_by(tag)
_commit_and_push(branch=branch, message=f"New Release {tag}")
g = _github_auth()
_create_pr_with(g, branch=branch, title=f'Release {tag}')
# logging.debug(f'Creating PR from branch {branch}')
# # get the repo by name
# repo = g.get_repo(full_repo_name)
# # create a GitHub pull request
# pr_command = f'''
# curl -L \
#   -X POST \
#   -H "Accept: application/vnd.github+json" \
#   -H "Authorization: Bearer {access_token}" \
#   -H "X-GitHub-Api-Version: 2022-11-28" \
#   https://api.github.com/repos/danibachar/HomebrewAutoDeplyment/pulls \
#   -d '{{"title":"Amazing new feature","body":"Please pull these awesome changes in!","head":"{branch}","base":"main"}}'
# '''
# pr = _run_command(pr_command)
# # pr = repo.create_pull(
# #     title=f"Release {tag}",
# #     body='Created from automated script',
# #     head=f"danibachar:{branch}",
# #     base='main'
# # )
# logging.info(f"created new PR {pr}")