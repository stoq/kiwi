PACKAGE=kiwi
TEST_PACKAGES=$(PACKAGE) tests
WEBDIR=/mondo/htdocs/async.com.br/www/projects/kiwi
# FIXME: This probably should be on utils.mk
TESTS_RUNNER=python3 -m nose --nocapture --nologcapture --verbose --detailed-errors

all:
	python setup.py build_ext -i

clean-docs:
	rm -fr doc/api
	rm -fr doc/howto

clean:
	rm -fr build
	rm -f MANIFEST

docs:
	make -s -C doc api howto

apidocs:
	make -C docs/api pickle html devhelp

upload-apidocs:
	scp -r docs/api/_build/html anthem:/var/www/stoq.com.br/doc/api/kiwi

web: clean-docs docs
	cp -r doc/api ${WEBDIR}
	cp -r doc/howto ${WEBDIR}
	cp -r doc/howto.ps ${WEBDIR}
	gzip ${WEBDIR}/howto.ps
	cd ${WEBDIR} && tar cfz howto.tar.gz howto
	cd ${WEBDIR} && tar cfz api.tar.gz api

check: check-source-all
	@rm -f .noseids
	$(TESTS_RUNNER) --failed $(TEST_PACKAGES)

check-failed:
	$(TESTS_RUNNER) --failed $(TEST_PACKAGES)

coverage: check-source-all
	$(TESTS_RUNNER) --with-coverage --with-xunit \
	                --cover-package=$(PACKAGE) --cover-erase $(TEST_PACKAGES)

include utils/utils.mk
.PHONY: all clean-docs clean docs apidocs upload-apidocs web check
