from typing import Optional
import os
import time
import click
from .compute_resource.register_compute_resource import register_compute_resource as register_compute_resource_function
from .compute_resource.start_compute_resource import start_compute_resource as start_compute_resource_function
from .sdk._make_spec_file import make_app_spec_file_function
from .sdk._test_app_processor import test_app_processor_function

# ------------------------------------------------------------
# Compute resource cli
# ------------------------------------------------------------
@click.command(help='Initialize a compute resource controller in the current directory')
@click.option('--compute-resource-id', default=None, help='Compute resource ID')
@click.option('--compute-resource-private-key', default=None, help='Compute resource private key')
def register_compute_resource(compute_resource_id: str, compute_resource_private_key: str):
    register_compute_resource_function(dir='.', compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key)


@click.command(help="Start the compute resource controller in the current directory")
@click.option('--timeout', default=None, type=float, help='Timeout (sec) for the daemon - used for testing')
def start_compute_resource(timeout: Optional[float] = None):
    start_compute_resource_function(dir='.', timeout=timeout)
    # unfortunately, the pubnub background thread cannot be terminated, so we have to force-exit the process
    # I opened a ticket with pubnub about this, and they acknowledged that it's a problem, but they don't seem to be fixing it
    os._exit(0)


# ------------------------------------------------------------
# App cli
# ------------------------------------------------------------
@click.command(help='Make an app spec file')
@click.option('--app-dir', default='.', help='Path to the app directory')
@click.option('--spec-output-file', default=None, help='Output file for the spec')
def make_app_spec_file(app_dir: str, spec_output_file: str):
    make_app_spec_file_function(app_dir=app_dir, spec_output_file=spec_output_file)

# ------------------------------------------------------------
# Mock job cli
# ------------------------------------------------------------
@click.command(help='Run a mock job (used during testing)')
def run_mock_job():
    print('Running mock job')
    time.sleep(0.001) # don't pause too long
    print('Mock job completed')


# ------------------------------------------------------------
# Test app processor
# ------------------------------------------------------------
@click.command(help='Run an app processor (used for testing)')
@click.option('--app-dir', default='.', help='Path to the app directory')
@click.option('--processor', default=None, help='Name of the processor to run')
@click.option('--context', default=None, help='Path to the context file (.json or .yaml)')
def test_app_processor(app_dir: str, processor: str, context: str):
    test_app_processor_function(app_dir=app_dir, processor=processor, context=context)

# ------------------------------------------------------------
# Main cli
# ------------------------------------------------------------
@click.group(help="dendro command line interface")
def main():
    pass

main.add_command(register_compute_resource)
main.add_command(start_compute_resource)
main.add_command(make_app_spec_file)
main.add_command(test_app_processor)
main.add_command(run_mock_job)
