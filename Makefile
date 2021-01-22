MONITOR:=honey-data-monitor.service
UPLOAD:=honey-data-upload.service

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_%/-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lab: ## Run an instance of Jupyter Lab
	poetry run jupyter lab

poetry: ## Install poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

python3: ## Make python3 the default
	sudo unlink /usr/bin/python
	sudo ln -s /usr/bin/python3 /usr/bin/python

restart-monitor: ## Restart monitor service
	sudo systemctl restart $(MONITOR)

restart-upload: ## Restart upload service
	sudo systemctl restart $(UPLOAD)

restart-all: restart-monitor restart-upload ## Restart all services

services: ## Install systemd services
	sudo cp infrastructure/systemd/*.service /etc/systemd/system/
	sudo systemctl start $(MONITOR)
	sudo systemctl start $(UPLOAD)
	sudo systemctl enable $(MONITOR)
	sudo systemctl enable $(UPLOAD)

tail-all: ## Tail all service logs
	journalctl -f -u $(MONITOR) -u $(UPLOAD)

venv: ## Create application virtual env
	poetry install --no-dev
