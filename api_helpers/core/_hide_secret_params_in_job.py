from .protocaas_types import ProtocaasJob


def _hide_secret_params_in_job(job: ProtocaasJob):
    for param in job.inputParameters:
        if param.secret:
            param.value = None