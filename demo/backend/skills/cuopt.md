---
name: cuopt
description: Install and set up NVIDIA cuOpt including pip, conda, Docker, and GPU requirements. Solve vehicle routing problems (VRP, TSP, PDP) with NVIDIA cuOpt. Use when the user asks about installation, setup, environments, CUDA versions, GPU requirements, getting started, delivery optimization, fleet routing, time windows, capacities, pickup-delivery pairs, or traveling salesman problems.
---

# cuOpt Installation

Set up NVIDIA cuOpt for GPU-accelerated optimization.

## System Requirements

### GPU Requirements
- NVIDIA GPU with Compute Capability >= 7.0 (Volta or newer)
- Supported: V100, A100, H100, RTX 20xx/30xx/40xx, etc.
- NOT supported: GTX 10xx series (Pascal)

### CUDA Requirements
- CUDA 12.x or CUDA 13.x (match package suffix)
- Compatible NVIDIA driver

### Check Your System

```bash
# Check GPU
nvidia-smi

# Check CUDA version
nvcc --version

# Check compute capability
nvidia-smi --query-gpu=compute_cap --format=csv
```

## Installation Methods

### pip (Recommended for Python)

```bash
# For CUDA 13
pip install --extra-index-url=https://pypi.nvidia.com cuopt-cu13

# For CUDA 12
pip install --extra-index-url=https://pypi.nvidia.com cuopt-cu12

# With version pinning (recommended for reproducibility)
pip install --extra-index-url=https://pypi.nvidia.com 'cuopt-cu12==26.2.*'
```

### pip: Server + Client

```bash
# CUDA 12 example
pip install --extra-index-url=https://pypi.nvidia.com \
  cuopt-server-cu12 cuopt-sh-client

# With version pinning
pip install --extra-index-url=https://pypi.nvidia.com \
  cuopt-server-cu12==26.02.* cuopt-sh-client==26.02.*
```

### conda

```bash
# Python API
conda install -c rapidsai -c conda-forge -c nvidia cuopt

# Server + client
conda install -c rapidsai -c conda-forge -c nvidia cuopt-server cuopt-sh-client

# With version pinning
conda install -c rapidsai -c conda-forge -c nvidia cuopt=26.02.*
```

### Docker (Recommended for Server)

```bash
# Pull image
docker pull nvidia/cuopt:latest-cuda12.9-py3.13

# Run server
docker run --gpus all -it --rm \
  -p 8000:8000 \
  -e CUOPT_SERVER_PORT=8000 \
  nvidia/cuopt:latest-cuda12.9-py3.13

# Verify
curl http://localhost:8000/cuopt/health
```

### Docker: Interactive Python

```bash
docker run --gpus all -it --rm nvidia/cuopt:latest-cuda12.9-py3.13 python
```

## Verification

### Verify Python Installation

```python
# Test import
import cuopt
print(f"cuOpt version: {cuopt.__version__}")

# Test GPU access
from cuopt import routing
dm = routing.DataModel(n_locations=3, n_fleet=1, n_orders=2)
print("GPU access OK")
```

### Verify Server Installation

```bash
# Start server
python -m cuopt_server.cuopt_service --ip 0.0.0.0 --port 8000 &

# Wait and test
sleep 5
curl -s http://localhost:8000/cuopt/health | jq .
```

### Verify C API Installation

```bash
# Find header
find $CONDA_PREFIX -name "cuopt_c.h"

# Find library
find $CONDA_PREFIX -name "libcuopt.so"
```

## Common Installation Issues

### "No module named 'cuopt'"

```bash
# Check if installed
pip list | grep cuopt

# Check Python environment
which python
echo $CONDA_PREFIX

# Reinstall
pip uninstall cuopt-cu12 cuopt-cu13
pip install --extra-index-url=https://pypi.nvidia.com cuopt-cu12
```

### "CUDA not available" / GPU not detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA toolkit
nvcc --version

# In Python
import torch  # if using PyTorch
print(torch.cuda.is_available())
```

### Version mismatch (CUDA 12 vs 13)

```bash
# Check installed CUDA
nvcc --version

# Install matching package
# For CUDA 12.x
pip install cuopt-cu12

# For CUDA 13.x
pip install cuopt-cu13
```

### Docker: "could not select device driver"

```bash
# Install NVIDIA Container Toolkit
# Ubuntu:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Environment Setup

### Create Clean Environment (conda)

```bash
conda create -n cuopt-env python=3.11
conda activate cuopt-env
conda install -c rapidsai -c conda-forge -c nvidia cuopt
```

### Create Clean Environment (pip/venv)

```bash
python -m venv cuopt-env
source cuopt-env/bin/activate  # Linux/Mac
pip install --extra-index-url=https://pypi.nvidia.com cuopt-cu12
```

## Cloud Deployment

### AWS

- Use p4d.24xlarge (A100) or p3.2xlarge (V100)
- Deep Learning AMI has CUDA pre-installed
- Or use provided Docker image

### GCP

- Use a2-highgpu-1g (A100) or n1-standard with T4
- Deep Learning VM has CUDA pre-installed

### Azure

- Use NC-series (T4, A100)
- Data Science VM has CUDA pre-installed

## Offline Installation

```bash
# Download wheels on connected machine
pip download --extra-index-url=https://pypi.nvidia.com cuopt-cu12 -d ./wheels

# Transfer wheels directory to offline machine

# Install from local wheels
pip install --no-index --find-links=./wheels cuopt-cu12
```

## Upgrade

```bash
# pip
pip install --upgrade --extra-index-url=https://pypi.nvidia.com cuopt-cu12

# conda
conda update -c rapidsai -c conda-forge -c nvidia cuopt

# Docker
docker pull nvidia/cuopt:latest-cuda12.9-py3.13
```

## Verification Examples

See [resources/verification_examples.md](resources/verification_examples.md) for:
- Python installation verification
- LP/MILP verification
- Server verification
- C API verification
- System requirements check
- Docker verification

# cuOpt Routing

Model and solve vehicle routing problems using NVIDIA cuOpt's GPU-accelerated solver.

## Quick Reference: Python API

### Minimal VRP Example

```python
import cudf
from cuopt import routing

# Cost matrix (n_locations x n_locations)
cost_matrix = cudf.DataFrame([
    [0, 10, 15, 20],
    [10, 0, 12, 18],
    [15, 12, 0, 10],
    [20, 18, 10, 0],
], dtype="float32")

# Build data model
dm = routing.DataModel(
    n_locations=4,      # Total locations including depot
    n_fleet=2,          # Number of vehicles
    n_orders=3          # Orders to fulfill (locations 1,2,3)
)

# Required: cost matrix
dm.add_cost_matrix(cost_matrix)

# Required: order locations (which location each order is at)
dm.set_order_locations(cudf.Series([1, 2, 3]))

# Solve
solution = routing.Solve(dm, routing.SolverSettings())

# Check result
if solution.get_status() == 0:  # SUCCESS
    solution.display_routes()
```

### Adding Constraints

```python
# Time windows (need transit time matrix)
dm.add_transit_time_matrix(transit_time_matrix)
dm.set_order_time_windows(
    cudf.Series([0, 10, 20]),    # earliest
    cudf.Series([50, 60, 70])    # latest
)

# Capacities
dm.add_capacity_dimension(
    "weight",
    cudf.Series([20, 30, 25]),       # demand per order
    cudf.Series([100, 100])          # capacity per vehicle
)

# Service times
dm.set_order_service_times(cudf.Series([5, 5, 5]))

# Vehicle locations (start/end)
dm.set_vehicle_locations(
    cudf.Series([0, 0]),  # start at depot
    cudf.Series([0, 0])   # return to depot
)

# Vehicle time windows
dm.set_vehicle_time_windows(
    cudf.Series([0, 0]),      # earliest start
    cudf.Series([200, 200])   # latest return
)
```

### Pickup and Delivery (PDP)

```python
# Demand: positive=pickup, negative=delivery (must sum to 0 per pair)
demand = cudf.Series([10, -10, 15, -15])

# Pair indices: order 0 pairs with 1, order 2 pairs with 3
dm.set_pickup_delivery_pairs(
    cudf.Series([0, 2]),   # pickup order indices
    cudf.Series([1, 3])    # delivery order indices
)
```

### Precedence Constraints

Use `add_order_precedence()` to require certain orders to be visited before others.

**Important:** This is a per-node API — call it once for each order that has predecessors.

```python
import numpy as np

# Order 2 must come after orders 0 and 1
dm.add_order_precedence(
    node_id=2,                           # this order
    preceding_nodes=np.array([0, 1])     # must come after these
)

# Order 3 must come after order 2
dm.add_order_precedence(
    node_id=3,
    preceding_nodes=np.array([2])
)
```

**Rules:**
- Call once per order that has predecessors
- `preceding_nodes` is a numpy array of order indices
- Circular dependencies are NOT allowed (A before B before A)
- Orders without precedence constraints don't need a call

**Example: Assembly sequence**
```python
# Task B requires Task A to be done first
# Task C requires Tasks A and B to be done first
dm.add_order_precedence(1, np.array([0]))     # B after A
dm.add_order_precedence(2, np.array([0, 1]))  # C after A and B
```

## Quick Reference: REST Server

### Terminology Difference

| Concept | Python API | REST Server |
|---------|------------|-------------|
| Jobs | `order_locations` | `task_locations` |
| Time windows | `set_order_time_windows()` | `task_time_windows` |
| Service times | `set_order_service_times()` | `service_times` |

### Minimal REST Payload

```json
{
  "cost_matrix_data": {
    "data": {"0": [[0,10,15],[10,0,12],[15,12,0]]}
  },
  "travel_time_matrix_data": {
    "data": {"0": [[0,10,15],[10,0,12],[15,12,0]]}
  },
  "task_data": {
    "task_locations": [1, 2]
  },
  "fleet_data": {
    "vehicle_locations": [[0, 0]],
    "capacities": [[100]]
  },
  "solver_config": {
    "time_limit": 10
  }
}
```

## Solution Checking

```python
status = solution.get_status()
# 0 = SUCCESS
# 1 = FAIL
# 2 = TIMEOUT
# 3 = EMPTY

if status == 0:
    solution.display_routes()
    route_df = solution.get_route()
    total_cost = solution.get_total_objective()
else:
    print(f"Error: {solution.get_error_message()}")
    infeasible = solution.get_infeasible_orders()
    if len(infeasible) > 0:
        print(f"Infeasible orders: {infeasible.to_list()}")
```

## Solution DataFrame Schema

`solution.get_route()` returns a `cudf.DataFrame` with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `route` | int | Order/task index in the route sequence |
| `truck_id` | int | Vehicle ID assigned to this stop |
| `location` | int | Location index (0 = depot typically) |
| `arrival_stamp` | float | Arrival time at this location |

**Example output:**
```
   route  arrival_stamp  truck_id  location
0      0            0.0         1         0    # Vehicle 1 starts at depot
1      3            2.0         1         3    # Vehicle 1 visits location 3
2      2            4.0         1         2    # Vehicle 1 visits location 2
3      0            5.0         1         0    # Vehicle 1 returns to depot
4      0            0.0         0         0    # Vehicle 0 starts at depot
5      1            1.0         0         1    # Vehicle 0 visits location 1
6      0            3.0         0         0    # Vehicle 0 returns to depot
```

**Working with results:**
```python
route_df = solution.get_route()

# Routes per vehicle
for vid in route_df["truck_id"].unique().to_arrow().tolist():
    vehicle_route = route_df[route_df["truck_id"] == vid]
    locations = vehicle_route["location"].to_arrow().tolist()
    print(f"Vehicle {vid}: {locations}")

# Total travel time
max_arrival = route_df["arrival_stamp"].max()
```

## Common Issues

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Empty solution | Time windows too tight | Widen windows or check travel times |
| Infeasible orders | Demand > capacity | Increase fleet or capacity |
| Status != 0 | Missing transit time matrix | Add `add_transit_time_matrix()` when using time windows |
| Wrong route cost | Matrix not symmetric | Check cost_matrix values |

## Data Type Requirements

```python
# Always use explicit dtypes
cost_matrix = cost_matrix.astype("float32")
order_locations = cudf.Series([...], dtype="int32")
demand = cudf.Series([...], dtype="int32")
vehicle_capacity = cudf.Series([...], dtype="int32")
time_windows = cudf.Series([...], dtype="int32")
```

## Solver Settings

```python
ss = routing.SolverSettings()
ss.set_time_limit(30)           # seconds
ss.set_verbose_mode(True)       # enable progress output
ss.set_error_logging_mode(True) # log constraint errors if infeasible
```

## Examples

See `resources/` for complete examples:
- [Python API](resources/python_examples.md) — VRP, PDP, multi-depot
- [REST Server](resources/server_examples.md) — curl and Python requests
