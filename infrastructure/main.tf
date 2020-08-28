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
  athena_results_path = "athena-results"
  incoming_rotations_path = "incoming-rotations"
}