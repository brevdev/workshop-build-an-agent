# Requesting HPC Cluster Access

## Purpose

This article provides instructions for requesting access to the company's High Performance Computing (HPC) cluster resources. HPC clusters are designed for computationally intensive workloads that require parallel processing, large memory allocations, or specialized hardware accelerators.

## What is HPC Cluster Access

High Performance Computing clusters are networked collections of powerful computers that work together to solve complex computational problems. Our HPC environment provides:

- **Parallel processing capabilities** for compute-intensive applications
- **High-memory nodes** for large dataset analysis
- **GPU acceleration** for machine learning and scientific computing
- **High-speed interconnects** for distributed computing workloads
- **Specialized software** for research and development applications

## Eligibility and Use Cases

HPC cluster access is available for legitimate business and research needs, including:

### **Research and Development**
- Scientific simulations and modeling
- Computational fluid dynamics (CFD)
- Finite element analysis (FEA)
- Climate and weather modeling
- Genomics and bioinformatics research

### **Data Analytics and Machine Learning**
- Large-scale data processing and analytics
- Machine learning model training
- Deep learning neural networks
- Statistical analysis of big datasets
- Artificial intelligence research

### **Engineering and Design**
- Computer-aided engineering (CAE)
- Structural analysis and optimization
- Signal processing applications
- Image and video processing
- Rendering and visualization

### **Business Intelligence**
- Financial risk modeling
- Supply chain optimization
- Market simulation and forecasting
- Customer behavior analysis
- Operations research

## Cluster Resources Available

### **Compute Nodes**
- **Standard Nodes:** 128 nodes, 48 cores each, 192 GB RAM
- **High-Memory Nodes:** 16 nodes, 48 cores each, 768 GB RAM
- **GPU Nodes:** 8 nodes, 4x NVIDIA A100 GPUs each, 512 GB RAM
- **Fat Nodes:** 4 nodes, 96 cores each, 1.5 TB RAM

### **Storage Systems**
- **Home Directory:** 100 GB per user (backed up daily)
- **Scratch Storage:** 10 TB per project (temporary, high-performance)
- **Project Storage:** 1-50 TB per project (long-term, backed up)
- **Archive Storage:** Unlimited (tape-based, for long-term retention)

### **Software Environment**
- **Operating System:** Rocky Linux 8
- **Job Scheduler:** Slurm Workload Manager
- **Compilers:** GCC, Intel, NVIDIA HPC SDK
- **MPI Libraries:** OpenMPI, Intel MPI, MVAPICH2
- **Scientific Software:** MATLAB, Mathematica, ANSYS, Abaqus, and 200+ packages

## Prerequisites

Before requesting HPC access, ensure you have:

- **Active company account** with appropriate security clearance
- **Manager or PI approval** for resource allocation
- **Basic Linux command-line knowledge** (training available)
- **Understanding of batch job submission** concepts
- **Defined project scope** with computational requirements
- **Budget approval** for resource usage charges

## Account Types and Allocations

### **Trial Account (Free)**
- **Duration:** 30 days
- **Resources:** Up to 1,000 CPU hours
- **Storage:** 100 GB home directory only
- **Purpose:** Evaluation and small-scale testing
- **Limitations:** Standard nodes only, no GPU access

### **Research Account**
- **Duration:** 1 year (renewable)
- **Resources:** 10,000-100,000 CPU hours per quarter
- **Storage:** Up to 5 TB project storage
- **GPU Hours:** 500-5,000 hours per quarter
- **Cost:** $0.05 per CPU hour, $2.50 per GPU hour

### **Production Account**
- **Duration:** Multi-year agreements available
- **Resources:** 100,000+ CPU hours per quarter
- **Storage:** 10-50 TB project storage
- **Priority Access:** Dedicated queues and reservations
- **Cost:** Negotiated rates based on commitment

### **Educational Account**
- **Duration:** Academic semester/year
- **Resources:** 5,000 CPU hours per quarter
- **Storage:** 1 TB project storage
- **Cost:** Free for approved educational projects
- **Restrictions:** Academic use only, no commercial applications

## Request Procedure

### 1. Project Planning and Justification

Before submitting a request, prepare the following information:

#### **Technical Requirements**
- **Computational workload description** and expected runtime
- **Software requirements** and licensing needs
- **Memory and storage requirements** per job
- **Parallel processing needs** (number of cores/nodes)
- **GPU requirements** (if applicable)
- **Network and I/O requirements**

#### **Project Details**
- **Project title and description**
- **Principal Investigator (PI)** or project sponsor
- **Team members** requiring access
- **Project timeline** and milestones
- **Expected deliverables** and outcomes

#### **Resource Estimation**
- **Estimated total CPU/GPU hours** needed
- **Peak resource requirements** during project
- **Storage needs** throughout project lifecycle
- **Data transfer requirements** (inbound/outbound)

### 2. Submit Access Request

- Navigate to the **HPC Portal** at `hpc.company.com`
- Click **Request Access** and select **New Project Request**
- Complete the comprehensive request form:

#### **Required Information**
- **Applicant details** (name, department, contact information)
- **Project information** (title, description, duration)
- **Technical requirements** (compute, memory, storage, software)
- **Team members** and their roles
- **Budget information** and funding source
- **Manager/PI approval** (digital signature required)

#### **Supporting Documentation**
- **Project proposal** or research plan
- **Budget justification** and cost center information
- **Software licensing** documentation (if required)
- **Data management plan** (for sensitive data)
- **Publications or reports** from previous HPC work (if applicable)

### 3. Review and Approval Process

#### **Initial Review (3-5 business days)**
- **Technical feasibility assessment** by HPC team
- **Resource availability confirmation**
- **Software licensing verification**
- **Security and compliance review** (if applicable)

#### **Allocation Committee Review (5-10 business days)**
- **Scientific/business merit evaluation**
- **Resource allocation determination**
- **Priority level assignment**
- **Budget and cost approval**

#### **Final Approval and Provisioning (2-3 business days)**
- **Account creation and configuration**
- **Storage allocation and setup**
- **Software environment preparation**
- **Access credentials and documentation delivery**

### 4. Account Setup and Orientation

#### **Initial Access**
- **SSH Key Setup:** Generate and upload public SSH key
- **Login Node Access:** `login.hpc.company.com`
- **Username:** Assigned during provisioning process
- **Authentication:** SSH key-based (no password login)

#### **Mandatory Orientation**
- **HPC Basics Workshop:** 2-hour session covering cluster architecture
- **Job Submission Training:** Hands-on Slurm scheduler training
- **Storage and Data Management:** Best practices for file systems
- **Software Environment:** Module system and available applications
- **Schedule:** Monthly sessions or on-demand for urgent projects

#### **Getting Started Resources**
- **Quick Start Guide:** Comprehensive PDF documentation
- **Sample Job Scripts:** Templates for common workloads
- **Benchmarking Tools:** Performance testing utilities
- **User Forum:** `community.company.com/hpc-users`

## Usage Guidelines and Best Practices

### **Job Submission Best Practices**
- **Use appropriate queues** based on job requirements:
  - `short`: Jobs < 2 hours, up to 16 nodes
  - `medium`: Jobs 2-24 hours, up to 64 nodes
  - `long`: Jobs 24-168 hours, up to 32 nodes
  - `gpu`: GPU-accelerated jobs, up to 8 GPU nodes
  - `bigmem`: High-memory jobs, up to 16 high-memory nodes

### **Resource Optimization**
- **Right-size your jobs** - don't request more resources than needed
- **Use checkpointing** for long-running jobs
- **Optimize I/O patterns** to minimize storage system impact
- **Profile your applications** to identify bottlenecks
- **Use appropriate parallelization** strategies

### **Data Management**
- **Clean up temporary files** regularly from scratch storage
- **Archive completed project data** to long-term storage
- **Use appropriate file systems** for different data types
- **Follow data retention policies** for your organization
- **Implement backup strategies** for critical data

### **Fair Use and Etiquette**
- **Monitor your resource usage** through the HPC portal
- **Don't monopolize resources** - be considerate of other users
- **Report problems promptly** to help maintain system stability
- **Participate in user community** discussions and feedback
- **Acknowledge HPC resources** in publications and reports

## Monitoring and Billing

### **Usage Tracking**
- **Real-time monitoring** available through HPC Portal
- **Job accounting** and resource utilization reports
- **Monthly usage summaries** emailed to users and PIs
- **Allocation tracking** against approved limits

### **Billing Structure**
- **CPU Hours:** Charged per core-hour used
- **GPU Hours:** Charged per GPU-hour used
- **Storage:** Monthly charges for project storage over base allocation
- **Data Transfer:** Charges for large external data transfers
- **Monthly Billing:** Automatic charges to approved cost centers

### **Cost Management**
- **Budget alerts** when approaching allocation limits
- **Usage forecasting** tools to predict future needs
- **Optimization recommendations** from HPC team
- **Quarterly reviews** with resource managers

## Troubleshooting and Support

### **Common Issues**
- **Job failures:** Check error logs and resource requirements
- **Performance problems:** Profile applications and optimize code
- **Software issues:** Verify module loading and dependencies
- **Storage problems:** Check quotas and file permissions
- **Authentication failures:** Verify SSH keys and network connectivity

### **Getting Help**
- **Documentation:** Comprehensive guides at `docs.hpc.company.com`
- **Ticket System:** Submit support requests through HPC Portal
- **User Consultations:** One-on-one sessions with HPC specialists
- **Office Hours:** Weekly drop-in sessions (Wednesdays 2-4 PM)
- **Emergency Support:** `hpc-emergency@company.com` for urgent issues

### **Training and Education**
- **Monthly Workshops:** Various topics for different skill levels
- **Online Tutorials:** Self-paced learning modules
- **Best Practices Seminars:** Quarterly sessions on optimization
- **User Conference:** Annual event with advanced topics and networking

## Account Renewal and Changes

### **Annual Renewal Process**
- **Renewal notifications** sent 60 days before expiration
- **Usage review** and allocation adjustment
- **Updated project documentation** required
- **Continued business justification** needed

### **Allocation Modifications**
- **Mid-cycle increases** available for justified needs
- **Emergency allocations** for time-sensitive projects
- **Resource type changes** (CPU to GPU, standard to high-memory)
- **Storage expansion** requests

### **Account Closure**
- **30-day notice** required for planned closure
- **Data migration assistance** provided
- **Final billing** and resource cleanup
- **Project archive** creation for future reference

## Security and Compliance

### **Data Security**
- **Encrypted data transmission** for all connections
- **Secure file systems** with appropriate access controls
- **Regular security audits** and vulnerability assessments
- **Compliance** with company data governance policies

### **Export Control and Regulations**
- **ITAR/EAR compliance** for applicable projects
- **International collaboration** restrictions
- **Publication review** requirements for sensitive research
- **Legal clearance** for certain types of computations

## Support Contacts

### **Technical Support**
- **HPC Help Desk:** `hpc-support@company.com` or ext. 4-HPC
- **System Administrators:** `hpc-admin@company.com`
- **User Consultants:** `hpc-consulting@company.com`
- **Training Coordinator:** `hpc-training@company.com`

### **Administrative Support**
- **Allocation Requests:** `hpc-allocations@company.com`
- **Billing Questions:** `hpc-billing@company.com`
- **Account Management:** `hpc-accounts@company.com`
- **Policy Questions:** `hpc-policy@company.com`

### **Emergency Contacts**
- **System Emergencies:** `hpc-emergency@company.com`
- **Security Incidents:** `security@company.com`
- **After-hours Support:** `1-800-HPC-HELP` (critical issues only)

---

*Last updated: [Current Date] | Document ID: KB-HPC-001 | Classification: Internal Use*
