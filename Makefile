WEBDIR=/mondo/htdocs/async/projects/kiwi

docs:
	@make -s -C doc api howto

release: docs
	@bin/kiwi-i18n -c
	@rm -f MANIFEST
	@python setup.py -q sdist
	@python setup.py -q bdist_wininst

web: docs
	@rm -fr ${WEBDIR}/api
	@cp -r doc/api ${WEBDIR}
	@rm -fr ${WEBDIR}/howto
	@cp -r doc/howto ${WEBDIR}
	@cd ${WEBDIR} && tar cfz howto.tar.gz howto
	@cd ${WEBDIR} && tar cfz api.tar.gz api
	@echo Website updated

.PHONY: docs
