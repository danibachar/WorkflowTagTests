#!/bin/bash

# Env vars
target_repo_name="$TARGET_REPO_NAME"
if [ -z "$target_repo_name" ]; then
    echo "No target repo name, please set TARGET_REPO_NAME environment variable"
    exit 1
fi

access_token="$GITHUB_ACCESS_TOKEN"
if [ -z "$access_token" ]; then
    echo "No access token, cannot authenticate with GitHub. Please set GITHUB_ACCESS_TOKEN environment variable"
    exit 1
fi

branch_prefix="${RELEASE_BRANCH_PREFIX:-release}"
git_email="${TUIST_GIT_EMAIL:-}"
git_user="${GITHUB_REPOSITORY_OWNER:-}"

# Constants
target_repo_url="https://github.com/$target_repo_name"
tuist_package_repo_url="https://github.com/tuist/tuist"

# Helpers
_create_new_formula() {
    template_name="$1"
    new_formula_file_name="$2"
    formula_placeholder="$3"
    sha_placeholder="$4"
    url_placeholder="$5"

    echo "Creating formula from $template_name"
    echo "New formula file: $new_formula_file_name"
    echo "Formula rb name: $formula_placeholder"
    echo "Formula SHA: $sha_placeholder"
    echo "Formula URL: $url_placeholder"

    cp $template_name ./$new_formula_file_name

    if [ "$(uname)" == "Darwin" ]; then
        sed -i '' "s|_FORMULA_|$formula_placeholder|g" "$new_formula_file_name"
        sed -i '' "s|_SHA_|\"$sha_placeholder\"|g" "$new_formula_file_name"
        sed -i '' "s|_URL_|\"$url_placeholder\"|g" "$new_formula_file_name"
    else
        sed -i "s|_FORMULA_|$formula_placeholder|g" "$new_formula_file_name"
        sed -i "s|_SHA_|\"$sha_placeholder\"|g" "$new_formula_file_name"
        sed -i "s|_URL_|\"$url_placeholder\"|g" "$new_formula_file_name"
    fi

    echo "New Homebrew formula created successfully at $new_formula_file_name"
}

_create_new_tuistenv_formula_by() {
    tag="$1"
    sha="$2"
    url="$3"

    _create_new_formula "../make/tasks/homebrew/tuistenv_template.rb" "tuistenv@$tag.rb" "TuistenvAt${tag//./}" "$sha" "$url"
}

_create_new_tuist_formula_by() {
    tag="$1"
    sha="$2"
    url="$3"

    _create_new_formula "../make/tasks/homebrew/tuist_template.rb" "tuist@$tag.rb" "TuistAt${tag//./}" "$sha" "$url"
}

_create_new_formulas_by() {
    tag="$1"
    package_url="${tuist_package_repo_url}/archive/refs/tags/${tag}.tar.gz"
    curl $package_url -o package.zip -s
    new_sha="$(shasum -a 256 package.zip | cut -d ' ' -f 1 | tr -d '\n')"

    _create_new_tuist_formula_by "$tag" "$new_sha" "$package_url"
    _create_new_tuistenv_formula_by "$tag" "$new_sha" "$package_url"
}

_get_tag() {
    tags=$(git ls-remote --tags)
    echo "tags $tags"

    tag_list=($(echo "$tags" | grep -o 'refs/tags/[0-9.]\+' | sed 's|refs/tags/||g'))
    echo "tag_list ${tag_list[*]}"

    latest_tag="${tag_list[-1]}"
    if [ -z "$latest_tag" ]; then
        echo "Could not find a tag"
        exit 1
    fi
    echo "$latest_tag"
}

_prepare_repo_locally() {
    echo "cloning $target_repo_url"
    git clone $target_repo_url
    repo_name=$(echo "$target_repo_url" | awk -F'/' '{print $(NF-0)}' | sed 's/.git$//')
    cd "$repo_name" || exit
    git config --local user.email $git_email
    git config --local user.name $git_user
}

_checkout_branch_by() {
    tag="$1"
    branch="${branch_prefix}_${tag}"
    git checkout -b $branch
    echo "new branch $branch"
    echo "$branch"
}

_commit_and_push() {
    branch="$1"
    message="$2"
    git remote set-url origin https://$git_user:$access_token@github.com/$target_repo_name
    git add .
    git reset -- filename
    git commit -m \"$message\"
    git push --set-upstream origin $branch
}

_github_auth() {
    echo "Starting Authentication"
    echo "Authentication Done"
}

_create_pr_with() {
    branch="$1"
    title="$2"
    echo "Creating PR from branch $branch"

    curl -L \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $access_token" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    $target_repo_url/pulls \
    -d '{'title':'$title','body':'Created from automated script','head':'$branch','base':'main'}'

    echo "created new PR with title: $title"

}

###############
# MAIN SCRIPT #
###############

tag=$(_get_tag)
_prepare_repo_locally
branch=$(_checkout_branch_by "$tag")
_create_new_formulas_by "$tag"
_commit_and_push "$branch" "Release $tag"
_github_auth
_create_pr_with "$branch" "Release $tag"

exit 0