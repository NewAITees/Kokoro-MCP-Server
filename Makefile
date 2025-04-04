.PHONY: build up down logs shell clean install-claude setup-claude test dev multi-arch-build

# Docker関連コマンド
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec kokoro-mcp-server /bin/bash

clean:
	docker compose down -v --rmi local

# マルチアーキテクチャビルド
multi-arch-build:
	chmod +x build-multi-arch.sh
	./build-multi-arch.sh

# Claude Desktop設定ヘルパー
install-claude-macos:
	mkdir -p ~/Library/Application\ Support/Claude/
	cp claude_desktop_config.json.example ~/Library/Application\ Support/Claude/claude_desktop_config.json
	@echo "Claude Desktop設定ファイルをインストールしました"
	@echo "場所: ~/Library/Application Support/Claude/claude_desktop_config.json"

install-claude-windows:
	mkdir -p "$(APPDATA)\Claude"
	cp claude_desktop_config.json.example "$(APPDATA)\Claude\claude_desktop_config.json"
	@echo "Claude Desktop設定ファイルをインストールしました"
	@echo "場所: %APPDATA%\Claude\claude_desktop_config.json"

setup-claude:
	@echo "使用しているOSを選択してください:"
	@echo "1) macOS"
	@echo "2) Windows"
	@read -p "選択 (1/2): " os; \
	case $$os in \
		1) make install-claude-macos ;; \
		2) make install-claude-windows ;; \
		*) echo "無効な選択です" ;; \
	esac

# 開発用コマンド
dev:
	MOCK_TTS=true docker compose up

test:
	docker compose run --rm kokoro-mcp-server pytest 