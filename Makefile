build:
	python3 -m build

test_build: clean
	pip uninstall spyctl -y
	pip install .

release:
	python3 -m twine upload dist/*

release_to_test_pypi:
	python3 -m twine upload --repository testpypi dist/*

install_from_test:
	pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple spyctl

venv:
	python3.12 -m venv ./spyctl_venv --clear

clean:
	rm -rf ./dist
	rm -rf ./spyctl.egg-info
	rm -rf ./build

.PHONY: rebuild
rebuild:
	$(MAKE) clean
	$(MAKE) build

view_coverage_wsl:
	coverage html
	explorer.exe "htmlcov\index.html" ||:

test-coverage:
	coverage run --omit="test_*.py" -m pytest

test-coverage-report: test-coverage
	coverage report -m

test-coverage-html: test-coverage
	coverage html

test-coverage-xml:
	pytest --cov=src --cov-report=xml

format:
	./ruff-format.sh

pre-commit-init:
	pre-commit install

pre-commit-update:
	pre-commit autoupdate