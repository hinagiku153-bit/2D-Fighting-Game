from __future__ import annotations

import pygame

from src.entities.player import Player, PlayerInput
from src.utils import constants


def main() -> None:
    # Pygame 初期化。
    pygame.init()

    # 画面作成とフレーム管理用の Clock。
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    pygame.display.set_caption(constants.CAPTION)
    clock = pygame.time.Clock()

    # プレイヤー生成。
    # Phase 1 は「塗りつぶし矩形」だけでキャラクターを表現する。
    p1 = Player(x=150, color=constants.COLOR_P1)
    p2 = Player(x=constants.SCREEN_WIDTH - 200, color=constants.COLOR_P2)

    # 判定枠線（Hurtbox/Pushbox/Hitbox）を描画するかどうか。
    # F3 で切り替える。
    debug_draw = constants.DEBUG_DRAW_DEFAULT

    # “押した瞬間だけ True” にしたい入力は、KEYDOWN でトリガを立てて
    # フレームの先頭で False に戻す（エッジ入力）。
    p1_jump_pressed = False
    p2_jump_pressed = False
    p1_attack_pressed = False
    p2_attack_pressed = False

    running = True
    while running:
        # 毎フレーム、エッジ入力をリセット。
        p1_jump_pressed = False
        p2_jump_pressed = False
        p1_attack_pressed = False
        p2_attack_pressed = False

        # イベント処理：終了、デバッグ切り替え、ジャンプ/攻撃の押下（瞬間）入力。
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    debug_draw = not debug_draw
                elif event.key == pygame.K_w:
                    p1_jump_pressed = True
                elif event.key == pygame.K_UP:
                    p2_jump_pressed = True
                elif event.key == pygame.K_f:
                    p1_attack_pressed = True
                elif event.key == pygame.K_l:
                    p2_attack_pressed = True

        # 押しっぱなし入力（左右移動・しゃがみ）は get_pressed で取得。
        keys = pygame.key.get_pressed()

        # move_x は -1/0/+1 の3値にする。
        p1_move_x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        p2_move_x = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])

        p1_crouch = bool(keys[pygame.K_s])
        p2_crouch = bool(keys[pygame.K_DOWN])

        # 向きは相手の位置から決める（Phase 1 の簡易仕様）。
        p1.facing = 1 if p2.rect.centerx >= p1.rect.centerx else -1
        p2.facing = 1 if p1.rect.centerx >= p2.rect.centerx else -1

        # 入力（intent）を Player に渡す。
        p1.apply_input(
            PlayerInput(
                move_x=p1_move_x,
                jump_pressed=p1_jump_pressed,
                crouch=p1_crouch,
                attack_pressed=p1_attack_pressed,
            )
        )
        p2.apply_input(
            PlayerInput(
                move_x=p2_move_x,
                jump_pressed=p2_jump_pressed,
                crouch=p2_crouch,
                attack_pressed=p2_attack_pressed,
            )
        )

        # 物理更新。
        p1.update()
        p2.update()

        # 押し合い（Pushbox）解決。
        # Pushbox が重なったら、x方向に左右へ押し戻して重なりを解消する。
        p1_push = p1.get_pushbox()
        p2_push = p2.get_pushbox()
        if p1_push.colliderect(p2_push):
            overlap_x = min(p1_push.right - p2_push.left, p2_push.right - p1_push.left)
            if overlap_x > 0:
                push = (overlap_x + 1) // 2
                if p1.rect.centerx < p2.rect.centerx:
                    p1.rect.x -= push
                    p2.rect.x += push
                else:
                    p1.rect.x += push
                    p2.rect.x -= push

                # 押し戻し後も画面外へ出ないように補正する。
                p1.rect.left = max(0, p1.rect.left)
                p1.rect.right = min(constants.SCREEN_WIDTH, p1.rect.right)
                p2.rect.left = max(0, p2.rect.left)
                p2.rect.right = min(constants.SCREEN_WIDTH, p2.rect.right)

        # 描画。
        screen.fill(constants.COLOR_BG)

        # 地面ライン（目印）。
        pygame.draw.line(
            screen,
            (80, 80, 80),
            (0, constants.GROUND_Y),
            (constants.SCREEN_WIDTH, constants.GROUND_Y),
            2,
        )

        # キャラクター描画（内部でデバッグ枠線も描画）。
        p1.draw(screen, debug_draw=debug_draw)
        p2.draw(screen, debug_draw=debug_draw)

        pygame.display.flip()

        # FPS を固定し、1フレームあたりの挙動が安定するようにする。
        clock.tick(constants.FPS)

    # 終了処理。
    pygame.quit()


if __name__ == "__main__":
    main()
