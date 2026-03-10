# Source Control Management

## Purpose

This article provides comprehensive guidance on using the company's source control management systems for software development, document versioning, and collaborative project work. Proper source control practices ensure code integrity, enable team collaboration, and maintain project history for audit and recovery purposes.

## What is Source Control Management

Source Control Management (SCM), also known as Version Control, is a system that tracks changes to files and directories over time, allowing multiple users to collaborate on projects while maintaining a complete history of modifications. Our SCM systems provide:

- **Version tracking** for all code and document changes
- **Collaborative development** with merge and conflict resolution
- **Branch management** for parallel development workflows
- **Backup and recovery** through distributed repositories
- **Audit trails** for compliance and change tracking
- **Release management** and deployment coordination

## Available Source Control Systems

### **Git (Primary System)**
- **Platform:** GitLab Enterprise (self-hosted)
- **URL:** `git.company.com`
- **Purpose:** Primary source control for all software development
- **Features:** Distributed version control, advanced branching, CI/CD integration
- **Capacity:** Unlimited repositories, 10GB per repository limit
- **Backup:** Daily snapshots, geo-redundant storage

### **Subversion (SVN) - Legacy**
- **Platform:** Apache Subversion
- **URL:** `svn.company.com`
- **Purpose:** Legacy projects and document management
- **Status:** Maintenance mode - migration to Git recommended
- **Features:** Centralized version control, directory versioning
- **Migration Support:** Available through IT Development Services

### **Team Foundation Server (TFS)**
- **Platform:** Azure DevOps Server
- **URL:** `tfs.company.com`
- **Purpose:** Microsoft stack development and project management
- **Features:** Work item tracking, build automation, testing tools
- **Integration:** Visual Studio, Office 365, Microsoft Project
- **Licensing:** Per-user licensing through Microsoft Enterprise Agreement

## Account Setup and Access

### **Prerequisites**
Before requesting source control access, ensure you have:

- **Active company network account** with appropriate permissions
- **Development role** or manager approval for access
- **Basic understanding** of version control concepts
- **Completed security training** for code management
- **SSH key pair** generated for Git authentication
- **Development workstation** with required tools installed

### **Git Access Setup**

#### **1. Request GitLab Account**
- Navigate to **IT Service Portal** → **Development Services** → **GitLab Access Request**
- Complete the access request form:
  - **Employee information** and department
  - **Project or team** requiring access
  - **Role requested** (Developer, Maintainer, Owner)
  - **Manager approval** (digital signature required)
  - **Security clearance level** (if applicable)

#### **2. Account Provisioning (2-3 business days)**
- **GitLab account creation** with appropriate permissions
- **Group membership** assignment based on team structure
- **Initial repository access** configuration
- **Welcome email** with setup instructions

#### **3. SSH Key Configuration**
1. **Generate SSH Key Pair**
   ```bash
   ssh-keygen -t ed25519 -C "your.email@company.com"
   ```
   - Save to default location (`~/.ssh/id_ed25519`)
   - Use strong passphrase for security
   - Do not share private key

2. **Add Public Key to GitLab**
   - Login to `git.company.com`
   - Navigate to **User Settings** → **SSH Keys**
   - Paste contents of `~/.ssh/id_ed25519.pub`
   - Add descriptive title (e.g., "Work Laptop - John Doe")
   - Set expiration date (maximum 1 year)

3. **Test SSH Connection**
   ```bash
   ssh -T git@git.company.com
   ```
   - Should return welcome message with your username
   - If connection fails, contact IT Development Services

### **Development Tool Setup**

#### **Git Client Installation**
- **Windows:** Download from `git.company.com/downloads/git-windows`
- **macOS:** Install via Homebrew: `brew install git`
- **Linux:** Install via package manager: `sudo apt install git`
- **Configuration required:** Set username and email globally

#### **Integrated Development Environments**
- **Visual Studio Code:** Install GitLens extension for enhanced Git integration
- **IntelliJ IDEA:** Built-in Git support with company GitLab integration
- **Visual Studio:** Team Explorer with GitLab plugin
- **Eclipse:** EGit plugin for Git integration

#### **Initial Git Configuration**
```bash
git config --global user.name "Your Full Name"
git config --global user.email "your.email@company.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

## Repository Management

### **Repository Types and Naming Conventions**

#### **Application Repositories**
- **Naming:** `app-[application-name]`
- **Examples:** `app-customer-portal`, `app-inventory-management`
- **Purpose:** Complete application codebases
- **Structure:** Standard application directory layout
- **Access:** Team-based with role permissions

#### **Library Repositories**
- **Naming:** `lib-[library-name]`
- **Examples:** `lib-authentication`, `lib-data-access`
- **Purpose:** Shared code libraries and components
- **Structure:** Library-specific organization
- **Access:** Broader access for reuse across projects

#### **Infrastructure Repositories**
- **Naming:** `infra-[infrastructure-component]`
- **Examples:** `infra-kubernetes-configs`, `infra-terraform-modules`
- **Purpose:** Infrastructure as Code and deployment configurations
- **Structure:** Environment-based organization
- **Access:** DevOps and infrastructure teams

#### **Documentation Repositories**
- **Naming:** `docs-[project-or-team]`
- **Examples:** `docs-api-specifications`, `docs-architecture`
- **Purpose:** Technical documentation and specifications
- **Structure:** Topic-based organization with markdown files
- **Access:** Read access for stakeholders, write access for authors

### **Creating New Repositories**

#### **Repository Creation Process**
1. **Request Approval**
   - Submit **Repository Creation Request** through IT Service Portal
   - Include **project justification** and team information
   - Specify **access requirements** and initial team members
   - Manager approval required for new projects

2. **Repository Setup**
   - **Create repository** in appropriate GitLab group
   - **Configure default branch** protection rules
   - **Set up initial structure** with README, .gitignore, LICENSE
   - **Configure CI/CD pipelines** if applicable

3. **Team Access Configuration**
   - **Add team members** with appropriate roles
   - **Configure branch permissions** and merge requirements
   - **Set up notification preferences** for team communication
   - **Document repository** purpose and contribution guidelines

#### **Initial Repository Structure**
```
project-root/
├── README.md                 # Project overview and setup instructions
├── .gitignore               # Files to exclude from version control
├── LICENSE                  # Project licensing information
├── CONTRIBUTING.md          # Contribution guidelines for team members
├── CHANGELOG.md             # Version history and release notes
├── docs/                    # Project documentation
├── src/                     # Source code directory
├── tests/                   # Test files and test data
├── config/                  # Configuration files
└── scripts/                 # Build and deployment scripts
```

## Branching Strategy and Workflow

### **Git Flow Model**
The company follows a modified Git Flow branching strategy:

#### **Main Branches**
- **`main`:** Production-ready code, protected branch
  - Direct commits prohibited
  - Merge only through pull requests
  - Automatic deployment to production
  - Tagged for releases

- **`develop`:** Integration branch for features
  - Latest development changes
  - Automatic deployment to staging environment
  - Base branch for feature development

#### **Supporting Branches**
- **Feature Branches:** `feature/[ticket-number]-[brief-description]`
  - Created from `develop` branch
  - Merged back to `develop` via pull request
  - Deleted after successful merge
  - Examples: `feature/PROJ-123-user-authentication`

- **Release Branches:** `release/[version-number]`
  - Created from `develop` when ready for release
  - Bug fixes only, no new features
  - Merged to both `main` and `develop`
  - Tagged with version number

- **Hotfix Branches:** `hotfix/[ticket-number]-[brief-description]`
  - Created from `main` for critical production fixes
  - Merged to both `main` and `develop`
  - Immediate deployment to production
  - Examples: `hotfix/PROJ-456-security-patch`

### **Development Workflow**

#### **Starting New Work**
1. **Update Local Repository**
   ```bash
   git checkout develop
   git pull origin develop
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/PROJ-123-user-authentication
   ```

3. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "PROJ-123: Implement user authentication module"
   ```

4. **Push Branch to Remote**
   ```bash
   git push -u origin feature/PROJ-123-user-authentication
   ```

#### **Pull Request Process**
1. **Create Pull Request**
   - Navigate to GitLab repository
   - Click **Create Merge Request**
   - Select source branch and target (`develop`)
   - Add descriptive title and detailed description

2. **Pull Request Requirements**
   - **Code review** by at least one team member
   - **Automated tests** must pass
   - **No merge conflicts** with target branch
   - **Documentation updates** if applicable
   - **Security scan** completion (automatic)

3. **Review and Approval**
   - **Reviewers assigned** automatically based on code ownership
   - **Address feedback** and update code as needed
   - **Approval required** from designated reviewers
   - **Merge when approved** and all checks pass

## Code Review Guidelines

### **Review Responsibilities**

#### **Author Responsibilities**
- **Self-review code** before submitting pull request
- **Write clear commit messages** following conventional format
- **Include tests** for new functionality
- **Update documentation** for API or behavior changes
- **Respond promptly** to reviewer feedback
- **Keep pull requests focused** and reasonably sized

#### **Reviewer Responsibilities**
- **Review within 24 hours** during business days
- **Provide constructive feedback** with specific suggestions
- **Check for security vulnerabilities** and best practices
- **Verify test coverage** and quality
- **Ensure compliance** with coding standards
- **Approve only when confident** in code quality

### **Review Criteria**

#### **Code Quality**
- **Readability:** Clear, well-commented code
- **Maintainability:** Modular design with appropriate abstractions
- **Performance:** Efficient algorithms and resource usage
- **Security:** No obvious vulnerabilities or sensitive data exposure
- **Testing:** Adequate test coverage and quality
- **Standards:** Adherence to team coding conventions

#### **Technical Requirements**
- **Functionality:** Code works as intended and meets requirements
- **Error Handling:** Appropriate exception handling and logging
- **Dependencies:** Minimal and justified external dependencies
- **Documentation:** Updated API docs and inline comments
- **Configuration:** Environment-specific settings externalized
- **Backward Compatibility:** Considers impact on existing functionality

## Security and Compliance

### **Repository Security**

#### **Access Control**
- **Role-based permissions** aligned with job responsibilities
- **Principle of least privilege** for repository access
- **Regular access reviews** quarterly for all repositories
- **Automated deprovisioning** when employees change roles
- **Guest access restrictions** for external collaborators

#### **Branch Protection**
- **Protected main branch** prevents direct commits
- **Required pull request reviews** before merging
- **Status checks required** for automated testing
- **Dismiss stale reviews** when new commits pushed
- **Restrict force pushes** to prevent history rewriting

#### **Secret Management**
- **No secrets in code** - use environment variables or secret management
- **API keys and passwords** stored in company secret management system
- **Database credentials** managed through configuration management
- **SSL certificates** stored in secure certificate store
- **Regular secret rotation** following security policies

### **Compliance Requirements**

#### **Audit Trail**
- **Complete commit history** maintained for all repositories
- **Author identification** through verified email addresses
- **Change tracking** with detailed commit messages
- **Release documentation** for all production deployments
- **Backup verification** through regular restore testing

#### **Data Classification**
- **Source code classification** based on business sensitivity
- **Intellectual property** protection through access controls
- **Customer data handling** following privacy regulations
- **Export control** compliance for international development
- **Retention policies** for archived repositories

## Backup and Recovery

### **Backup Strategy**
- **Distributed nature** of Git provides inherent backup
- **Daily snapshots** of GitLab server and data
- **Geo-redundant storage** in multiple data centers
- **Developer workstations** serve as additional backups
- **Automated backup verification** and integrity checking

### **Recovery Procedures**

#### **Repository Recovery**
1. **Individual File Recovery**
   ```bash
   git checkout HEAD~1 -- filename.txt  # Restore from previous commit
   git checkout branch-name -- filename.txt  # Restore from specific branch
   ```

2. **Branch Recovery**
   ```bash
   git reflog  # Find lost commit hash
   git checkout -b recovered-branch [commit-hash]
   ```

3. **Complete Repository Recovery**
   - Contact **IT Development Services** for server-level recovery
   - Provide **repository name** and **approximate timeframe**
   - Recovery typically completed within **4 hours**

#### **Disaster Recovery**
- **Primary site failure:** Automatic failover to secondary data center
- **Complete data loss:** Restore from most recent backup (maximum 24 hours old)
- **Partial corruption:** Selective restore of affected repositories
- **Communication plan:** Status updates through company communication channels

## Training and Best Practices

### **Required Training**
- **Git Fundamentals:** 4-hour course for all developers
- **Code Review Training:** 2-hour workshop on review practices
- **Security Awareness:** Annual training on secure coding practices
- **Compliance Training:** Specific to regulated industries or projects

### **Best Practices**

#### **Commit Guidelines**
- **Atomic commits:** Each commit represents a single logical change
- **Descriptive messages:** Clear explanation of what and why
- **Conventional format:** `[TICKET-ID]: Brief description of change`
- **Regular commits:** Commit frequently to avoid large changesets
- **Clean history:** Use interactive rebase to clean up before merging

#### **Collaboration Guidelines**
- **Communication:** Discuss significant changes with team before implementation
- **Documentation:** Update relevant documentation with code changes
- **Testing:** Write tests for new features and bug fixes
- **Code style:** Follow established team conventions and style guides
- **Peer review:** Engage constructively in code review process

## Troubleshooting Common Issues

### **Authentication Problems**

#### **SSH Key Issues**
- **Permission denied:** Verify SSH key is added to GitLab profile
- **Key not found:** Check SSH agent is running and key is loaded
- **Wrong key:** Ensure correct private key file is being used
- **Expired key:** Generate new key pair if existing key expired

#### **HTTPS Authentication**
- **Password prompts:** Configure credential helper for automatic authentication
- **Token authentication:** Use personal access tokens instead of passwords
- **Two-factor authentication:** Generate application-specific passwords
- **Corporate proxy:** Configure Git to work with company proxy settings

### **Repository Issues**

#### **Merge Conflicts**
1. **Identify conflicted files:**
   ```bash
   git status  # Shows files with conflicts
   ```

2. **Resolve conflicts manually:**
   - Edit files to resolve conflicts
   - Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
   - Test changes to ensure functionality

3. **Complete merge:**
   ```bash
   git add resolved-file.txt
   git commit -m "Resolve merge conflict in resolved-file.txt"
   ```

#### **Performance Issues**
- **Large repository:** Use Git LFS for large binary files
- **Slow clones:** Use shallow clones for CI/CD environments
- **Network issues:** Configure Git to use company proxy settings
- **Disk space:** Regular cleanup of local branches and Git garbage collection

## Support and Resources

### **Development Services Support**
- **Git Support:** `git-support@company.com` or ext. 4-GIT
- **Repository Management:** `repo-admin@company.com`
- **CI/CD Pipeline Support:** `devops-support@company.com`
- **Security Questions:** `devsec@company.com`

### **Self-Service Resources**
- **Git Documentation:** `git.company.com/help`
- **Video Tutorials:** Available in Learning Portal → Development Training
- **Cheat Sheets:** Quick reference guides for common Git commands
- **Team Wikis:** Project-specific documentation and guidelines

### **Training and Certification**
- **Internal Training:** Monthly Git workshops for beginners and advanced users
- **External Training:** Budget available for Git certification courses
- **Conference Attendance:** Support for version control and DevOps conferences
- **Mentorship Program:** Pairing experienced developers with newcomers

### **Community Resources**
- **Developer Forum:** `community.company.com/developers`
- **Lunch and Learn:** Monthly presentations on development topics
- **Code Review Club:** Weekly sessions for reviewing and discussing code
- **Open Source Contributions:** Encouraged with legal approval process

---

*Last updated: [Current Date] | Document ID: KB-SCM-001 | Classification: Internal Use*
