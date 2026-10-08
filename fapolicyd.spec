# Conditional build:
%bcond_without	audit	# decision auditing support
%bcond_without	rpm	# RPM database as a trust source
%bcond_without	tests	# unit tests
%bcond_with	selinux	# SELinux policy module (needs selinux-policy-devel)

Summary:	Application allow listing daemon
Summary(pl.UTF-8):	Demon do obsługi listy dozwolonych aplikacji
Name:		fapolicyd
Version:	2.0.1
Release:	1
License:	GPL v3+
Group:		Daemons
#Source0Download: https://github.com/linux-application-whitelisting/fapolicyd/releases
Source0:	https://github.com/linux-application-whitelisting/fapolicyd/releases/download/v%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	d063b6db132bcefee2814cf46545c826
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	https://github.com/linux-application-whitelisting/fapolicyd-selinux/archive/v1.2/%{name}-selinux-1.2.tar.gz
# Source3-md5:	cb7f9e705e03a14408812a101d6aef30
Patch0:		%{name}-ldso.patch
Patch1:		%{name}-poldek.patch
URL:		https://github.com/linux-application-whitelisting/fapolicyd
BuildRequires:	autoconf >= 2.60
BuildRequires:	automake
BuildRequires:	file
BuildRequires:	libcap-ng-devel
BuildRequires:	libmagic-devel
BuildRequires:	libseccomp-devel
BuildRequires:	libtool >= 2:2
BuildRequires:	linux-libc-headers >= 7:4.20
BuildRequires:	lmdb-devel
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
%{?with_rpm:BuildRequires:	rpm-devel}
BuildRequires:	rpmbuild(macros) >= 1.673
BuildRequires:	udev-devel
BuildRequires:	uthash-devel
Requires(post,preun,postun):	systemd-units >= 38
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
# magic.mgc is only in file; fapolicyd-magic.mgc is compiled by the build-time file and older libmagic cannot read it
Requires:	file >= 5.48
Requires:	rc-scripts
Requires:	systemd-units >= 38
Requires:	uname(release) >= 4.20
Provides:	group(fapolicyd)
Provides:	user(fapolicyd)
%{?with_selinux:BuildRequires:	selinux-policy-devel}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Fapolicyd (File Access Policy Daemon) implements application allow
listing to decide file access rights. Applications that are known via
a reputation source are allowed access while unknown applications are
not. The daemon makes use of the kernel's fanotify interface to
determine file access rights.

%description -l pl.UTF-8
Fapolicyd (File Access Policy Daemon - demon polityki dostępu do
plików) implementuje obsługę listy dozwolonych aplikacji, decydującą o
prawach dostępu do plików. Aplikacje znane przez źródło reputacji mają
dostęp dozwolony, natomiast nieznane aplikacje nie. Demon wykorzystuje
interfejs jądra fanotify do określania praw dostępu do plików.

%if %{with selinux}
%package selinux
Summary:	SELinux policy module for fapolicyd
Summary(pl.UTF-8):	Moduł polityki SELinux dla fapolicyd
Group:		Base
Requires(post,postun):	/usr/sbin/semodule
Requires:	%{name} = %{version}-%{release}
Requires:	selinux-policy
BuildArch:	noarch

%description selinux
SELinux policy module for fapolicyd. It is optional - fapolicyd works
without it.

%description selinux -l pl.UTF-8
Moduł polityki SELinux dla fapolicyd. Jest opcjonalny - fapolicyd
działa bez niego.
%endif

%prep
%setup -q %{?with_selinux:-a3}
%patch -P0 -p1
%patch -P1 -p1

%build
%{__libtoolize}
%{__aclocal} -I m4
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	%{?with_audit:--with-audit} \
	%{!?with_rpm:--without-rpm} \
	--disable-shared

# rules must name the same dynamic linker the daemon was configured with
ld_so=$(%{__sed} -n 's/^#define SYSTEM_LD_SO "\(.*\)"$/\1/p' config.h)
test -n "$ld_so"
%{__sed} -i -e "s|%%ld_so_path%%|$ld_so|" rules.d/*.rules

%{__make}

%if %{with tests}
%{__make} check
%endif

%if %{with selinux}
%{__make} -C %{name}-selinux-1.2
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/log,/etc/{rc.d/init.d,sysconfig},%{systemdtmpfilesdir},/var/lib/fapolicyd,%{_sysconfdir}/fapolicyd/{rules.d,trust.d}}

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT \
	completiondir=%{bash_compdir} \
	systemdservicedir=%{systemdunitdir}

%{__mv} $RPM_BUILD_ROOT%{bash_compdir}/fapolicyd{.bash_completion,}

install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/fapolicyd
cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/fapolicyd
cp -p init/fapolicyd-tmpfiles.conf $RPM_BUILD_ROOT%{systemdtmpfilesdir}/fapolicyd.conf

# default policy: the "known-libs" set from README-rules
for f in 10-languages 20-dracut 21-updaters 30-patterns 40-bad-elf 41-shared-obj \
		42-trusted-elf 70-trusted-lang 72-shell 90-deny-execute 95-allow-open; do
	cp -p $RPM_BUILD_ROOT%{_datadir}/fapolicyd/sample-rules/$f.rules \
		$RPM_BUILD_ROOT%{_sysconfdir}/fapolicyd/rules.d
done

touch $RPM_BUILD_ROOT%{_sysconfdir}/fapolicyd/compiled.rules \
	$RPM_BUILD_ROOT/var/log/fapolicyd-access.log

%if %{with selinux}
install -D -p %{name}-selinux-1.2/%{name}.pp.bz2 $RPM_BUILD_ROOT%{_datadir}/selinux/packages/targeted/%{name}.pp.bz2
install -D -p -m644 %{name}-selinux-1.2/%{name}.if $RPM_BUILD_ROOT%{_datadir}/selinux/devel/include/contrib/ipp-%{name}.if
%endif

# no API exported
%{__rm} $RPM_BUILD_ROOT%{_libdir}/libfapolicyd.{a,la}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 367 fapolicyd
%useradd -u 367 -d /var/lib/fapolicyd -s /bin/false -c "File Access Policy Daemon" -g fapolicyd fapolicyd

%post
/sbin/chkconfig --add fapolicyd
%service fapolicyd restart "File Access Policy Daemon"
%systemd_post fapolicyd.service

%preun
if [ "$1" = "0" ]; then
	%service -q fapolicyd stop
	/sbin/chkconfig --del fapolicyd
fi
%systemd_preun fapolicyd.service

%postun
%systemd_reload
if [ "$1" = "0" ]; then
	%userremove fapolicyd
	%groupremove fapolicyd
fi

%if %{with selinux}
%post selinux
/usr/sbin/semodule -n -i %{_datadir}/selinux/packages/targeted/%{name}.pp.bz2

%postun selinux
if [ "$1" = "0" ]; then
	/usr/sbin/semodule -n -r %{name}
fi

%files selinux
%defattr(644,root,root,755)
%{_datadir}/selinux/packages/targeted/%{name}.pp.bz2
%{_datadir}/selinux/devel/include/contrib/ipp-%{name}.if
%endif

%files
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog NEWS README.md TODO doc/systemd-watchdog.md
%attr(755,root,root) %{_sbindir}/fagenrules
%attr(755,root,root) %{_sbindir}/fapolicyd
%attr(755,root,root) %{_sbindir}/fapolicyd-cli
%if %{with rpm}
%attr(755,root,root) %{_libexecdir}/fapolicyd-rpm-loader
%endif
%attr(750,root,fapolicyd) %dir %{_sysconfdir}/fapolicyd
%attr(750,root,fapolicyd) %dir %{_sysconfdir}/fapolicyd/rules.d
%attr(750,root,fapolicyd) %dir %{_sysconfdir}/fapolicyd/trust.d
%attr(640,root,fapolicyd) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd.conf
%attr(640,root,fapolicyd) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd.trust
%attr(640,root,fapolicyd) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd-filter.conf
%attr(640,root,fapolicyd) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/rules.d/*.rules
%ghost %attr(640,root,fapolicyd) %{_sysconfdir}/fapolicyd/compiled.rules
%attr(754,root,root) /etc/rc.d/init.d/fapolicyd
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/fapolicyd
%{systemdunitdir}/fapolicyd.service
%{systemdtmpfilesdir}/fapolicyd.conf
%{bash_compdir}/fapolicyd
%{_datadir}/fapolicyd
%attr(770,root,fapolicyd) %dir /var/lib/fapolicyd
%ghost %attr(440,fapolicyd,fapolicyd) %{_localstatedir}/log/fapolicyd-access.log
%{_mandir}/man5/fapolicyd.conf.5*
%{_mandir}/man5/fapolicyd.metrics.5*
%{_mandir}/man5/fapolicyd.rules.5*
%{_mandir}/man5/fapolicyd.state.5*
%{_mandir}/man5/fapolicyd.timing.5*
%{_mandir}/man5/fapolicyd.trust.5*
%{_mandir}/man5/fapolicyd-filter.conf.5*
%{_mandir}/man5/rpm-filter.conf.5*
%{_mandir}/man8/fagenrules.8*
%{_mandir}/man8/fapolicyd.8*
%{_mandir}/man8/fapolicyd-cli.8*
