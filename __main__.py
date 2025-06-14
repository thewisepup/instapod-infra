"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

stack = pulumi.get_stack()


# IMPORTANT: push docker image to this ECR repository first before creating the Lambda
podcast_generation_lambda_repository = aws.ecr.Repository(
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
podcast_generation_lambda = aws.lambda_.Function(
    f"podcast-generator-lambda-{stack}",
    package_type="Image",
    image_uri=podcast_generation_lambda_repository.repository_url.apply(
        lambda url: f"{url}:latest"
    ),
    role=lambda_role.arn,
    timeout=900,
    memory_size=600,
    architectures=["arm64"],
)

# Create a function URL for the Lambda
podcast_generation_lambda_function_url = aws.lambda_.FunctionUrl(
    f"podcast-generator-lambda-url-{stack}",
    function_name=podcast_generation_lambda.name,
    authorization_type="NONE",
    cors={
        "allow_origins": ["*"],
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "max_age": 86400,
    },
)

# Export all resources
pulumi.export(
    "podcast_generation_lambda_repository",
    podcast_generation_lambda_repository.repository_url,
)
pulumi.export("lambda_role", lambda_role.arn)
pulumi.export("podcast_generation_lambda", podcast_generation_lambda.arn)
pulumi.export("function_url", podcast_generation_lambda_function_url.function_url)
