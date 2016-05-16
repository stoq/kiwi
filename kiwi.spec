%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Name:           python-kiwi
Version:        1.10.2
Release:        1%{?dist}
Summary:        Framework for Python GUI applications
Group:          Development/Libraries
License:        LGPL
URL:            http://www.async.com.br/projects/kiwi/
Source0:        http://download.gnome.org/sources/kiwi/1.9/kiwi-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python-devel, pygtk2 >= 2.18, gettext
Requires:       pygtk2 >= 2.18


%description
Kiwi consists of a set of classes and wrappers for PyGTK that were 
developed to provide a sort of framework for applications. Fully 
object-oriented, and roughly Smalltalk's MVC, Kiwi provides a simple, 
practical way to build forms, windows and widgets that transparently 
access and display your object data.


%package docs
Group:          Documentation
Summary:        Documentation related to python-kiwi
Requires:       %{name} = %{version}-%{release}

%description docs
This package contains documentation that contains APIs and related materials,
useful for reference when writing software using Kiwi.


%prep
%setup -q -n kiwi-%{version}
sed -i -e 's|share/doc/kiwi|share/doc/%{name}-%{version}|' setup.py


%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
rm -rf $RPM_BUILD_ROOT%{_defaultdocdir}

%{find_lang} kiwi


%clean
rm -rf $RPM_BUILD_ROOT


%files -f kiwi.lang
%defattr(-,root,root,-)
%doc AUTHORS COPYING README NEWS
%{_bindir}/*
%{_libdir}/python*/site-packages/*.egg-info
%{_libdir}/glade3/*
%{_datadir}/glade3/*
%{_datadir}/kiwi
%{python_sitelib}/kiwi

%files docs
%defattr(-,root,root,-)
%doc COPYING doc/* examples


%changelog
* Tue Jul 14 2011 Johan Dahlin <jdahlin@async.com.br> 1.9.28-1
- upstream 1.9.28

* Tue Feb 04 2007 Johan Dahlin <jdahlin@async.com.br> 1.9.14-1
- Version 1.9.14
- Add .mo files

* Tue Feb 04 2007 Johan Dahlin <jdahlin@async.com.br> 1.9.13-1
- Upstream 1.9.13

* Sun Dec 17 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.11-1
- Upstream 1.9.11
- Do not manually provide python-abi
- Move docs into a subpackage
- Do a better job with gazpacho dir ownerships

* Sun Sep 03 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.9-1
- Version 1.9.9
- Do not ghost
- No more /etc/kiwi

* Wed Jul 12 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.8-1
- Fedora Extras rebuild.

* Fri Jul 07 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.8-0.4
- Build in slimmer build environments.

* Fri Jun 16 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.8-0.3
- Fix the incorrect gazpacho location on x86_64 (we are fully noarch)

* Fri May 19 2006 Konstantin Ryabitsev <icon@fedoraproject.org> - 1.9.8-0.2
- Initial packaging
