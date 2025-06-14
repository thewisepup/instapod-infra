"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

stack = pulumi.get_stack()


# IMPORTANT: push docker image to this ECR repository first before creating the Lambda
podcast_generation__lambda_repository = aws.ecr.Repository(
    f"podcast-generator-lambda-{stack}",
    name=f"podcast-generator-lambda-{stack}",
    image_tag_mutability="MUTABLE",
)

# Create IAM role for Lambda
lambda_role = aws.iam.Role(
    f"podcast-generator-lambda-role-{stack}",
    assume_role_policy=aws.iam.get_policy_document(
        statements=[
            {
                "actions": ["sts:AssumeRole"],
                "principals": [
                    {
                        "type": "Service",
                        "identifiers": ["lambda.amazonaws.com"],
                    }
                ],
            }
        ]
    ).json,
)

# Attach AWSLambdaBasicExecutionRole to the role
lambda_role_policy_attachment = aws.iam.RolePolicyAttachment(
    f"podcast-generator-lambda-role-policy-{stack}",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

# Create the Lambda function using the ECR image
lambda_function = aws.lambda_.Function(
    f"podcast-generator-lambda-{stack}",
    package_type="Image",
    image_uri=podcast_generation__lambda_repository.repository_url.apply(
        lambda url: f"{url}:latest"
    ),
    role=lambda_role.arn,
    timeout=300,  # 5 minutes TODO update to 15 min
    memory_size=1024,  # 1GB TODO figure out new size
)


# Create an AWS resource (S3 Bucket)
bucket = aws.s3.BucketV2(f"my-bucket-{stack}")

# Export the name of the bucket
pulumi.export(f"my-bucket-{stack}", bucket.id)
