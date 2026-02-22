---
description: キャラ実装・導入手順（MUGEN AIR + 画像 + 当たり判定）
---

# キャラ実装・導入手順（MUGEN AIR + 画像 + 当たり判定）

このドキュメントは、新しいキャラクター素材（MUGENの `SFF` / `AIR` から書き出した画像と `AIR`）を本プロジェクトへ導入し、
アニメーション表示・当たり判定（`clsn1/clsn2`）・被弾（Action 5000）まで動かすための手順です。

## 1. 前提（このプロジェクトのキャラ実装モデル）

このプロジェクトの「キャラ」は、主に以下で成立しています。

- `assets/images/<CHAR_NAME>/organized/`
  - MUGENのグループ番号とインデックスから `(group, index)` を引けるようにしたPNG群
- `assets/images/<CHAR_NAME>/<CHAR_NAME>_air_actions.py`（例：`ryuko_air_actions.py`）
  - `ACTIONS = [...]` を持つPythonファイル
  - 各フレーム辞書に `group/index/x/y/time/flags/clsn1/clsn2` を持つ
- `src/entities/player.py`
  - `Player` が `ACTIONS` と `organized` PNG を読み込み、現在フレームを進めて描画
  - `clsn1` を攻撃判定、`clsn2` を食らい判定として毎フレーム同期
- `main.py`
  - `Player` を生成し、入力・更新・描画・ヒット処理を行う

## 2. 素材配置（フォルダ構成）

新キャラ `FOO` を導入する例です。

- `assets/images/FOO/FOO.AIR`
- `assets/images/FOO/organized/`（PNG群）
  - ファイル名に `_<group>_<index>.png` または `_<group>-<index>.png` を含める
  - 例: `Foo_200_0.png`, `Foo_0-0.png`

注意:
- `organized/` は「すでに整理済み」を前提です。
- もしFighter Factory等から「SFF出力画像」を丸ごと受け取る場合は、`scripts/organize_ryuko2nd_assets.py` と同等の整理処理を別途用意するか、
  既存スクリプトをキャラ汎用化してください。

## 3. AIRのパース→Python化（当たり判定 clsn1/clsn2 をフレームに埋め込む）

### 3.1 なぜ必要か

`Player` は「現在のアニメーションフレーム」に紐づく `clsn1/clsn2` を参照して、
`Hitbox/Hurtbox` を毎フレーム更新します。

そのため、`ACTIONS` の各フレームに `clsn1/clsn2` が入っている必要があります。

### 3.2 変換コマンド

`FOO.AIR` を `foo_air_actions.py` に書き出す例:

```powershell
python -c "from pathlib import Path; from scripts.organize_ryuko2nd_assets import parse_air_file, write_air_as_python; a=parse_air_file(Path('assets/images/FOO/FOO.AIR')); write_air_as_python(a, Path('assets/images/FOO/foo_air_actions.py')); print('actions=', len(a))"
```

補足:
- `parse_air_file` は `AIR` の `Clsn1/Clsn2` を読み取り、次のフレーム行に紐づけて `frame['clsn1'] / frame['clsn2']` に格納します。

## 4. コードへの組み込み

### 4.1 `main.py` で ACTIONS を読み込み `Player` に渡す

既存の `RYUKO2nd` 読み込みを参考に、対象ファイルとフォルダを差し替えます。

- `air_py` を `assets/images/FOO/foo_air_actions.py` に
- `sprites_root` を `assets/images/FOO/organized` に

そして `p1.set_mugen_animation(actions=actions, sprites_root=sprites_root)` を呼びます。

### 4.2 攻撃ID → AIR Action番号の割当

攻撃キーを押したときに、どのAIR Action（例: 200）を再生するかは `Player._attack_to_action_id()` で決まります。

- 例:
  - `P1_U_PUNCH` → 200
  - `P1_J_KICK` → 400

新キャラで異なるAction番号を使う場合は、ここを調整します。

### 4.3 被弾（HIT）アニメーション

被弾時は `Player.enter_hitstun()` により `Action 5000` を oneshot 再生します。

- 新キャラのAIRに `Begin Action 5000` が無い場合:
  - 被弾時に見た目が変わらない（または候補が無ければIdleへ戻る）ため、
  - `AIR` 側にAction 5000を用意するか、`_best_action_id([5000])` の候補を増やしてください。

## 5. 当たり判定（clsn1/clsn2）の仕様

- `clsn1`:
  - 攻撃判定（赤枠）
  - 「攻撃中」かつ「そのフレームにclsn1がある」時のみ有効
- `clsn2`:
  - 食らい判定（青枠）
  - 常に参照（フレームに無い場合は本体rectへフォールバック）

座標の基準:
- `clsn1/clsn2` は「Axis（キャラの原点）」からの相対座標
- `Player` は現在フレームの `x/y` を Axis の補正として加味し、
  `facing` が左向きのときはXを左右反転して `pygame.Rect` に変換します。

## 6. デバッグ手順（F3）

1. `python main.py` で起動
2. `F3` でデバッグ表示ON
3. 確認ポイント:
   - 青枠（`clsn2`）が体に沿ってフレーム同期している
   - 攻撃ボタンで、赤枠（`clsn1`）が「腕が伸びた瞬間だけ」出る
   - 左向き時に、当たり判定も左右反転している

## 7. よくある不具合と対策

- 判定が表示されない
  - `foo_air_actions.py` のフレームに `clsn1/clsn2` が入っているか確認
  - `AIR` → `Python` 変換をやり直す

- 判定が左右反転しない
  - `Player.facing` が更新されているか確認（`main.py` で相手位置から決める）

- 被弾モーションにならない
  - `AIR` に Action 5000 があるか確認

- 多段ヒットしてしまう
  - `Player.can_deal_damage()` / `mark_damage_dealt()` の制御が入っているか確認
