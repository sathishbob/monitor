Name:           las-agent
Version:        1.0.0
Release:        1%{?dist}
Summary:        Lab Server Monitoring AI Agent
License:        Proprietary
Group:          Applications/System
URL:            https://github.com/your-repo/monitor
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3 >= 3.8
Requires:       python3 >= 3.8 python3-pip curl systemd
Recommends:     elasticsearch

%description
Comprehensive monitoring and AI analytics for lab server environments.
Features:
 - Real-time performance monitoring
 - User activity tracking
 - Command execution monitoring
 - AI-powered anomaly detection
 - Engagement scoring
 - Inactivity alerts
 - Cross-server comparison

%prep
%setup -q

%build
# No build required for Python application

%install
mkdir -p %{buildroot}/opt/las-agent
mkdir -p %{buildroot}/var/log/las-agent
mkdir -p %{buildroot}%{_sysconfdir}/systemd/system
mkdir -p %{buildroot}%{_sharedstatedir}/las-agent

# Copy application files
cp -r agent %{buildroot}/opt/las-agent/
cp monitor_agent.py %{buildroot}/opt/las-agent/
cp requirements.txt %{buildroot}/opt/las-agent/
cp config.json %{buildroot}/opt/las-agent/config.json.example

# Copy systemd service
cp setup/las-agent.service %{buildroot}%{_sysconfdir}/systemd/system/las-agent.service

# Create directories
mkdir -p %{buildroot}/opt/las-agent/setup
mkdir -p %{buildroot}/opt/las-agent/docs

# Copy setup scripts
cp setup/run_service.sh %{buildroot}/opt/las-agent/setup/
chmod +x %{buildroot}/opt/las-agent/setup/run_service.sh

%pre
# Create user if it doesn't exist
if ! id las-agent >/dev/null 2>&1; then
    useradd -r -s /bin/false -d /opt/las-agent las-agent
    echo "Created las-agent user"
fi

%post
# Setup Python virtual environment
cd /opt/las-agent
if [ ! -d venv ]; then
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt >/dev/null 2>&1
    deactivate
fi

# Setup configuration if it doesn't exist
if [ ! -f config.json ]; then
    cp config.json.example config.json
fi

# Setup systemd service
systemctl daemon-reload
systemctl enable las-agent >/dev/null 2>&1 || true

echo "las-agent installed successfully"
echo "To start the service: systemctl start las-agent"
echo "To check status: systemctl status las-agent"

%preun
# Stop and disable service before removal
if systemctl is-active --quiet las-agent; then
    systemctl stop las-agent
fi

if systemctl is-enabled --quiet las-agent 2>/dev/null; then
    systemctl disable las-agent
fi

systemctl daemon-reload

%postun
# Clean up user if it exists (optional)
# userdel monitor >/dev/null 2>&1 || true

%files
%defattr(-,las-agent,las-agent,-)
/opt/las-agent
/var/log/las-agent
%config(noreplace) %{_sysconfdir}/systemd/system/las-agent.service

%changelog
* Tue Jan 01 2025 Lab Server Monitoring Team <support@example.com> - 1.0.0-1
- Initial RPM package release

