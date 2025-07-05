import pyxel
import random
import math

# --- 定数 ---
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 200
PADDLE_WIDTH = 20  # パドルの幅を半分に変更 (40 -> 20)
PADDLE_HEIGHT = 5
PADDLE_SPEED = 2
BALL_RADIUS = 3
BLOCK_WIDTH = 16
BLOCK_HEIGHT = 8
BLOCK_COLS = 10
BLOCK_ROWS = 5
BLOCK_START_Y = 20


# --- ボールクラス ---
class Ball:
    """CPUが打ち出すボールを管理するクラス"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BALL_RADIUS
        # ボールが上方向に飛ぶように、ランダムな角度を設定
        angle = random.uniform(math.pi * 1.25, math.pi * 1.75)
        self.dx = math.cos(angle) * 2
        self.dy = math.sin(angle) * 2
        self.color = 9  # 黄色
        self.is_active = True

    def update(self):
        """ボールの位置を更新"""
        if not self.is_active:
            return

        self.x += self.dx
        self.y += self.dy

        # 壁との反射
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.dx *= -1
        if self.y <= self.radius:
            self.dy *= -1
        # 画面下は通り抜ける
        if self.y >= SCREEN_HEIGHT + self.radius:
            self.is_active = False  # 画面外に出たら非アクティブに

    def draw(self):
        """ボールを描画"""
        if self.is_active:
            pyxel.circ(self.x, self.y, self.radius, self.color)


# --- パドルクラス (動きを大幅に修正) ---
class Paddle:
    """CPUが操作するパドルを管理するクラス"""

    def __init__(self, stage):
        self.w = PADDLE_WIDTH
        self.h = PADDLE_HEIGHT
        self.x = (SCREEN_WIDTH - self.w) / 2
        self.y = SCREEN_HEIGHT - self.h - 10
        self.base_speed = PADDLE_SPEED
        # 開始時の移動方向をランダムに設定
        self.speed = random.choice([-self.base_speed, self.base_speed])
        # ステージに応じて耐久力を設定
        self.hp = 3 + (stage - 1) * 2
        self.initial_hp = self.hp
        # 停止タイマー
        self.pause_timer = 0

    def update(self):
        """パドルの位置を更新（よりランダムで予測しにくい動き）"""
        # ポーズ中の場合
        if self.pause_timer > 0:
            self.pause_timer -= 1
            # ポーズが終わったら、新しい方向へランダムに動き出す
            if self.pause_timer <= 0:
                self.speed = random.choice([-self.base_speed, self.base_speed])
            return  # ポーズ中はここで処理を終了

        # 移動
        self.x += self.speed

        # 壁に衝突したら必ず反転
        if self.x <= 0:
            self.x = 0
            self.speed = self.base_speed
        elif self.x + self.w >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.w
            self.speed = -self.base_speed

        # --- 新しいランダム性のロジック ---
        # 低い確率で（約1秒間に1回程度）、行動を変化させる
        if random.randint(0, 60) == 0:
            # 「反転」か「停止」かをランダムに選択
            action = random.choice(["reverse", "pause"])

            if action == "reverse":
                # 現在の進行方向と逆へ
                self.speed *= -1
            elif action == "pause":
                # 短時間、その場で停止する
                self.pause_timer = random.randint(15, 45)  # 0.25秒から0.75秒間

    def draw(self):
        """パドルとHPバーを描画"""
        # HPの割合に応じて色を変える
        hp_ratio = self.hp / self.initial_hp
        if hp_ratio > 0.6:
            color = 11  # 緑
        elif hp_ratio > 0.3:
            color = 10  # オレンジ
        else:
            color = 8  # 赤
        pyxel.rect(self.x, self.y, self.w, self.h, color)


# --- ブロッククラス ---
class Block:
    """画面上部に積まれるブロックを管理するクラス"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.w = BLOCK_WIDTH
        self.h = BLOCK_HEIGHT
        self.color = color
        self.is_active = True

    def draw(self):
        """アクティブなブロックを描画"""
        if self.is_active:
            pyxel.rect(self.x, self.y, self.w, self.h, self.color)
            pyxel.rectb(self.x, self.y, self.w, self.h, 1)  # 枠線


# --- 投げるブロッククラス (pyxel.bltの回転機能を使用) ---
class ThrownBlock:
    """プレイヤーが投げるブロックを管理するクラス"""

    def __init__(self, x, y, target_x, target_y, color):
        self.x = x
        self.y = y
        self.w = BLOCK_WIDTH
        self.h = BLOCK_HEIGHT
        self.color = color
        self.is_active = True

        # ターゲットへの方向ベクトルを計算
        angle = math.atan2(target_y - y, target_x - x)
        speed = 3
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

        # 回転角度を初期化
        self.rotation_angle = 0

    def update(self):
        """ブロックの位置と角度を更新"""
        self.x += self.dx
        self.y += self.dy
        # 毎フレーム角度を加算して回転させる
        self.rotation_angle += 15
        if (
            self.y > SCREEN_HEIGHT
            or self.y < -self.h
            or self.x < -self.w
            or self.x > SCREEN_WIDTH
        ):
            self.is_active = False

    def draw(self):
        """投げられたブロックを回転させながら描画"""
        if not self.is_active:
            return

        # --- ここからが変更された描画ロジック ---
        # 描画したいブロックをイメージバンク1の一時的な領域(0,0)に描画
        # (毎フレーム描画するのは非効率だが、色が異なるブロックに対応する簡単な方法)
        pyxel.images[1].cls(0)  # 透明色(0)でクリア
        pyxel.images[1].rect(0, 0, self.w, self.h, self.color)
        pyxel.images[1].rectb(0, 0, self.w, self.h, 1)  # 枠線も描画

        # bltを使って回転描画
        # (ブロックの中心を軸に回転させるため、描画位置をオフセットする)
        pyxel.blt(
            self.x,
            self.y,
            1,  # イメージバンク1を使用
            0,
            0,
            self.w,
            self.h,  # ソースの座標とサイズ
            0,  # 透明色
            rotate=self.rotation_angle,
        )
        # --- ここまでが変更された描画ロジック ---


# --- メインのAppクラス ---
class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Reverse Block Breaker", fps=60)
        pyxel.mouse(True)
        self.setup_sound()
        self.stage = 1
        self.game_state = "start"  # "start", "playing", "clear", "gameover"
        self.setup_stage()
        pyxel.run(self.update, self.draw)

    def setup_sound(self):
        """音声のセットアップ"""
        pyxel.sounds[0].set("c2c1g1c1", "t", "7", "n", 10)  # ヒット音
        pyxel.sounds[1].set("c3e3g3c4", "t", "7", "n", 15)  # クリア音
        pyxel.sounds[2].set("g2f2e2d2", "t", "7", "n", 20)  # ゲームオーバー音

    def setup_stage(self):
        """ステージの初期化"""
        self.paddle = Paddle(self.stage)
        self.max_balls = 3 + (self.stage - 1) * 2  # ステージごとの最大ボール数を設定

        self.balls = []
        # 最大ボール数で初期化
        for _ in range(self.max_balls):
            self.balls.append(Ball(self.paddle.x + self.paddle.w / 2, self.paddle.y))

        self.blocks = []
        colors = [2, 9, 10, 11, 12]
        for r in range(BLOCK_ROWS):
            for c in range(BLOCK_COLS):
                block_x = c * BLOCK_WIDTH
                block_y = r * BLOCK_HEIGHT + BLOCK_START_Y
                self.blocks.append(Block(block_x, block_y, colors[r % len(colors)]))

        self.thrown_blocks = []

    def update(self):
        """全体のゲームロジックを更新"""
        if self.game_state == "playing":
            self.update_playing()
        elif self.game_state in ["start", "clear", "gameover"]:
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                if self.game_state == "clear":
                    self.stage += 1
                else:
                    self.stage = 1
                self.game_state = "playing"
                self.setup_stage()

    def update_playing(self):
        """ゲームプレイ中の更新処理"""
        self.paddle.update()

        # ボールの更新と壁のブロックとの衝突判定
        for ball in self.balls:
            ball.update()
            if not ball.is_active:
                continue

            for block in self.blocks:
                if (
                    block.is_active
                    and ball.x + ball.radius > block.x
                    and ball.x - ball.radius < block.x + block.w
                    and ball.y + ball.radius > block.y
                    and ball.y - ball.radius < block.y + block.h
                ):
                    block.is_active = False
                    ball.dy *= -1
                    break

        # プレイヤーの入力（ブロック発射）
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            active_blocks = [b for b in self.blocks if b.is_active]
            if active_blocks:
                max_y = max(b.y for b in active_blocks)
                launchable_blocks = [b for b in active_blocks if b.y == max_y]

                if launchable_blocks:
                    block_to_throw = random.choice(launchable_blocks)
                    block_to_throw.is_active = False
                    self.thrown_blocks.append(
                        ThrownBlock(
                            block_to_throw.x,
                            block_to_throw.y,
                            pyxel.mouse_x,
                            pyxel.mouse_y,
                            block_to_throw.color,
                        )
                    )

        # 投げたブロックの更新と衝突判定
        for thrown in self.thrown_blocks:
            thrown.update()
            if not thrown.is_active:
                continue

            # パドルとの衝突判定
            # (衝突判定は回転を考慮しないAABBで行っています)
            if (
                thrown.x < self.paddle.x + self.paddle.w
                and thrown.x + thrown.w > self.paddle.x
                and thrown.y < self.paddle.y + self.paddle.h
                and thrown.y + thrown.h > self.paddle.y
            ):
                self.paddle.hp -= 1
                thrown.is_active = False
                pyxel.play(0, 0)
                continue

            # ボールとの衝突判定
            # (衝突判定は回転を考慮しないAABBで行っています)
            for ball in self.balls:
                if not ball.is_active:
                    continue

                # 矩形と円の衝突判定
                closest_x = max(thrown.x, min(ball.x, thrown.x + thrown.w))
                closest_y = max(thrown.y, min(ball.y, thrown.y + thrown.h))

                dist_x = ball.x - closest_x
                dist_y = ball.y - closest_y

                # 衝突していたら、ボールは跳ね返り、投げたブロックは消える
                if (dist_x * dist_x + dist_y * dist_y) < (ball.radius * ball.radius):
                    # ボールの反射方向を決定
                    overlap_x = (thrown.w / 2 + ball.radius) - abs(
                        ball.x - (thrown.x + thrown.w / 2)
                    )
                    overlap_y = (thrown.h / 2 + ball.radius) - abs(
                        ball.y - (thrown.y + thrown.h / 2)
                    )

                    if overlap_x >= overlap_y:
                        ball.dy *= -1
                    else:
                        ball.dx *= -1

                    thrown.is_active = False
                    pyxel.play(0, 0)  # ヒット音
                    break  # この投げブロックは消えたので、他のボールとの判定は不要

        # 非アクティブなオブジェクトをリストから削除
        self.balls = [b for b in self.balls if b.is_active]
        self.thrown_blocks = [b for b in self.thrown_blocks if b.is_active]

        # ボールが最大数より少なければ補充する
        if len(self.balls) < self.max_balls:
            self.balls.append(Ball(self.paddle.x + self.paddle.w / 2, self.paddle.y))

        # 勝利・敗北判定
        if self.paddle.hp <= 0:
            self.game_state = "clear"
            pyxel.play(0, 1)
        elif not any(b.is_active for b in self.blocks):
            self.game_state = "gameover"
            pyxel.play(0, 2)

    def draw(self):
        """全体の描画処理"""
        pyxel.cls(7)

        if self.game_state == "start":
            self.draw_title_screen("REVERSE BLOCK BREAKER", "CLICK or ENTER to START")
            return

        if self.game_state == "clear":
            self.draw_title_screen(
                f"STAGE {self.stage} CLEAR!", "CLICK or ENTER to NEXT STAGE"
            )
            return

        if self.game_state == "gameover":
            self.draw_title_screen("GAME OVER", "CLICK or ENTER to RESTART")
            return

        for block in self.blocks:
            block.draw()

        self.paddle.draw()

        for ball in self.balls:
            ball.draw()

        for thrown in self.thrown_blocks:
            thrown.draw()

        pyxel.text(5, 5, f"STAGE: {self.stage}", 0)
        pyxel.text(SCREEN_WIDTH - 60, 5, f"PADDLE HP: {max(0, self.paddle.hp)}", 0)

    def draw_title_screen(self, title, subtitle):
        """タイトルやメッセージ画面の描画"""
        pyxel.cls(1)
        title_x = (SCREEN_WIDTH - len(title) * 4) / 2
        subtitle_x = (SCREEN_WIDTH - len(subtitle) * 4) / 2
        pyxel.text(title_x, 80, title, 7)
        if pyxel.frame_count % 30 < 15:
            pyxel.text(subtitle_x, 100, subtitle, 7)


App()
