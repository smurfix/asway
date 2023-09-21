.PHONY: test format lint all clean publish docs coverage docker-test
.DEFAULT_GOAL := all

source_dirs = asway test examples

lint:
	flake8 $(source_dirs)

format:
	yapf -rip $(source_dirs)

test:
	./run-tests.py

docker-test:
	docker build -t asway-test .
	docker run -it asway-test

clean:
	rm -rf dist asway.egg-info build docs/_build
	rm -rf `find -type d -name __pycache__`

publish:
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

docs:
	sphinx-build docs docs/_build/html

livedocs:
	sphinx-autobuild docs docs/_build/html --watch asway --ignore '*swp' --ignore '*~'

all: format lint docker-test
