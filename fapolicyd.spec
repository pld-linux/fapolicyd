# TODO: handle "fapolicyd" user, systemd service etc. (see upstream fapolicyd.spec)
#
# Conditional build:
%bcond_without	audit	# decision auditing support
%bcond_without	rpm	# RPM database as a trust source

Summary:	Application allow listing daemon
Summary(pl.UTF-8):	Demon do obsługi listy dozwolonych aplikacji
Name:		fapolicyd
Version:	1.3.3
Release:	0.1
License:	GPL v2+
Group:		Daemons
Source0:	https://people.redhat.com/sgrubb/fapolicyd/%{name}-%{version}.tar.gz
# Source0-md5:	072f3e281662838f608b3da6e1061a9e
Patch0:		%{name}-ldso.patch
URL:		https://people.redhat.com/sgrubb/fapolicyd/
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
Requires:	uname(release) >= 4.20
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

%prep
%setup -q
%patch -P0 -p1

%build
%{__libtoolize}
%{__aclocal} -I m4
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	%{?with_audit:--with-audit} \
	%{!?with_rpm:--without-rpm}
%{__make}

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT \
	completiondir=%{bash_compdir} \
	systemdservicedir=%{systemdunitdir}

%{__mv} $RPM_BUILD_ROOT%{bash_compdir}/fapolicyd{.bash_completion,}

# no API exported
%{__rm} $RPM_BUILD_ROOT%{_libdir}/libfapolicyd.{a,la}

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog README.md TODO
%attr(755,root,root) %{_sbindir}/fagenrules
%attr(755,root,root) %{_sbindir}/fapolicyd
%attr(755,root,root) %{_sbindir}/fapolicyd-cli
%dir %{_sysconfdir}/fapolicyd
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd.trust
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/fapolicyd/fapolicyd-filter.conf
%{_datadir}/fapolicyd
%{systemdunitdir}/fapolicyd.service
%{bash_compdir}/fapolicyd
%{_mandir}/man5/fapolicyd.conf.5*
%{_mandir}/man5/fapolicyd.rules.5*
%{_mandir}/man5/fapolicyd.trust.5*
%{_mandir}/man5/fapolicyd-filter.conf.5*
%{_mandir}/man5/rpm-filter.conf.5*
%{_mandir}/man8/fagenrules.8*
%{_mandir}/man8/fapolicyd.8*
%{_mandir}/man8/fapolicyd-cli.8*
