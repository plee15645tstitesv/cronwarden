# cronwarden

> A CLI tool to audit, validate, and document cron jobs across multiple servers from a single config file.

---

## Installation

```bash
pip install cronwarden
```

Or install from source:

```bash
git clone https://github.com/yourname/cronwarden.git && cd cronwarden && pip install .
```

---

## Usage

Define your servers and cron jobs in a single `cronwarden.yaml` config file:

```yaml
servers:
  - name: web-prod
    host: 192.168.1.10
    user: deploy
  - name: worker-01
    host: 192.168.1.20
    user: deploy

jobs:
  - name: daily-backup
    schedule: "0 2 * * *"
    command: /usr/local/bin/backup.sh
    servers: [web-prod]
  - name: queue-flush
    schedule: "*/5 * * * *"
    command: /usr/local/bin/flush-queue.sh
    servers: [worker-01]
```

Then run:

```bash
# Audit all cron jobs across servers
cronwarden audit

# Validate cron expressions in your config
cronwarden validate

# Generate a markdown report of all jobs
cronwarden docs --output cron-report.md
```

---

## Commands

| Command    | Description                                      |
|------------|--------------------------------------------------|
| `audit`    | Connect to servers and verify jobs are installed |
| `validate` | Check cron expressions and config structure      |
| `docs`     | Generate a human-readable report of all jobs     |

---

## License

MIT © [yourname](https://github.com/yourname)