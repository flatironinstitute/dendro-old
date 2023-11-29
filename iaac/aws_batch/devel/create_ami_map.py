import json
import subprocess


def main():
    regions = [
        'af-south-1',
        'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2', 'ap-south-1', 'ap-east-1',
        'ca-central-1',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'eu-south-1', 'eu-central-1',
        'me-south-1',
        'sa-east-1',
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2'
    ]
    ami_map = {}
    for region in regions:
        print(f'Region: {region}')
        cmd = f'aws ssm get-parameter --name /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended --region {region} --output json'
        print(cmd)
        try:
            output = subprocess.check_output(cmd, shell=True)
            output = json.loads(output)
            yy = json.loads(output['Parameter']['Value'])
            image_id = yy['image_id']
            print(f'Image ID: {image_id}')
            ami_map[region] = image_id
        except Exception as e:
            print(f'Error: {e}')
            print('')
            print('')
            continue
        print('')
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print(json.dumps(ami_map, indent=4))

if __name__ == '__main__':
    main()
