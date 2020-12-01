from src.ttp.reconnaissance.models import Scanner


class ScannerTest:
    scanner = Scanner(target='0.0.0.0')


if __name__ == '__main__':
    ScannerTest.scanner.run(True)
