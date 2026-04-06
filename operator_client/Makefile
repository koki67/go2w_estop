COMPOSE := ./docker/run.sh

.PHONY: build up down logs restart shell help

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

restart:
	$(COMPOSE) down
	$(COMPOSE) up

shell:
	$(COMPOSE) run --rm estop_operator bash

help:
	@grep -E '^[a-z_-]+:.*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; /^[a-z_-]+:.*## / {printf "  make %-12s %s\n", $$1, $$2}'
