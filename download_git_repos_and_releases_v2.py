import argparse
import requests
import os
import shutil
import subprocess
from tqdm import tqdm

def download_file(url, output_path):
    if not os.path.exists(output_path):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f, tqdm(
            desc=url,
            total=int(response.headers.get('content-length', 0)),
            unit='iB',
            unit_scale=True,
            unit_divisor=1024
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                size = f.write(chunk)
                bar.update(size)
    else:
        print(f"File already exists: {output_path}")

def get_remote_file_list(release_data):
    return {asset['name'] for asset in release_data.get('assets', [])}

def download_assets_from_release(release_data, release_folder, num_to_fetch):
    if not os.path.exists(release_folder):
        os.makedirs(release_folder, exist_ok=True)
    print(f"Checking assets for release: {release_data['tag_name']}")

    remote_files = get_remote_file_list(release_data)
    local_files = set(os.listdir(release_folder)) if os.path.exists(release_folder) else set()

    missing_files = remote_files - local_files

    for file_name in missing_files:
        asset = next((asset for asset in release_data['assets'] if asset['name'] == file_name), None)
        if asset:
            asset_url = asset['browser_download_url']
            asset_path = os.path.join(release_folder, file_name)
            print(f"Downloading {file_name}...")
            download_file(asset_url, asset_path)

def update_repository(repo_folder, github_token):
    print(f"Updating repository: {repo_folder}")
    repo_clone_path = os.path.join(repo_folder, os.path.basename(repo_folder))
    if os.path.exists(repo_clone_path):
        # Perform a git pull to update the repository and capture its output
        git_pull_result = subprocess.run(['git', '-C', repo_clone_path, 'pull'], capture_output=True, text=True)
        print(git_pull_result.stdout)
    else:
        print(f"Repository not found for updating: {repo_clone_path}")

    # Copy README.md back to the first directory, if it exists and is different
    readme_src = os.path.join(repo_clone_path, 'README.md')
    readme_dst = os.path.join(repo_folder, 'README.md')
    if os.path.exists(readme_src) and (not os.path.exists(readme_dst) or not os.path.samefile(readme_src, readme_dst)):
        shutil.copy(readme_src, readme_dst)

    # Re-fetch and overwrite description.txt
    repo_api_url = f"https://api.github.com/repos/{os.path.basename(repo_folder)}"
    response = requests.get(repo_api_url, headers={'Authorization': f'token {github_token}'} if github_token else {})
    if response.ok:
        repo_data = response.json()
        with open(os.path.join(repo_folder, 'description.txt'), 'w', encoding='utf-8') as f:
            f.write(repo_data.get('description', 'No description available'))

def update_repositories(base_folder, github_token, releases, prereleases):
    for repo_name in os.listdir(base_folder):
        repo_folder = os.path.join(base_folder, repo_name)
        if os.path.isdir(repo_folder):
            update_repository(repo_folder, github_token)
            download_assets(f"https://github.com/{repo_name}", base_folder, github_token, releases, prereleases)

def download_assets(repo_url, base_folder, github_token, releases, prereleases):
    try:
        # Extract repository owner and name from URL
        split_url = repo_url.rstrip('/').split('/')
        repo_owner, repo_name = split_url[-2], split_url[-1]

        # Prepare folder structure
        repo_folder = os.path.join(base_folder, repo_name)
        os.makedirs(repo_folder, exist_ok=True)

        # Clone the repository only if it doesn't exist
        repo_clone_path = os.path.join(repo_folder, repo_name)
        if not os.path.exists(repo_clone_path):
            subprocess.run(['git', 'clone', repo_url, repo_clone_path], check=True)
        else:
            print(f"Repository already cloned: {repo_clone_path}")

        # Copy README.md up a subfolder only if it doesn't exist
        readme_src = os.path.join(repo_folder, repo_name, 'README.md')
        readme_dst = os.path.join(repo_folder, 'README.md')
        if os.path.exists(readme_src) and not os.path.exists(readme_dst):
            shutil.copy(readme_src, readme_dst)

        # Fetch repository details for description
        repo_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        response = requests.get(repo_api_url)
        if response.ok:
            repo_data = response.json()
            with open(os.path.join(repo_folder, 'description.txt'), 'w', encoding='utf-8') as f:
                f.write(repo_data.get('description', 'No description available'))

        # Check and clone the wiki only if it doesn't exist
        wiki_url = f"{repo_url}.wiki.git"
        wiki_folder = os.path.join(repo_folder, 'Wiki')
        if not os.path.exists(wiki_folder):
            os.makedirs(wiki_folder, exist_ok=True)
            wiki_clone_result = subprocess.run(['git', 'clone', wiki_url, wiki_folder], capture_output=True, text=True)
            if wiki_clone_result.returncode != 0:
                shutil.rmtree(wiki_folder)  # Remove the created Wiki folder if cloning fails
                print(f"No wiki available or accessible for {repo_url}")
        else:
            print(f"Wiki already cloned: {wiki_folder}")

        # Headers for authentication (if needed)
        headers = {'Authorization': f'token {github_token}'} if github_token else {}

        # Fetch and download specified number of latest releases
        releases_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page={releases}"
        releases_response = requests.get(releases_url, headers=headers)
        if releases_response.ok:
            for release_data in releases_response.json():
                if not release_data['prerelease']:
                    release_folder = os.path.join(repo_folder, f"Release-{release_data['tag_name']}")
                    download_assets_from_release(release_data, release_folder, releases)

        # Fetch and download specified number of latest prereleases
        prereleases_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page={prereleases}&prerelease=true"
        prereleases_response = requests.get(prereleases_url, headers=headers)
        if prereleases_response.ok:
            for prerelease_data in prereleases_response.json():
                prerelease_folder = os.path.join(repo_folder, f"Prerelease-{prerelease_data['tag_name']}")
                download_assets_from_release(prerelease_data, prerelease_folder, prereleases)

    except Exception as e:
        print(f"An error occurred with {repo_url}: {e}")

def main():
    folder = 'H:/File Archiving'
    
    parser = argparse.ArgumentParser(description="Download and organize GitHub repository releases.")
    parser.add_argument('--use-text-file', action='store_true', help='Use URLs from a text file')
    parser.add_argument('--base-folder', type=str, default=f'{folder}', help='Base folder for downloads')
    parser.add_argument('--github-token', type=str, default="", help='GitHub token for authentication')
    parser.add_argument('--releases', type=int, default=1, help='Number of latest releases to fetch')
    parser.add_argument('--prereleases', type=int, default=1, help='Number of latest prereleases to fetch')
    parser.add_argument('--urls-file', type=str, default='urls.txt', help='Path to the text file with URLs')
    parser.add_argument('-u', '--update', action='store_true', help='Update existing repositories')

    args = parser.parse_args()


    if args.update:
        update_repositories(args.base_folder, args.github_token, args.releases, args.prereleases)
    elif args.use_text_file:
        with open(args.urls_file, 'r') as file:
            for repo_url in file:
                repo_url = repo_url.strip()
                if repo_url:
                    download_assets(repo_url, args.base_folder, args.github_token, args.releases, args.prereleases)
    else:
        # Prompt user for repository URL
        repo_url = input("Enter the GitHub repository URL (e.g., 'https://github.com/author/repository'): ").strip()
        download_assets(repo_url, args.base_folder, args.github_token, args.releases, args.prereleases)

if __name__ == "__main__":
    main()