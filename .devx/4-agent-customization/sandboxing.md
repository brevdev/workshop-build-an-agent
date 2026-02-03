# Safe Execution & Sandboxing

<img src="_static/robots/debug.png" alt="Safety" style="float:right;max-width:250px;margin:15px;" />

Terminal agents execute **real commands**—they can modify files and system state.

## Built-in Safety Layers

| Layer | How |
|-------|-----|
| **Command allowlist** | Only permitted commands can run |
| **Injection prevention** | Blocks `$` and backticks |
| **Human-in-the-loop** | Every command needs approval |

## Production: Sandboxing Options

| Solution | Use Case |
|----------|----------|
| **Docker** | Isolated filesystem, resource limits |
| **Modal** | Serverless sandboxed execution |
| **Firecracker** | Lightweight VMs for high security |

## Docker Example

```python
import docker
client = docker.from_env()
result = client.containers.run(
    "ubuntu:22.04", command,
    remove=True, network_mode="none"
)
```

## Best Practices

1. **Least privilege** — Only allow needed commands
2. **Audit logging** — Log every execution
3. **Rate limiting** — Prevent runaway agents

---

🎉 **Congratulations!** You've completed Module 4: Agent Customization.
