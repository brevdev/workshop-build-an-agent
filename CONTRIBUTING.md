# Developing a lab using this template

There are two supported methods for running this developer environment:

- Working locally with [NVIDIA AI Workbench](https://www.nvidia.com/en-us/deep-learning-ai/solutions/data-science/workbench/)
- Working on the cloud with [NVIDIA Brev](https://brev.nvidia.com)

## Working Locally with Workbench

1. Download, install, and configure [NVIDIA AI Workbench](https://www.nvidia.com/en-us/deep-learning-ai/solutions/data-science/workbench/)

1. Use Workbench to clone this project to your desired location.

1. Map the host mount for `/var/host-run/` to `/var/run`.

1. Start your project and click **Open DevX-Lab**.

## Cloud Development with Brev Launchable

This repository supports building the development environment with a Brev Launchable. However, you will need to create the Launchable.

The Launchables will use a startup script in VM Mode to download+install NVIDIA AI Workbench, clone the project, and start Jupyter. They will also ensure Jupyter is restarted when the Brev machine restarts.

### Create the startup script

A starter Launchable startup script is available at [.project/brev.nvwb-startup.sh](.project/brev.nvwb-startup.sh). Edit the constants at the top of this file to point to your repo and branch.

Save this file, you'll use it in the next step.

### Create the Launchable

1. Go to the Brev [Launchable Creation Page](https://brev.nvidia.com/launchables/create)

1. Select `I have code files in a git repository`

1. Paste your GitHub repo URL into: `Enter a public repository or notebook file URL`

1. Select `VM Mode` and click `Next ->`

1. Upload or Paste in your startup script [from before](#create-the-startup-script). Click `Next ->`.

1. Select `No, I don't want Jupyter (Not Recommended)`.

1. Add a secure link with a **Secure Link Name** of `jupyter` and **Port** of `8888`.

1. Add any desired other servces and click `Next ->`.

1. Select and configure your desired hardware profile. Click `Next ->`.

1. Provide your new Workshop Launchable with a name.

1. Click `Create Launchable` and you will be provided with a link to your Lauchable!