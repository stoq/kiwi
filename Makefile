WEBDIR=/mondo/htdocs/async/projects/kiwi
VERSION=$(shell python -c "execfile('kiwi/__version__.py'); print '.'.join(map(str, version))")
BUILDDIR=tmp
TARBALL=kiwi-$(VERSION).tar.gz

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
	cp -r doc/api ${WEBDIR}
	cp -r doc/howto ${WEBDIR}
	cd ${WEBDIR} && tar cfz howto.tar.gz howto
	cd ${WEBDIR} && tar cfz api.tar.gz api

sdist: docs
	bin/kiwi-i18n -c
	python setup.py -q sdist

bdist:
	python setup.py -q bdist_wininst

deb: sdist
	rm -fr $(BUILDDIR)
	mkdir $(BUILDDIR)
	cd $(BUILDDIR) && tar xfz ../dist/$(TARBALL)
	cd $(BUILDDIR)/kiwi-$(VERSION) && debuild
	rm -fr $(BUILDDIR)/kiwi-$(VERSION)
	mv $(BUILDDIR)/* dist
	rm -fr $(BUILDDIR)

release: clean sdist bdist deb

upload: release
	scp dist/$(TARBALL) gnome.org:
	ssh gnome.org install-module $(TARBALL)
	scp dist/kiwi-$(VERSION).win32.exe gnome.org:/ftp/pub/GNOME/binaries/win32/kiwi/

.PHONY: docs web sdist bdist release deb
