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
    authorization_type="AWS_IAM",
    cors={
        "allow_origins": (
            ["https://instapod.app"]
            if stack == "prod"
            else [
                "https://instapod.app",
                "http://localhost:3000",
                "http://localhost:8000",
                "https://*.vercel.app",
            ]
        ),
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["*"],
        "max_age": 86400,
    },
)

# Create an IAM policy for the Next.js app to invoke the Lambda function URL
nextjs_lambda_policy = aws.iam.Policy(
    f"nextjs-lambda-policy-{stack}",
    policy=aws.iam.get_policy_document(
        statements=[
            {
                "actions": ["lambda:InvokeFunctionUrl"],
                "resources": [podcast_generation_lambda.arn],
            }
        ]
    ).json,
)

# Create IAM user for Next.js application
nextjs_user = aws.iam.User(
    f"nextjs-app-user-{stack}",
    name=f"nextjs-app-user-{stack}",
)

# Attach the Lambda policy to the Next.js user
nextjs_user_policy_attachment = aws.iam.UserPolicyAttachment(
    f"nextjs-user-policy-attachment-{stack}",
    user=nextjs_user.name,
    policy_arn=nextjs_lambda_policy.arn,
)

# Create access key for the Next.js user
nextjs_user_access_key = aws.iam.AccessKey(
    f"nextjs-user-access-key-{stack}",
    user=nextjs_user.name,
)

# Export all resources
pulumi.export(
    "podcast_generation_lambda_repository",
    podcast_generation_lambda_repository.repository_url,
)
pulumi.export("lambda_role", lambda_role.arn)
pulumi.export("podcast_generation_lambda", podcast_generation_lambda.arn)
pulumi.export("function_url", podcast_generation_lambda_function_url.function_url)
pulumi.export("nextjs_lambda_policy_arn", nextjs_lambda_policy.arn)
pulumi.export("nextjs_user_arn", nextjs_user.arn)
pulumi.export("nextjs_access_key_id", nextjs_user_access_key.id)
pulumi.export("nextjs_secret_access_key", nextjs_user_access_key.secret)
