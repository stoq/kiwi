docs:
	@make -s -C doc api howto

release: docs
	@python setup.py -q sdist

.PHONY: docs
