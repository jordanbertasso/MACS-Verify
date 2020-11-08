.PHONY: run
run:
	cd discord-verify ; env PYTHONIOENCODING=UTF-8 PYTHONUNBUFFERED=1 \
	AWS_CONFIG_FILE=./aws/config \
	AWS_SHARED_CREDENTIALS_FILE=./aws/credentials \
	DB_HOST=localhost \
	python src/bot.py

.PHONY: run-drop-db
run-drop-db:
	env DROP_DATABASE=1 $(MAKE) run

.PHONY: docker-build
docker-build:
	docker-compose build

.PHONY: docker-run
docker-run:
	mkdir -p db ; docker-compose up -d && docker-compose logs -f bot

.PHONY: docker-run-drop-db
docker-run-drop-db:
	env DROP_DATABASE=1 $(MAKE) docker-run

.PHONY: docker-stop
docker-stop:
	docker-compose down