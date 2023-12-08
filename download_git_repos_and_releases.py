import requests
import os
import shutil
from subprocess import call
from tqdm import tqdm

def download_file(url, output_path):
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

def download_assets_from_release(release_data, release_folder):
    os.makedirs(release_folder, exist_ok=True)
    print(f"Downloading assets for release: {release_data['tag_name']}")

    if 'assets' in release_data and release_data['assets']:
        for asset in release_data['assets']:
            asset_url = asset['browser_download_url']
            asset_name = asset['name']
            asset_path = os.path.join(release_folder, asset_name)

            print(f"Downloading {asset_name}...")
            download_file(asset_url, asset_path)
    else:
        print(f"No assets available for release: {release_data['tag_name']}")

def download_assets(repo_url, base_folder, github_token):
    try:
        # Extract repository owner and name from URL
        split_url = repo_url.rstrip('/').split('/')
        repo_owner, repo_name = split_url[-2], split_url[-1]

        # Prepare folder structure
        repo_folder = os.path.join(base_folder, repo_name)
        os.makedirs(repo_folder, exist_ok=True)

        # Clone the repository
        call(['git', 'clone', repo_url, os.path.join(repo_folder, repo_name)])

        # Copy README.md up a subfolder
        readme_src = os.path.join(repo_folder, repo_name, 'README.md')
        readme_dst = os.path.join(repo_folder, 'README.md')
        if os.path.exists(readme_src):
            shutil.copy(readme_src, readme_dst)

        # Fetch repository details for description
        repo_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        response = requests.get(repo_api_url)
        if response.ok:
            repo_data = response.json()
            with open(os.path.join(repo_folder, 'description.txt'), 'w', encoding='utf-8') as f:
                f.write(repo_data.get('description', 'No description available'))

        # Check if the repository has a wiki
        wiki_url = f"{repo_url}.wiki.git"
        wiki_folder = os.path.join(repo_folder, 'Wiki')
        wiki_clone_response = call(['git', 'clone', wiki_url, wiki_folder])

        if wiki_clone_response != 0:  # Non-zero return code indicates cloning failed
            print(f"No wiki available or accessible for {repo_url}")

        # Headers for authentication (if needed)
        headers = {'Authorization': f'token {github_token}'} if github_token else {}

        # Download assets from the latest release
        release_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        release_response = requests.get(release_url, headers=headers)
        if release_response.ok:
            release_data = release_response.json()
            release_folder = os.path.join(repo_folder, f"Release-{release_data['tag_name']}")
            download_assets_from_release(release_data, release_folder)

        # Download assets from the latest prerelease
        prerelease_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=1&prerelease=true"
        prerelease_response = requests.get(prerelease_url, headers=headers)
        if prerelease_response.ok and prerelease_response.json():
            prerelease_data = prerelease_response.json()[0]  # Get the first prerelease
            prerelease_folder = os.path.join(repo_folder, f"Prerelease-{prerelease_data['tag_name']}")
            download_assets_from_release(prerelease_data, prerelease_folder)

    except Exception as e:
        print(f"An error occurred with {repo_url}: {e}")

def main():
    # Toggle for choosing input method
    use_text_file = True  # Set to False to use terminal input

    # Base download folder - Replace with your preferred folder
    base_folder = "C:\\Users\\ianco\\Downloads\\File Archiving\\"
    
    # Your GitHub token, if needed for authentication
    github_token = ""  

    if use_text_file:
        with open('urls.txt', 'r') as file:
            for repo_url in file:
                repo_url = repo_url.strip()
                if repo_url:
                    download_assets(repo_url, base_folder, github_token)
    else:
        # User input for repository URL
        repo_url = input("Enter the GitHub repository URL (e.g., 'https://github.com/jellyfin/jellyfin-meta'): ").strip()
        download_assets(repo_url, base_folder, github_token)

if __name__ == "__main__":
    main()