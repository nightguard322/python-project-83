PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app
install:
	uv sync
dev:
	uv run flask --debug --app page_analyzer:app run
lint:
	uv run ruff check .
build:
	./build.sh
render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app