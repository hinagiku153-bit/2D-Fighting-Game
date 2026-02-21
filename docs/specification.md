# (仮) PyFight Online 仕様書

## プロジェクト名

(仮) PyFight Online

## 使用言語と環境

- Python 3.10以上
- Pygame CE (Community Edition)

## プロジェクトの目的

- Python/Pygameを用いた格闘ゲームの基礎習得。
- 1対1のローカル対戦およびオンライン対戦の実装。
- Windsurfを活用した効率的な開発フローの確立。

## ゲーム概要

- シンプルな2D対戦格闘（HP制、タイムリミットあり）。
- 基本的な操作（移動、ジャンプ、弱/強攻撃、ガード）。

## オンライン仕様

- Pythonの `socket` 通信または PodSixNet を使用した P2P / サーバークライアント方式。
- まずは同期方式（Delay-based）から着手する。

## 開発フェーズ

- Phase 1: ローカルでの2人操作と当たり判定の完成。
- Phase 2: キャラクター状態管理（State Machine）の洗練。
- Phase 3: 通信プロトコルの設計と同期テスト。
