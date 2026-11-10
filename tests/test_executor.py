import unittest

from executor import validate_command


class TestTeleKali(unittest.TestCase):

    def test_linux_commands(self):
        commands = [
            "whoami",
            "uname -a",
            "ip a",
            "ip route",
            "df -h",
            "free -h",
        ]

        for command in commands:
            with self.subTest(command=command):
                argv, error = validate_command(command)
                self.assertIsNotNone(argv)
                self.assertIsNone(error)

    def test_nmap_commands(self):
        commands = [
            "nmap 192.168.100.5",
            "nmap -F 192.168.100.5",
            "nmap -sV 192.168.100.5",
            "nmap -p 80,443 192.168.100.5",
            "nmap -sT -sV -p 80,443 192.168.100.5",
            "nmap --top-ports 100 192.168.100.5",
        ]

        for command in commands:
            with self.subTest(command=command):
                argv, error = validate_command(command)
                self.assertIsNotNone(argv)
                self.assertIsNone(error)

    def test_rejected_commands(self):
        commands = [
            "whoami; id",
            "sudo nmap 192.168.100.5",
            "nmap -sS 192.168.100.5",
            "nmap 8.8.8.8",
            "nmap -p 99999 192.168.100.5",
        ]

        for command in commands:
            with self.subTest(command=command):
                argv, error = validate_command(command)
                self.assertIsNone(argv)
                self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()
