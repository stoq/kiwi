VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
PACKAGE=kiwi
DEBPACKAGE=python-kiwi
WEBDIR=/mondo/htdocs/async.com.br/www/projects/kiwi
TARBALL_DIR=/mondo/htdocs/stoq.com.br/download/sources
TARBALL=kiwi-$(VERSION).tar.gz

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

bdist:
	python setup.py -q bdist_wininst

upload-release:
	scp dist/$(TARBALL) johan@master.gnome.org:
	ssh johan@master.gnome.org ftpadmin install $(TARBALL)
	scp dist/kiwi-$(VERSION).win32.exe johan@master.gnome.org:/ftp/pub/GNOME/binaries/win32/kiwi/

include async.mk

.PHONY: bdist upload-release
