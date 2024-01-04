# Project analysis

You are viewing the analysis for this project.

{% if project.analysisSourceUrl %}

This is a read-only view of a directory in a Git repository.

[{{ project.analysisSourceUrl }}]({{ project.analysisSourceUrl }})

You can clone and edit the analysis locally or on [dandi-hub](https://hub.dandiarchive.org):

```bash
git clone {{ project.analysisSource.repoUrl }}
cd {{ project.analysisSource.repoName }}
git checkout {{ project.analysisSource.branch }}
{% if project.analysisSource.path %}
cd {{ project.analysisSource.path }}
{% endif %}
```


{% else %}

This project does not have an associated analysis. If you have editor permissions, you can configure an analysis on the home tab of the project. Navigate to the directory of your analysis on GitHub and copy/paste the URL in the address bar of your browser. For now only GitHub is supported.

{% endif %}