"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

stack = pulumi.get_stack()


podcast_generation_image = aws.ecr.Repository(
    f"podcast-generator-lambda-{stack}",
    name=f"podcast-generator-lambda-{stack}",
    image_tag_mutability="MUTABLE",
)
# Create an AWS resource (S3 Bucket)
bucket = aws.s3.BucketV2(f"my-bucket-{stack}")

# Export the name of the bucket
pulumi.export(f"my-bucket-{stack}", bucket.id)
