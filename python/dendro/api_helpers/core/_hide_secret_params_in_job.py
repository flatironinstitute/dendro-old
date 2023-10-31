from ...common.dendro_types import DendroJob


def _hide_secret_params_in_job(job: DendroJob):
    for param in job.inputParameters:
        if param.secret:
            param.value = None
