# Linked analysis

{% if project.analysisSourceUrl %}

You are viewing the linked analysis for this project. This is a read-only view of a directory in a Git repository.

[{{ project.analysisSourceUrl }}]({{ project.analysisSourceUrl }})

You can edit this analysis in at least four ways.

<details>
<summary>Clone and edit locally with VS Code</summary>

You can clone and edit the analysis locally with VS Code:

```bash
git clone {{ project.analysisSource.repoUrl }}
cd {{ project.analysisSource.repoName }}
git checkout {{ project.analysisSource.branch }}
{% if project.analysisSource.path %}cd {{ project.analysisSource.path }}{% endif %}
```

Then open the directory in VS Code.

```
code .
```

VS Code has built-in support for ipynb files. You can edit and run notebooks directly in VS Code. You can also use the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) for linting, debugging, and other features. If you have a subscription to GitHub Copilot, you can use it with the GitHub Copilot extension. Finally VS Code has built-in support for Git, so you can commit and push changes back to your GitHub repository.

It is recommended that you use a dedicated Conda environment.

You should consider whether you want to commit the content in the output Jupyter notebook cells, as this can make the size of the repository grow quickly.

</details>

<details>
<summary>Clone and edit locally with Jupyter Lab</summary>

You can clone and edit the analysis locally with Jupyter Lab:

```bash
git clone {{ project.analysisSource.repoUrl }}
cd {{ project.analysisSource.repoName }}
git checkout {{ project.analysisSource.branch }}
{% if project.analysisSource.path %}cd {{ project.analysisSource.path }}{% endif %}
```

Then open the directory in Jupyter Lab.

```
jupyter lab
```

Note that you must have Jupyter Lab installed locally.

It is recommended that you use a dedicated Conda environment.

As you make changes, you can commit and push them back to your GitHub repository. You should consider whether you want to commit the content in the output Jupyter notebook cells, as this can make the size of the repository grow quickly.

</details>

<details>
<summary>Clone and edit on Dandihub</summary>

You can clone and edit the analysis on [Dandihub](https://hub.dandiarchive.org/).

First, you must [register an account](https://dandiarchive.org/) on DANDI and Dandihub.

Then open a machine instance on [Dandihub](https://hub.dandiarchive.org/).

Then follow the instructions above for cloning and editing locally with Jupyter Lab. Note that in order to clone the repo, you will need to open a terminal within Jupyter Lab and run the git commands there.

</details>

<details>
<summary>Edit using GitHub Codespaces</summary>

If you don't need to perform heavy computations, Codespaces is a great way to edit your analysis in a way that is tightly integrated with your git repository.

First, navigate to [your repository]({{ project.analysisSource.repoUrl }}) on GitHub. Then click the "Code" button and create a new Codespace. Essentially you get VS Code in the browser. You can install extensions, including Python, and Copilot, and you can run Jupyter notebooks. You can also open a terminal and issue commands to run scripts.

A notable difference is that in the browser-based VS Code, files are saved on edit (no need to press Ctrl+S). But you can still control which files are committed back to the repository.

</details>


{% else %}

This project does not have an associated linked analysis. If you have editor permissions, you can configure a linked analysis on the home tab of the project. Navigate to the directory of your analysis on GitHub and copy/paste the URL in the address bar of your browser. For now only GitHub is supported.

{% endif %}