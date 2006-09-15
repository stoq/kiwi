docs:
	@make -s -C doc api howto

release: docs
	@bin/kiwi-i18n -c
	@rm -f MANIFEST
	@python setup.py -q sdist

.PHONY: docs
