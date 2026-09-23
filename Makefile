PY := python3

.PHONY: all build defence clean site

all: build defence

build:
	$(PY) src/run_01_build.py

defence:
	$(PY) src/run_02_defence.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install markdown`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*
