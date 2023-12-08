GitHub Repository Archiver Script
=================================

Installation and Setup
----------------------

### Prerequisites

*   Python 3.x
*   Git
*   Required Python libraries: `requests`, `tqdm`
    *   Install them using `pip install requests tqdm`

### Folder Structure

Before running the script, ensure your desired folder structure is set up. Here's an example structure:

mathematica

```mathematica
ArchiveFolder/
├── RepositoryName1/
│   ├── Wiki/
│   ├── Release-Tag1/
│   ├── Prerelease-Tag1/
│   ├── README.md
│   └── description.txt
└── RepositoryName2/
    ├── Wiki/
    ├── Release-Tag2/
    ├── Prerelease-Tag2/
    ├── README.md
    └── description.txt
```

### Configuration

1.  Clone or download this script to your local machine.
2.  Open the script in a text editor.
3.  Set the `base_folder` path in the `main()` function to your desired archive location.
    
    python
    
    ```python
    base_folder = "C:\\Path\\To\\Your\\ArchiveFolder\\"
    ```
    
4.  If you need to use a GitHub token for private repositories or higher rate limits, set the `github_token` variable.
    
    python
    
    ```python
    github_token = "your_github_token_here"
    ```
    

Usage
-----

### Using the Script

1.  To run the script, open a terminal or command prompt.
2.  Navigate to the script's directory.
3.  Run the script using Python:
    
    bash
    
    ```bash
    python script_name.py
    ```
    
4.  If `use_text_file` is set to `True` in the script:
    *   Create a `urls.txt` file in the same directory as the script.
    *   Add GitHub repository URLs you want to archive, each on a new line.
5.  If `use_text_file` is set to `False`:
    *   You will be prompted to enter the GitHub repository URL directly in the terminal.

The script will clone the repositories, download wikis (if available), fetch release/prerelease assets, and organize them into the specified archive folder.