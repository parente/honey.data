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

output "bot_user" {
  value       = aws_iam_user.honey_data
  description = "Data bot IAM user"
}

output "access_key" {
  value       = aws_iam_access_key.honey_data
  description = "PGP-encrypted IAM key and secret for the data bot"
  sensitive   = true
}
