import click
from .compute_resource.register_compute_resource import register_compute_resource as register_compute_resource_function
from .compute_resource.start_compute_resource import start_compute_resource as start_compute_resource_function

@click.group(help="protocaas command line interface")
def main():
    pass

@click.command(help='Initialize a compute resource node in the current directory')
@click.option('--compute-resource-id', default=None, help='Compute resource ID')
@click.option('--compute-resource-private-key', default=None, help='Compute resource private key')
def register_compute_resource(compute_resource_id: str, compute_resource_private_key: str):
    register_compute_resource_function(dir='.', compute_resource_id=compute_resource_id, compute_resource_private_key=compute_resource_private_key)

@click.command(help="Start the compute resource node in the current directory")
def start_compute_resource():
    start_compute_resource_function(dir='.')

main.add_command(register_compute_resource)
main.add_command(start_compute_resource)