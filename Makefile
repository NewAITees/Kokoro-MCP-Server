.PHONY: setup run test lint format clean

# セットアップ
setup:
	uv venv
	uv pip install -e ".[dev,test]"

# サーバー起動
run:
	python -m src.main

# テスト実行
test:
	pytest

# リント
lint:
	flake8 src tests
	mypy src

# フォーマット
format:
	black src tests
	isort src tests

# クリーンアップ
clean:
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 