terraform {
  backend "remote" {
    organization = "parente"

    workspaces {
      name = "honey-infra"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.4"
    }
  }
}

variable "aws_region" {
  type        = string
  description = "Region for AWS resources"
  default     = "us-east-1"
}

variable "pgp_key" {
  type        = string
  description = "PGP public key to use to encrypt IAM creds"
  default     = "keybase:parente"
}

provider "aws" {
  version = "~> 3.4"
  region  = var.aws_region
}

locals {
  athena_results_path     = "athena-results"
  incoming_rotations_path = "incoming-rotations"
}

output "bot_user_arn" {
  value       = aws_iam_user.honey_data.arn
  description = "Data bot IAM user ARN"
}

output "access_key_id" {
  value       = aws_iam_access_key.honey_data.id
  description = "IAM key ID for the data bot"
}

output "secret_access_key" {
  value       = aws_iam_access_key.honey_data.encrypted_secret
  description = "PGP-encrypted IAM secret for the data bot"
  sensitive   = true
}