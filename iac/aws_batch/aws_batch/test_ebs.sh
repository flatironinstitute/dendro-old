#!/bin/bash

# Define the tag for searching the EBS volume
VOLUME_TAG_KEY="dendrotag"
VOLUME_TAG_VALUE="pipeline001"
DEVICE="/dev/sdf"
MOUNT_POINT="/dendro-tmp"

# Fetch the volume ID of the first available EBS volume with the specified tag
VOLUME_ID=$(aws ec2 describe-volumes --filters "Name=tag-key,Values=$VOLUME_TAG_KEY" --query "Volumes[0].VolumeId" --output text)

# Check if a volume ID was found
if [ "$VOLUME_ID" != "None" ]; then
    echo "Found EBS volume with ID: $VOLUME_ID"

    # Get instance ID
    TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
    INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)

    # Attach the EBS volume to this instance
    aws ec2 attach-volume --volume-id $VOLUME_ID --instance-id $INSTANCE_ID --device $DEVICE

    # Wait for the EBS volume to be attached
    while [ ! -e $DEVICE ]; do
        echo "Waiting for EBS volume to attach..."
        sleep 10
    done

    # Create a mount point
    mkdir -p $MOUNT_POINT

    # Check if the EBS volume already has a filesystem
    FS_TYPE=$(file -s $DEVICE | cut -d , -f 1 | awk '{print $2}')
    if [ "$FS_TYPE" == "data" ]; then
        # Format the EBS volume
        echo "No filesystem detected on $DEVICE. Formatting..."
        mkfs -t ext4 $DEVICE
    else
        echo "Filesystem already exists on $DEVICE"
    fi

    # Mount the EBS volume
    mount $DEVICE $MOUNT_POINT

    # Ensure it mounts on reboot
    # echo "$DEVICE $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab
else
    echo "No available EBS volume found with the specified tag"
fi
