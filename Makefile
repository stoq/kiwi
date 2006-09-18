WEBDIR=/mondo/htdocs/async/projects/kiwi
VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
BUILDDIR=tmp

clean-docs:
	rm -fr doc/api
	rm -fr doc/howto

clean: clean-docs
	debclean
	rm -fr $(BUILDDIR)
	rm -f MANIFEST

docs:
	make -s -C doc api howto

web: clean-docs docs
	rm -fr ${WEBDIR}/api
	cp -r doc/api ${WEBDIR}
	rm -fr ${WEBDIR}/howto
	cp -r doc/howto ${WEBDIR}
	cd ${WEBDIR} && tar cfz howto.tar.gz howto
	cd ${WEBDIR} && tar cfz api.tar.gz api
	echo Website updated

sdist: docs
	bin/kiwi-i18n -c
	python setup.py -q sdist

bdist:
	python setup.py -q bdist_wininst

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/kiwi-$(VERSION).tar.gz
	cd $(BUILDDIR)/kiwi-$(VERSION) && debuild
	rm -fr $(BUILDDIR)/kiwi-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

release: clean sdist bdist deb

.PHONY: docs web sdist bdist release deb
