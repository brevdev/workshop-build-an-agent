# Getting WiFi Access

## Purpose

This article provides instructions for connecting to the company's wireless networks, including initial setup, troubleshooting common connection issues, and understanding different network types available for various user categories and device types.

## Available WiFi Networks

The company provides several wireless networks to accommodate different security requirements and user types:

### **Corporate Networks**

#### **COMPANY-SECURE** (Primary Network)
- **Purpose:** Standard corporate network for company-managed devices
- **Security:** WPA3-Enterprise with certificate-based authentication
- **Access:** Full access to internal resources and internet
- **Speed:** Up to 1 Gbps
- **Coverage:** All office locations and conference rooms

#### **COMPANY-BYOD** (Bring Your Own Device)
- **Purpose:** Personal devices of authorized employees
- **Security:** WPA3-Enterprise with username/password authentication
- **Access:** Limited internal resources, full internet access
- **Speed:** Up to 500 Mbps
- **Coverage:** Common areas, conference rooms, and work spaces

### **Guest Networks**

#### **COMPANY-GUEST** (Visitor Access)
- **Purpose:** Temporary access for visitors and contractors
- **Security:** WPA2-PSK with daily rotating password
- **Access:** Internet only, no internal network access
- **Speed:** Up to 100 Mbps
- **Duration:** 24-hour access periods

#### **COMPANY-CONFERENCE** (Event Access)
- **Purpose:** Large meetings, conferences, and training sessions
- **Security:** WPA2-PSK with event-specific password
- **Access:** Internet only, bandwidth-managed per user
- **Speed:** Shared bandwidth based on attendee count
- **Duration:** Event-specific activation periods

## Prerequisites

Before connecting to company WiFi, ensure you have:

- **Active company network account** (for corporate networks)
- **Device compliance** with company security policies
- **Updated operating system** and security patches
- **Company certificate** installed (for COMPANY-SECURE network)
- **Multi-Factor Authentication (MFA)** enabled on your account

### **Device Requirements**
- **Operating System:** Windows 10/11, macOS 10.15+, iOS 13+, Android 9+, or Linux (Ubuntu 18.04+)
- **WiFi Standards:** 802.11n (2.4GHz/5GHz) or newer required
- **Security Support:** WPA2/WPA3 capability required
- **Certificate Support:** Device must support enterprise certificates

## Connection Procedures

### **Connecting to COMPANY-SECURE (Managed Devices)**

#### **Windows 10/11**
1. **Open WiFi Settings**
   - Click the **WiFi icon** in the system tray
   - Select **COMPANY-SECURE** from available networks
   - Click **Connect**

2. **Authentication**
   - **Username:** Your company username (without domain)
   - **Password:** Your standard company password
   - **Certificate:** Select **Company Root CA** if prompted
   - Click **OK** to connect

3. **Automatic Configuration**
   - Group Policy will automatically configure advanced settings
   - Connection profile will be saved for future use
   - Certificate renewal handled automatically

#### **macOS**
1. **Open WiFi Menu**
   - Click the **WiFi icon** in the menu bar
   - Select **COMPANY-SECURE** from the list
   - Click **Join**

2. **Authentication Dialog**
   - **Username:** Enter your company username
   - **Password:** Enter your company password
   - **Certificate:** Verify **Company Root CA** is selected
   - Click **Join**

3. **Trust Certificate** (First-time setup)
   - Click **Continue** when prompted about certificate trust
   - Enter your **local admin password** to install certificate
   - Connection will complete automatically

#### **Mobile Devices (iOS/Android)**

##### **iOS Setup**
1. **Install Configuration Profile**
   - Open **Safari** and navigate to `wifi.company.com/ios`
   - Download and install the **Company WiFi Profile**
   - Enter device **passcode** when prompted
   - Tap **Install** to complete setup

2. **Connect to Network**
   - Go to **Settings → WiFi**
   - Select **COMPANY-SECURE**
   - Enter your **company credentials** when prompted

##### **Android Setup**
1. **Manual Configuration**
   - Go to **Settings → WiFi**
   - Tap **COMPANY-SECURE**
   - Configure the following settings:
     - **EAP Method:** PEAP
     - **Phase 2 Authentication:** MSCHAPv2
     - **CA Certificate:** Company Root CA
     - **Username:** Your company username
     - **Password:** Your company password
   - Tap **Connect**

### **Connecting to COMPANY-BYOD (Personal Devices)**

#### **Initial Device Registration**
1. **Device Enrollment**
   - Navigate to `devicereg.company.com` on your personal device
   - Sign in with your **company credentials**
   - Complete the **device registration form**:
     - Device type and operating system
     - MAC address (automatically detected)
     - Device name/description
     - Intended usage

2. **Compliance Check**
   - Install **Company Mobile Device Management (MDM)** profile if required
   - Allow **basic device information** collection
   - Agree to **Acceptable Use Policy**
   - Complete **security assessment** questionnaire

3. **Approval Process**
   - Registration reviewed by IT Security within **24 hours**
   - Email notification sent upon approval/rejection
   - Approved devices receive **connection instructions**

#### **Network Connection**
1. **Connect to COMPANY-BYOD**
   - Select **COMPANY-BYOD** from available networks
   - **Username:** Your company username
   - **Password:** Your company password + current MFA token
   - **Domain:** COMPANY (if prompted)

2. **Accept Terms**
   - Review and accept **Network Usage Agreement**
   - Acknowledge **monitoring and security policies**
   - Complete connection process

### **Guest Network Access**

#### **For Visitors**
1. **Request Guest Access**
   - Contact your **company host/sponsor**
   - Host submits **guest access request** through IT Portal
   - Guest receives **welcome email** with connection details

2. **Connect to COMPANY-GUEST**
   - Select **COMPANY-GUEST** network
   - Enter **daily password** provided by host
   - Accept **Guest Network Terms** in captive portal
   - Access granted for **24 hours**

#### **For Contractors**
1. **Extended Guest Access**
   - Submit **contractor access request** through Procurement
   - Include **project duration** and **business justification**
   - IT provides **extended access credentials**
   - Access valid for **project duration** (up to 90 days)

## Network-Specific Features and Limitations

### **COMPANY-SECURE Network**
#### **Full Access Features**
- **Internal file shares** and network drives
- **Internal web applications** and intranet sites
- **Printer access** to network printers
- **VoIP phone** functionality
- **Video conferencing** with internal systems

#### **Security Features**
- **Network Access Control (NAC)** compliance checking
- **Automatic certificate** renewal and management
- **Device health** monitoring and reporting
- **Malware protection** through network filtering

### **COMPANY-BYOD Network**
#### **Limited Access Features**
- **Internet browsing** with content filtering
- **Email access** through web clients or mobile apps
- **Cloud applications** (Office 365, Salesforce, etc.)
- **Basic file sharing** through approved cloud services

#### **Restrictions**
- **No direct access** to internal file servers
- **Limited printer access** (designated BYOD printers only)
- **No VPN termination** on internal network
- **Bandwidth limitations** during peak hours

### **Guest Networks**
#### **Internet-Only Access**
- **Web browsing** with content filtering
- **Email access** through webmail
- **Basic productivity** applications
- **Social media** and communication apps

#### **Strict Limitations**
- **No internal network** access
- **No file sharing** capabilities
- **Time-based disconnection** (periodic re-authentication)
- **Bandwidth throttling** during high usage

## Troubleshooting Common Issues

### **Connection Problems**

#### **Cannot See Network**
- **Verify network availability:** Check with IT if network is broadcasting
- **Refresh network list:** Disable and re-enable WiFi adapter
- **Check location:** Ensure you're in a covered area
- **Restart device:** Reboot to clear network cache

#### **Authentication Failures**
- **Verify credentials:** Confirm username/password are correct
- **Check account status:** Ensure account is not locked or disabled
- **MFA issues:** Verify MFA device is working and synchronized
- **Certificate problems:** Reinstall company certificates

#### **Slow Performance**
- **Check signal strength:** Move closer to access point if signal is weak
- **Network congestion:** Try connecting during off-peak hours
- **Device issues:** Restart WiFi adapter or device
- **Interference:** Switch to 5GHz band if available

### **Device-Specific Issues**

#### **Windows Troubleshooting**
- **Run Network Troubleshooter:** Settings → Network → Status → Network Troubleshooter
- **Reset network settings:** `netsh wlan delete profile name="COMPANY-SECURE"`
- **Update WiFi drivers:** Check manufacturer's website for latest drivers
- **Check Windows updates:** Install latest security and feature updates

#### **macOS Troubleshooting**
- **Forget and rejoin:** System Preferences → Network → WiFi → Advanced → Forget Network
- **Reset network preferences:** Delete `/Library/Preferences/SystemConfiguration/`
- **Check keychain:** Remove old WiFi passwords from Keychain Access
- **Update macOS:** Install latest system updates

#### **Mobile Device Issues**
- **Reset network settings:** iOS: Settings → General → Reset → Reset Network Settings
- **Clear WiFi cache:** Android: Settings → Apps → WiFi → Storage → Clear Cache
- **Reinstall profiles:** Remove and reinstall company WiFi profiles
- **Check app permissions:** Ensure WiFi and location permissions are granted

## Security Best Practices

### **Device Security**
- **Keep devices updated** with latest security patches
- **Use strong device passwords** or biometric authentication
- **Enable automatic screen lock** with short timeout periods
- **Install reputable antivirus** software on personal devices
- **Avoid public charging stations** while connected to company WiFi

### **Network Security**
- **Never share WiFi passwords** with unauthorized users
- **Report suspicious activity** to IT Security immediately
- **Use encrypted connections** (HTTPS) when possible
- **Avoid sensitive transactions** on guest networks
- **Log off properly** when finished using network resources

### **Data Protection**
- **Use company-approved cloud storage** for business files
- **Enable device encryption** on all company-connected devices
- **Implement backup strategies** for important data
- **Follow data classification** policies for information handling
- **Report data incidents** promptly to Security team

## Performance Optimization

### **Connection Optimization**
- **Use 5GHz networks** when available for better performance
- **Position devices optimally** for best signal reception
- **Close unnecessary applications** that consume bandwidth
- **Update network drivers** regularly for optimal performance
- **Choose less congested channels** if configuring personal hotspots

### **Bandwidth Management**
- **Avoid large downloads** during business hours
- **Use wired connections** for bandwidth-intensive tasks when possible
- **Schedule updates** for off-peak hours
- **Compress files** before transferring over WiFi
- **Use efficient streaming settings** for video conferences

## Support and Resources

### **Self-Service Tools**
- **WiFi Status Page:** `status.company.com/wifi` - Real-time network status
- **Speed Test:** `speedtest.company.com` - Internal network speed testing
- **Coverage Maps:** Available on company intranet under IT Services
- **Configuration Guides:** Detailed setup instructions for all device types

### **Technical Support**
- **IT Help Desk:** `helpdesk@company.com` or ext. 4357
- **WiFi Specialists:** `wifi-support@company.com`
- **Network Operations:** `netops@company.com` (for outages and performance issues)
- **Security Team:** `security@company.com` (for security-related WiFi concerns)

### **Training and Documentation**
- **WiFi Security Training:** Required annually for all users
- **BYOD Policy Training:** Required before personal device registration
- **Guest Network Guidelines:** Available for employees hosting visitors
- **Network Etiquette:** Best practices for shared wireless resources

## Policies and Compliance

### **Acceptable Use Policy**
- **Business use priority** - Company networks are primarily for business purposes
- **Prohibited activities** include illegal downloads, streaming non-business content during work hours
- **Bandwidth limitations** may be enforced during peak usage
- **Monitoring notice** - Network activity may be logged and monitored

### **Device Management**
- **Company devices** must be managed through Active Directory and Group Policy
- **Personal devices** on BYOD network require basic MDM enrollment
- **Guest devices** are subject to time-based access controls
- **Non-compliant devices** may be automatically disconnected

### **Data Governance**
- **Data classification** policies apply to all network-transmitted data
- **Encryption requirements** for sensitive data transmission
- **Retention policies** for network logs and access records
- **Incident response** procedures for security events

---

*Last updated: [Current Date] | Document ID: KB-WIFI-001 | Classification: Internal Use*
