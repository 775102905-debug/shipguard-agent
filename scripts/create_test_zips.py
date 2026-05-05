import zipfile
import os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = SCRIPTS_DIR.parent / "examples"
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def add_file(zf: zipfile.ZipFile, arcname: str, content: str):
    info = zipfile.ZipInfo(arcname)
    info.external_attr = 0o644 << 16
    zf.writestr(info, content)


def create_good_project():
    zip_path = EXAMPLES_DIR / "good_project.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        add_file(zf, "README.md", "# Good Project\n\nA well-structured project.\n\n## 环境要求\nPython 3.10+\n\n## 安装步骤\npip install -r requirements.txt\n\n## 运行命令\npython main.py\n\n## 测试说明\npytest\n\n## 配置说明\nCopy .env.example to .env\n")
        add_file(zf, "requirements.txt", "fastapi==0.110.0\nuvicorn==0.29.0\n")
        add_file(zf, ".env.example", "APP_ENV=development\nDEBUG=True\n")
        add_file(zf, ".gitignore", "*.pyc\n__pycache__/\n.env\n")
        add_file(zf, "Dockerfile", "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"main.py\"]\n")
        add_file(zf, "docker-compose.yml", "version: '3.9'\nservices:\n  app:\n    build: .\n    ports:\n      - \"8000:8000\"\n")
        add_file(zf, "LICENSE", "MIT License\nCopyright (c) 2026\n")
        add_file(zf, "app/main.py", "print('hello')\n")
        add_file(zf, "tests/test_main.py", "def test_hello():\n    assert True\n")
    print(f"[OK] Created good_project.zip at {zip_path}")
    return zip_path


def create_bad_project():
    zip_path = EXAMPLES_DIR / "bad_project.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        add_file(zf, "app.py", "DEBUG=True\nSECRET_KEY='FAKE_OPENAI_KEY_FOR_SCANNER_TEST'\n")
        add_file(zf, "config.py", "PASSWORD='super-secret-pwd'\nAPI_KEY='FAKE_API_KEY_FOR_SCANNER_TEST'\nCORS_ORIGINS='*'\n")
        add_file(zf, "utils/path_helper.py", "DATA_DIR = 'C:\\\\Users\\\\fake\\\\path\\\\to\\\\data'\nLOG_DIR = '/Users/fakeuser/logs'\n")
        add_file(zf, "utils/auth.py", "Authorization = 'Bearer FAKE_BEARER_TOKEN_FOR_SCANNER_TEST'\n")
        add_file(zf, ".env", "OPENAI_API_KEY=FAKE_OPENAI_KEY_DO_NOT_USE\nDATABASE_URL=postgres://user:pass@localhost/db\n")
        add_file(zf, "node_modules/some_pkg/index.js", "console.log('this should be skipped')\n")
        add_file(zf, "node_modules/other_pkg/secret.js", "const SECRET = 'should-not-be-found-in-scan';\n")
        add_file(zf, "package.json", '{"name": "bad-project", "version": "1.0.0"}\n')
        add_file(zf, ".git/HEAD", "ref: refs/heads/main\n")
        add_file(zf, "dist/bundle.js", "var API_KEY = 'FAKE_KEY_SHOULD_BE_SKIPPED';\n")
        add_file(zf, "__pycache__/module.pyc", "cached bytecode - should be skipped\n")
    print(f"[OK] Created bad_project.zip at {zip_path}")
    return zip_path


if __name__ == "__main__":
    create_good_project()
    create_bad_project()
    print("\nDone. Run 'python scripts/smoke_test.py' to verify.")
