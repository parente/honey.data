help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_%/-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


poetry: ## Install poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

python3: ## Make python3 the default
	sudo unlink /usr/bin/python
	sudo link -s /usr/bin/python3 /usr/bin/python

restart-monitor: ## Restart monitor service
	sudo systemctl restart honey-data-monitor

restart-upload: ## Restart upload service
	sudo systemctl restart honey-data-upload

restart-all: restart-monitor restart-upload ## Restart all services

services: ## Install systemd services
	sudo cp infrastructure/systemd/*.service /etc/systemd/system/
	sudo systemctl start honey-data-monitor.service
	sudo systemctl start honey-data-upload.service
	sudo systemctl enable honey-data-monitor.service
	sudo systemctl enable honey-data-upload.service

venv: ## Create application virtual env
	poetry install --no-dev
