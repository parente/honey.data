# honey.data

Data collection and aggregation infrastructure for the
[honey.fitness](https://github.com/parente/honey.fitness) website.

## Setup

Create a Terraform Cloud workspace with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` having admin
permissions in an AWS account. Clone this repository on the development machine. The run the
following.

```bash
cd honey.data/infrastructure
# Provision AWS infrastructure
terraform apply
# Retrieve AWS access key and secret. Adjust pbcopy if not on macOS
terraform output access_key_id | pbcopy
terraform output secret_access_key | base64 --decode | keybase pgp decrypt | pbcopy
```

Switch to working on the Raspberry Pi device for the remaining steps. Add the following profile to
`~/.aws/credentials`.

```ini
[honey-data-bot]
region=us-east-1
aws_access_key_id=<access_key_id from terraform>
aws_secret_access_key=<decrypted secret_access_key from terraform>
```

Clone this repository as `/home/pi/honey.data`. Then run the following.

```bash
cd honey.data

# One time: Make python3 the default on older rpi devices
make python3
# One time: Install poetry
make poetry
# When deps change: Set up the application environment
make venv
# When service configs change: Set up systemd services
make services
```
