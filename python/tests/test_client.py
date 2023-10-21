from protocaas.client import load_project


def test_load_project():
    # if this project or file disappears then we'll need to update that here
    project_id = 'ed104ee8'
    file_name = 'imported/000618/sub-paired-kampff/sub-paired-kampff_ses-paired-kampff-2014-11-25-Pair-3-0_ecephys.nwb'
    project = load_project(project_id)
    file = project.get_file(file_name)
    assert file.get_url().startswith('https://')

    folder = project.get_folder('imported')
    assert len(folder.get_folders()) >= 1