# honey.data

Data collection and aggregation infrastructure for the honey.fitness website.

## Setup

Create a Terraform Cloud workspace with `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` having admin
permissions in an AWS account. Run the following on the development machine.

```bash
cd infrastructure
terraform apply

terraform output access_key_id
terraform output secret_access_key | base64 --decode | keybase pgp decrypt
```

Now do all of the following on the Raspberry Pi device.

Add the following profile to `~/.aws/credentials`.

```ini
[honey-data-bot]
region=us-east-1
aws_access_key_id=<access_key_id from terraform>
aws_secret_access_key=<decrypted secret_access_key from terraform>
```

Point `python` to Python 3.x if it is not already. Clone this repo. Then run the following.

```bash
# Make python3 the default on older rpi devices
sudo unlink /usr/bin/python
sudo link -s /usr/bin/python3 /usr/bin/python

# Install poetry one time
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# Set up the application environment
cd honey.data
poetry install --no-dev
```
