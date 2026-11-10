# TeleKali 🐉

**Control your Kali Linux machine remotely through Telegram.**

TeleKali is a Python-based remote command execution tool that connects a Telegram bot to a Kali Linux system.

It allows an authenticated Telegram user to execute approved Linux commands and network diagnostic tools remotely through a simple Telegram interface.

## 🚀 Features

- Remote command execution through Telegram
- Telegram user ID authentication
- Linux system information retrieval
- Network interface inspection
- Routing table inspection
- Disk and memory usage monitoring
- Ping utility
- Nmap integration
- Nmap argument validation
- Command allowlisting
- Command execution timeout
- Output size limitation
- Command execution logging
- Per-user command rate limiting
- Environment-based configuration

## 🛠️ Supported Commands

### Linux System Commands

| Command | Description |
|---|---|
| `whoami` | Display current user |
| `uname -a` | Display system information |
| `ip a` | Display network interfaces |
| `ip route` | Display routing table |
| `df -h` | Display disk usage |
| `free -h` | Display memory usage |

### Network Commands

**Ping**

```bash
ping -c 2 192.168.100.5
```

**Nmap**

```bash
nmap 192.168.100.5
nmap -F 192.168.100.5
nmap -sV 192.168.100.5
nmap -p 80,443 192.168.100.5
nmap -sT -sV -p 80,443 192.168.100.5
nmap --top-ports 100 192.168.100.5
```

Nmap options and targets are validated before execution. The current MVP restricts targets to private IPv4 addresses and applies an allowlist of supported options.

## 📋 Requirements

- Kali Linux or compatible Linux distribution
- Python 3.10 or later
- Telegram account
- Telegram bot token
- Telegram numeric user ID
- Nmap installed on the host

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd TeleKali
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
nano .env
```

Configure your credentials:

```env
BOT_TOKEN=your_telegram_bot_token
AUTHORIZED_USER_ID=your_telegram_user_id
```

Never share your actual bot token.

### 5. Start TeleKali

```bash
python bot.py
```

## 📱 Telegram Usage

Open your Telegram bot and use:

```text
/start
/help
/status
```

Execute commands remotely:

```text
/cmd whoami
/cmd uname -a
/cmd ip a
/cmd ip route
/cmd df -h
/cmd free -h
/cmd ping -c 2 192.168.100.5
/cmd nmap -F 192.168.100.5
```

## 🔐 Security Features

- Authorized Telegram user ID verification
- Command allowlisting
- Nmap argument validation
- Private IPv4 target restrictions
- Subprocess execution without shell interpretation
- Command execution timeout
- Bounded command output
- Command rate limiting
- Execution logging
- Environment-based secret management

**Security note:** TeleKali is an educational MVP, not a hardened production remote-access platform. Private IP restrictions and command allowlisting are not substitutes for network isolation or operating-system-level security controls.

## 🧪 Testing

Run automated tests:

```bash
python -m unittest discover -s tests -v
```

Check Python syntax:

```bash
python -m py_compile bot.py config.py executor.py logger.py
```

## 📁 Project Structure

```text
TeleKali/
│
├── bot.py
├── config.py
├── executor.py
├── logger.py
│
├── config/
├── logs/
├── tests/
│   ├── __init__.py
│   └── test_executor.py
│
├── systemd/
├── backup/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🗺️ Project Roadmap

- [x] Telegram bot integration
- [x] Telegram user authentication
- [x] Linux command execution
- [x] Nmap integration
- [x] Command validation
- [x] Execution timeout and output limits
- [x] Basic automated tests
- [x] Rate limiting
- [ ] Extended security testing
- [ ] Improved process isolation
- [ ] Additional monitoring features
- [ ] Stable public release

## ⚠️ Disclaimer

TeleKali is developed for educational purposes, authorized system administration, and security testing.

Only execute commands on systems you own or have explicit permission to test.

The developer is not responsible for misuse of this software.

## 📄 License

This project is intended to be released under the MIT License.
See the LICENSE file for details.
