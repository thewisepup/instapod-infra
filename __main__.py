"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3

stack = pulumi.get_stack()

# Create an AWS resource (S3 Bucket)
bucket = s3.BucketV2(f"my-bucket-{stack}")

# Export the name of the bucket
pulumi.export(f"my-bucket-{stack}", bucket.id)
