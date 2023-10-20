update-deps:
	pre-commit autoupdate
	python -m pip install --upgrade pip-tools pip wheel
	python -m piptools compile --upgrade --resolver backtracking -o requirements.txt --strip-extras pyproject.toml
	python -m piptools compile --extra dev --upgrade --resolver backtracking -o dev-requirements.txt --strip-extras pyproject.toml


init:
	rm -rf .tox
	python -m pip install --upgrade pip wheel
	python -m pip install --upgrade -r requirements.txt -r dev-requirements.txt -e .
	python -m pip check


dist:
	./mkdist.py

update: update-deps init

.PHONY: update-deps init update dist
