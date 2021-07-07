
all: clean install

install:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
	poetry install

clean: ## Clean out the .pyc files
	find . -name "*.pyc" -delete

env:
	scp TEMPLATE.env .env

config:
	scp configs/TEMPLATE.yaml configs/$(PROJECT_NAME).yaml

format:
	black *.py app

lint: format
	flake8

dependency-tree:
	poetry show --tree
