%{!?python:%define python python}
%{!?python_sitearch: %define python_sitearch %(%{python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Name:           %{python}-twisted-core
Version:        8.2.0
Release:        4%{?dist}
Summary:        Asynchronous networking framework written in Python
Group:          Development/Libraries
License:        MIT
URL:            http://twistedmatrix.com/trac/wiki/TwistedCore
Source0:        http://tmrc.mit.edu/mirror/twisted/Core/8.2/TwistedCore-%{version}.tar.bz2
# Available here:
# https://apestaart.org/thomas/trac/browser/pkg/fedora.extras/python-twisted-core/twisted-dropin-cache?format=raw
Source1:        twisted-dropin-cache

# rhbz:507610: Fix deprecation warnings (md5 and sha modules).
# Based on F-12 "changeset_r25457.patch" 1.3, which contains upstream r25457,
# but with a cleanup of the .orig and .rej versions of twisted/internet/_sslverify.py
Patch1:         python-twisted-core-8.2.0-fix-deprecation-warnings.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  %{python}-devel
BuildRequires:  %{python}-zope-interface >= 3.0.1
BuildRequires:  /bin/sed
BuildRequires:  /bin/awk

Requires:       %{python}-zope-interface
Requires:       pyOpenSSL

%description
An extensible framework for Python programming, with special focus
on event-based network programming and multiprotocol integration.

It is expected that one day the project will expanded to the point
that the framework will seamlessly integrate with mail, web, DNS,
netnews, IRC, RDBMSs, desktop environments, and your toaster.

Twisted Core is used by most of the servers, clients and protocols that are
part of other Twisted projects.

%package doc
Summary:        Documentation for Twisted Core
Group:          Documentation
Requires:       python-twisted-core = %{version}-%{release}

%description doc
Documentation for Twisted Core.

%package zsh
Summary:        Tab completion for Zsh and Twisted Core
Group:          System Environment/Shells
Requires:       python-twisted-core = %{version}-%{release}
Requires:       zsh

%description zsh
Tab completions for Zsh and Twisted Core.

%prep
%setup -q -n TwistedCore-%{version}
%patch1 -p1

# Turn off exec bits on docs to avoid spurious dependencies
find doc -type f | xargs chmod 644

# Fix line endings
sed -i -e 's,\r$,,' doc/howto/listings/udp/*

# Remove spurious shellbangs
sed -i -e '/^#! *\/usr\/bin\/python/d' \
    twisted/internet/glib2reactor.py
sed -i -e '/^#!\/bin\/python/d' \
    twisted/trial/test/scripttest.py

# Generate a brief README.zsh
awk '/^Zsh Notes:/,/^Have fun!/' twisted/python/zshcomp.py > README.zsh

# Fix encodings
for f in CREDITS LICENSE; do
    iconv -f iso-8859-1 -t utf-8 < ${f} > ${f}.utf8
    mv -f ${f}.utf8 ${f}
done

%build
CFLAGS="$RPM_OPT_FLAGS" %{python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# cfsupport is support for MacOSX Core Foundations, so we can delete it
rm -rf $RPM_BUILD_ROOT%{python_sitearch}/twisted/internet/cfsupport

# iocpreactor is a win32 reactor, so we can delete it
rm -rf $RPM_BUILD_ROOT%{python_sitearch}/twisted/internet/iocpreactor

# Man pages
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1/
cp -a doc/man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1/
rm -rf doc/man

# Zsh tab complete stub (à la teratorn)
mkdir -p $RPM_BUILD_ROOT%{_datadir}/zsh/site-functions/
sed -e 's#python -c#%{python} -c#g' twisted/python/_twisted_zsh_stub \
    > $RPM_BUILD_ROOT%{_datadir}/zsh/site-functions/_twisted_zsh_stub
rm -f $RPM_BUILD_ROOT%{python_sitearch}/twisted/python/_twisted_zsh_stub

# Some of the zsh completions are no longer appropriate
find $RPM_BUILD_ROOT%{python_sitearch}/twisted/python/zsh -size 0c -exec rm -f {} \;

# script to regenerate dropin.cache
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}
install -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_libexecdir}

# Create an empty dropin.cache to be %ghost-ed
touch $RPM_BUILD_ROOT%{python_sitearch}/twisted/plugins/dropin.cache

# C files don't need to be packaged
rm -f $RPM_BUILD_ROOT%{python_sitearch}/twisted/protocols/_c_urlarg.c
rm -f $RPM_BUILD_ROOT%{python_sitearch}/twisted/python/_epoll.c
rm -f $RPM_BUILD_ROOT%{python_sitearch}/twisted/test/raiser.c

# Fix permissions of shared objects
chmod 755 $RPM_BUILD_ROOT%{python_sitearch}/twisted/protocols/_c_urlarg.so
chmod 755 $RPM_BUILD_ROOT%{python_sitearch}/twisted/python/_epoll.so
chmod 755 $RPM_BUILD_ROOT%{python_sitearch}/twisted/test/raiser.so

# See if there's any egg-info
if [ -f $RPM_BUILD_ROOT%{python_sitearch}/Twisted*.egg-info ]; then
    echo $RPM_BUILD_ROOT%{python_sitearch}/Twisted*.egg-info |
        sed -e "s|^$RPM_BUILD_ROOT||"
fi > egg-info

%check
# trial twisted
# can't get this to work within the buildroot yet

%clean
rm -rf $RPM_BUILD_ROOT

%post
%{_libexecdir}/twisted-dropin-cache || :

%preun
if [ $1 -eq 0 ]; then
    # Complete removal, not upgrade, so remove plugins cache file
    %{__rm} -f %{python_sitearch}/twisted/plugins/dropin.cache || :
fi

%files -f egg-info
%defattr(-,root,root,-)
%doc CREDITS LICENSE NEWS README
%{_bindir}/manhole
%{_bindir}/mktap
%{_bindir}/pyhtmlizer
%{_bindir}/tap2deb
%{_bindir}/tap2rpm
%{_bindir}/tapconvert
%{_bindir}/trial
%{_bindir}/twistd
%{_libexecdir}/twisted-dropin-cache
%{_mandir}/man1/manhole.1*
%{_mandir}/man1/mktap.1*
%{_mandir}/man1/pyhtmlizer.1*
%{_mandir}/man1/tap2deb.1*
%{_mandir}/man1/tap2rpm.1*
%{_mandir}/man1/tapconvert.1*
%{_mandir}/man1/trial.1*
%{_mandir}/man1/twistd.1*
%dir %{python_sitearch}/twisted/
%{python_sitearch}/twisted/*.py*
%{python_sitearch}/twisted/application/
%{python_sitearch}/twisted/cred/
%{python_sitearch}/twisted/enterprise/
%{python_sitearch}/twisted/internet/
%{python_sitearch}/twisted/manhole/
%{python_sitearch}/twisted/persisted/
%dir %{python_sitearch}/twisted/plugins/
%{python_sitearch}/twisted/plugins/*.py*
%ghost %{python_sitearch}/twisted/plugins/dropin.cache
%{python_sitearch}/twisted/protocols/
%{python_sitearch}/twisted/python/
%{python_sitearch}/twisted/scripts/
%dir %{python_sitearch}/twisted/spread/
%{python_sitearch}/twisted/spread/*.py*
%dir %{python_sitearch}/twisted/spread/ui/
%{python_sitearch}/twisted/spread/ui/*.py*
%{python_sitearch}/twisted/spread/ui/*.glade
%{python_sitearch}/twisted/tap/
%{python_sitearch}/twisted/test/
%{python_sitearch}/twisted/trial/

%files doc
%defattr(-,root,root,-)
%doc doc/*

%files zsh
%defattr(-,root,root,-)
%doc README.zsh
%{_datadir}/zsh/site-functions/_twisted_zsh_stub

%changelog
* Tue Jun  8 2010 David Malcolm <dmalcolm@redhat.com> - 8.2.0-4
- fix deprecation warnings for md5 and sha modules (patch 1)
Resolves: rhbz#507610

* Tue Jan 26 2010 David Malcolm <dmalcolm@redhat.com> - 8.2.0-3.2
- fix source URL

* Mon Nov 30 2009 Dennis Gregorovic <dgregor@redhat.com> - 8.2.0-3.1
- Rebuilt for RHEL 6

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.2.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 8.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Dec 29 2008 Matthias Saou <http://freshrpms.net/> 8.2.0-1
- Update to 8.2.0.
- Change back spec cosmetic details from Paul's to Thomas' preference.

* Tue Dec 23 2008 Matthias Saou <http://freshrpms.net/> 8.1.0-2
- Re-introduce the python macro for parallel installable packages.
- Make sure the scriplet never returns a non-zero exit status.
- Remove dropin.cache file upon package removal.
- Merge back changes from Paul Howarth.

* Sun Nov 30 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 2.5.0-6
- Fix locations for Python 2.6

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 2.5.0-5
- Rebuild for Python 2.6

* Fri Mar 07 2008 Jesse Keating <jkeating@redhat.com> - 2.5.0-4
- Handle egg, drop pyver stuff, attempt to fix the multiple file listings

* Wed Feb 20 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.5.0-3
- Autorebuild for GCC 4.3

* Fri Aug 31 2007 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.5.0-2
- add sed and awk as buildrequires

* Thu Aug 23 2007 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.5.0-1
- updated to newest version
- remove twisted/spread/*.so
- added epoll.so

* Tue Dec 26 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-6
- new twisted-dropin-cache; does not complain loudly about plugins in
  the cache that are no longer installed

* Tue Nov 07 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-5
- incorporate suggestions by Paul Howarth:
- fix groups for doc and zsh
- don't package _twisted_zsh_stub from the python_sitearch dir
- generate README.zsh

* Wed Nov 01 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-4
- incorporate changes by Jeffrey C. Ollie:
- add doc and zsh subpackage
- remove executable bits from documentation files to avoid dependencies
- remove shebang from some files
- fix up end of line on some files
- remove .c files from being packaged

* Tue Sep 26 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-3
- no longer ghost .pyo files

* Fri Jun 09 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-2
- add twisted-dropin-cache script and use it
- ghost the dropin.cache file

* Wed Jun 07 2006 Thomas Vander Stichele <thomas at apestaart dot org>
- 2.4.0-1
- upstream release
- require pyOpenSSL as it is named in Extras

* Mon Oct 10 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.1.0-1
- upstream release

* Tue Aug 23 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.1-1
- upstream release

* Mon Apr 04 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0-2
- add zsh support

* Fri Mar 25 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0-1
- final release

* Thu Mar 17 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0-0.2.a3
- dropped web2

* Wed Mar 16 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0-0.1.a3
- upstream release

* Sat Mar 12 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0-0.1.a2
- new prerelease; FE versioning

* Mon Feb 07 2005 Jeff Pitman <symbiont+pyvault@berlios.de> 2.0.0a1-1
- prep for split

* Fri Aug 20 2004 Jeff Pitman <symbiont+pyvault@berlios.de> 1.3.0-1
- new version

* Mon Apr 19 2004 Jeff Pitman <symbiont+pyvault@berlios.de> 1.2.0-3
- vaultize

* Mon Apr 12 2004 Jeff Pitman <symbiont+pyvault@berlios.de> 1.2.0-2
- require pyOpenSSL, SOAPpy, openssh-clients, crypto, dia so trial can run

