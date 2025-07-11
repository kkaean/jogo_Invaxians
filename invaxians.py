import random
import arcade
import math
import os

"""
Invaxians – Versão aprimorada
============================
• Sons de disparo, explosão e música de fundo (arcade.Sound)
• Dificuldade dinâmica (velocidade dos inimigos e frequência de disparo)
• Animações de explosão usando arcade.SpriteList
• Power‑ups (velocidade e vida extra) liberados pelos UFOs
"""

# ------------------------ CONSTANTES GERAIS ------------------------
ESCALA_ESTRELA = 0.5
D_ALPHA_ESTRELA = 3
V_Y_ESTRELA = 3
QTD_ESTRELAS = 100

ESCALA_NAVE = 0.5
V_X_NAVE = 5  # velocidade padrão da nave

ESCALA_VIDA = 0.8
QTD_VIDAS = 3
DT_REVIVE = 200

ESCALA_FASE_P = 0.8
ESCALA_FASE_G = 0.9

V_Y_MISSIL = 9

ESCALA_INIMIGO = 0.4
LINS_INIMIGOS = 5
COLS_INIMIGOS = 7

V_X_INIMIGO_INI = 2   # velocidade mínima dos inimigos
V_Y_INIMIGO = 4
A_X_INIMIGO = 0.1

V_Y_INIMISSIL = 5
P_INIMISSIL_INI = 500   # probabilidade inicial de disparo (quanto menor, mais tiros)

ESCALA_UFO = 0.4
V_X_UFO = 5
P_UFO = 1000
DT_UFO = 200

# Power-ups
ESCALA_POWERUP = 0.5
DT_SPEED_BOOST = 600  # duração do aumento de velocidade da nave (quadros)

# Explosões
ESCALA_EXPLOSAO = 0.7

# Janela
LARG_TELA = 800
ALT_TELA = 600
MARGEM_Y_TELA = 25
TIT_TELA = "Invaxians"

# ------------------------ SPRITES AUXILIARES ------------------------
class EstrelaSprite(arcade.Sprite):
    """Estrelas de fundo que piscam e descem."""

    def __init__(self, filename):
        escala = random.uniform(0.6, 1.0) * ESCALA_ESTRELA
        super().__init__(filename, escala)
        self.center_x = random.randint(0, LARG_TELA)
        self.center_y = random.randint(0, ALT_TELA)
        self.alpha = random.randint(0, 255)
        self.d_alpha = random.randint(1, D_ALPHA_ESTRELA)
        self.change_y = -random.randint(1, V_Y_ESTRELA)

    def update(self, delta_time: float = 1 / 60):
        self.alpha += self.d_alpha
        if self.alpha < 0 or self.alpha > 255:
            self.d_alpha *= -1
            self.alpha += self.d_alpha
        if self.center_y < 0:
            self.center_y = ALT_TELA
            self.change_y = -random.randint(1, V_Y_ESTRELA)
        super().update()


class NaveSprite(arcade.Sprite):
    """Nave controlada pelo jogador."""

    def __init__(self, filename):
        super().__init__(filename, ESCALA_NAVE)
        self.center_x = LARG_TELA / 2
        self.bottom = MARGEM_Y_TELA

    def update(self, delta_time: float = 1 / 60):
        if self.left < 0:
            self.left = 0
        elif self.right > LARG_TELA - 1:
            self.right = LARG_TELA - 1
        super().update()


class MissilSprite(arcade.Sprite):
    """Míssil disparado pela nave."""

    def __init__(self, filename, nave):
        super().__init__(filename, ESCALA_NAVE)
        self.change_y = V_Y_MISSIL
        self.center_x = nave.center_x
        self.bottom = nave.top


class InimigoSprite(arcade.Sprite):
    """Inimigo base."""

    def __init__(self, filename, col, lin, vel_x):
        super().__init__(filename, ESCALA_INIMIGO)
        i = col - COLS_INIMIGOS / 2
        x = LARG_TELA / 2 + 1.2 * i * self.width
        y = (ALT_TELA - MARGEM_Y_TELA) - 1.2 * lin * self.height
        self.center_x = x
        self.top = y
        self.change_x = vel_x


class InimissilSprite(arcade.Sprite):
    """Míssil disparado por inimigos."""

    def __init__(self, filename, inimigo):
        super().__init__(filename, ESCALA_INIMIGO)
        self.change_y = -V_Y_INIMISSIL
        self.center_x = inimigo.center_x
        self.top = inimigo.bottom
        self.angle = 180


class ExplosionSprite(arcade.Sprite):
    """Sprite animado para explosões."""

    def __init__(self, center_x, center_y, textures):
        super().__init__(scale=ESCALA_EXPLOSAO)
        self.textures = textures
        self.texture = self.textures[0]
        self.center_x = center_x
        self.center_y = center_y
        self._frame = 0.0

    def update(self, delta_time: float = 1 / 60):
        self._frame += 0.25  # velocidade da animação
        if self._frame >= len(self.textures):
            self.remove_from_sprite_lists()
        else:
            self.texture = self.textures[int(self._frame)]


class PowerUpSprite(arcade.Sprite):
    """Power-up que cai do céu."""

    def __init__(self, tipo: str, filename, x, y):
        super().__init__(filename, ESCALA_POWERUP)
        self.tipo = tipo  # "speed" ou "life"
        self.center_x = x
        self.center_y = y
        self.change_y = -2  # cai lentamente

# ------------------------ JOGO ------------------------
class MeuJogo(arcade.Window):
    def __init__(self):
        super().__init__(LARG_TELA, ALT_TELA, TIT_TELA)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.base_path)

        # Listas de sprites
        self.estrela_list: arcade.SpriteList | None = None
        self.nave_list: arcade.SpriteList | None = None
        self.vida_list: arcade.SpriteList | None = None
        self.fase_list: arcade.SpriteList | None = None
        self.missil_list: arcade.SpriteList | None = None
        self.inimigo_list: arcade.SpriteList | None = None
        self.inimissil_list: arcade.SpriteList | None = None
        self.ufo_list: arcade.SpriteList | None = None
        self.explosao_list: arcade.SpriteList | None = None
        self.powerup_list: arcade.SpriteList | None = None

        # Sons
        path_audio = os.path.join("spaceshooter", "Audio")
        self.snd_shot = arcade.load_sound(os.path.join(path_audio, "laser5.ogg"))
        self.snd_explosion = arcade.load_sound(os.path.join(path_audio, "explosion2.ogg"))
        try:
            self.music = arcade.load_sound(os.path.join(path_audio, "background.ogg"), streaming=True)
            # A correção está aqui: Inicia a reprodução e depois define a propriedade loop.
            self.music_player = self.music.play(volume=0.4)
            self.music_player.loop = True
        except FileNotFoundError:
            self.music_player = None  # Música opcional

        # Texturas de explosão (pré-carregadas para performance)
        path_exp = os.path.join("spaceshooter", "PNG", "Effects")
        self.texturas_explosao = [
            arcade.load_texture(os.path.join(path_exp, f"explosion0{i}.png")) for i in range(9)
        ]

        # Estados do jogo
        self.placar = 0
        self.game_over = False
        self.revive = 0
        self.fase = 1
        self.bonus_ufo = 0
        self.pausado = False
        self.speed_timer = 0  # contagem regressiva para boost de velocidade

        # Dificuldade dinâmica
        self.vel_inimigo_x = V_X_INIMIGO_INI
        self.p_inimissil = P_INIMISSIL_INI

        # Textos
        self.score_text: arcade.Text | None = None
        self.game_over_text: arcade.Text | None = None
        self.pause_text: arcade.Text | None = None

        # Tipos de inimigo
        self.tipo_inimigo = [f"enemyGreen{i+1}.png" for i in range(5)]

        self.set_mouse_visible(False)
        arcade.set_background_color(arcade.color.MIDNIGHT_BLUE)

    # ------------------------ CONFIGURAÇÕES INICIAIS ------------------------
    def inicia_bg(self):
        """Cria as estrelas de fundo."""
        self.estrela_list = arcade.SpriteList()
        path_efeitos = os.path.join("spaceshooter", "PNG", "Effects")
        for _ in range(QTD_ESTRELAS):
            estrela = EstrelaSprite(os.path.join(path_efeitos, "star1.png"))
            self.estrela_list.append(estrela)

    def atualiza_dificuldade(self):
        """Ajusta dificuldade com base na fase atual."""
        self.vel_inimigo_x = V_X_INIMIGO_INI + 0.4 * (self.fase - 1)
        self.p_inimissil = max(P_INIMISSIL_INI - 30 * (self.fase - 1), 50)

    def inicia_jogo(self):
        """Reinicia / inicia a fase."""
        # SpriteLists
        self.nave_list = arcade.SpriteList()
        self.vida_list = arcade.SpriteList()
        self.fase_list = arcade.SpriteList()
        self.missil_list = arcade.SpriteList()
        self.inimigo_list = arcade.SpriteList()
        self.inimissil_list = arcade.SpriteList()
        self.ufo_list = arcade.SpriteList()
        self.explosao_list = arcade.SpriteList()
        self.powerup_list = arcade.SpriteList()

        # Dificuldade
        self.atualiza_dificuldade()

        # Nave do jogador
        path_png = os.path.join("spaceshooter", "PNG")
        nave = NaveSprite(os.path.join(path_png, "playerShip2_red.png"))
        self.nave_list.append(nave)

        # Indicadores de vida
        path_ui = os.path.join(path_png, "UI")
        for i in range(QTD_VIDAS):
            vida = arcade.Sprite(os.path.join(path_ui, "playerLife2_red.png"), ESCALA_VIDA)
            vida.left = 1.2 * i * vida.width
            vida.bottom = 0
            self.vida_list.append(vida)

        # Indicadores de fase
        path_pu = os.path.join(path_png, "Power-ups")
        n_fase_g = self.fase // 5
        n_fase_p = self.fase % 5
        j = 0
        for _ in range(n_fase_g):
            fase = arcade.Sprite(os.path.join(path_pu, "star_gold.png"), ESCALA_FASE_G)
            fase.right = LARG_TELA - 1.2 * j * fase.width
            fase.bottom = 0
            self.fase_list.append(fase)
            j += 1
        for _ in range(n_fase_p):
            fase = arcade.Sprite(os.path.join(path_pu, "star_bronze.png"), ESCALA_FASE_P)
            fase.right = LARG_TELA - 1.2 * j * fase.width
            fase.bottom = 0
            self.fase_list.append(fase)
            j += 1

        # Inimigos
        path_enemies = os.path.join(path_png, "Enemies")
        for lin in range(LINS_INIMIGOS):
            for col in range(COLS_INIMIGOS):
                tipo = lin % len(self.tipo_inimigo)
                inimigo = InimigoSprite(os.path.join(path_enemies, self.tipo_inimigo[tipo]), col, lin, self.vel_inimigo_x)
                self.inimigo_list.append(inimigo)

        # Textos fixos
        self.score_text = arcade.Text("0", 5, ALT_TELA - 5, arcade.color.WHITE, 20, anchor_y="top", bold=True, font_name="Courier New")
        self.game_over_text = arcade.Text(
            "GAME OVER", LARG_TELA / 2, ALT_TELA / 2,
            arcade.color.RED, 60, anchor_x="center", anchor_y="center", bold=True, font_name="Courier New"
        )
        self.pause_text = arcade.Text(
            "PAUSE", LARG_TELA / 2, ALT_TELA / 2,
            arcade.color.GREEN, 60, anchor_x="center", anchor_y="center", bold=True, font_name="Courier New"
        )

        self.placar = 0
        self.game_over = False
        self.revive = 0
        self.bonus_ufo = 0
        self.speed_timer = 0

    # ------------------------ MÉTODOS DE SUPORTE ------------------------
    def cria_explosao(self, x, y):
        explosao = ExplosionSprite(x, y, self.texturas_explosao)
        self.explosao_list.append(explosao)
        arcade.play_sound(self.snd_explosion)

    def cria_powerup(self, x, y):
        path_pu = os.path.join("spaceshooter", "PNG", "Power-ups")
        if random.random() < 0.5:
            # Aumento de velocidade
            power = PowerUpSprite("speed", os.path.join(path_pu, "bolt_gold.png"), x, y)
        else:
            # Vida extra
            power = PowerUpSprite("life", os.path.join(path_pu, "shield_bronze.png"), x, y)
        self.powerup_list.append(power)

    def atualiza_velocidade_nave(self):
        """Atualiza a velocidade da nave de acordo com power-up."""
        if self.speed_timer > 0:
            self.speed_timer -= 1
            return V_X_NAVE * 1.8
        return V_X_NAVE

    # ------------------------ DRAW ------------------------
    def on_draw(self):
        self.clear()
        self.estrela_list.draw()
        self.nave_list.draw()
        self.vida_list.draw()
        self.fase_list.draw()
        self.missil_list.draw()
        self.inimigo_list.draw()
        self.inimissil_list.draw()
        self.ufo_list.draw()
        self.explosao_list.draw()
        self.powerup_list.draw()
        self.score_text.draw()
        if self.game_over:
            self.game_over_text.draw()
        if self.pausado:
            self.pause_text.draw()

    # ------------------------ UPDATE ------------------------
    def on_update(self, delta_time: float):
        if self.pausado or self.game_over:
            return

        # Atualizar listas
        self.estrela_list.update()
        self.nave_list.update()
        self.missil_list.update()
        self.inimigo_list.update()
        self.inimissil_list.update()
        self.ufo_list.update()
        self.explosao_list.update()
        self.powerup_list.update()

        # Timer de invencibilidade
        if self.revive:
            self.revive += 1
            if self.revive >= DT_REVIVE:
                self.revive = 0
                self.nave_list[0].alpha = 255

        # Timer de bônus do UFO (para disparo duplo)
        if self.bonus_ufo:
            self.bonus_ufo += 1
            if self.bonus_ufo >= DT_UFO:
                self.bonus_ufo = 0

        # ----- Colisões dos mísseis do jogador -----
        for missil in self.missil_list:
            # Contra inimigos
            inimigos_hit = arcade.check_for_collision_with_list(missil, self.inimigo_list)
            if inimigos_hit:
                missil.remove_from_sprite_lists()
                for inimigo in inimigos_hit:
                    self.cria_explosao(inimigo.center_x, inimigo.center_y)
                    inimigo.remove_from_sprite_lists()
                    self.placar += 1
            # Contra inimísseis
            inimissil_hit = arcade.check_for_collision_with_list(missil, self.inimissil_list)
            if inimissil_hit:
                missil.remove_from_sprite_lists()
                for im in inimissil_hit:
                    self.cria_explosao(im.center_x, im.center_y)
                    im.remove_from_sprite_lists()
            # Contra UFO
            ufo_hit = arcade.check_for_collision_with_list(missil, self.ufo_list)
            if ufo_hit:
                missil.remove_from_sprite_lists()
                for ufo in ufo_hit:
                    self.cria_explosao(ufo.center_x, ufo.center_y)
                    self.cria_powerup(ufo.center_x, ufo.center_y)
                    ufo.remove_from_sprite_lists()
            # Fora da tela
            if missil.bottom > ALT_TELA:
                missil.remove_from_sprite_lists()

        # ----- Colisões dos mísseis inimigos -----
        for inimissil in self.inimissil_list:
            if self.revive == 0 and arcade.check_for_collision_with_list(inimissil, self.nave_list):
                self.cria_explosao(inimissil.center_x, inimissil.center_y)
                inimissil.remove_from_sprite_lists()
                if self.vida_list:
                    self.revive = 1
                    self.nave_list[0].alpha = 64
                    vida = self.vida_list.pop()
                    vida.remove_from_sprite_lists()
                else:
                    self.game_over = True
            if inimissil.top < 0:
                inimissil.remove_from_sprite_lists()

        # ----- Power-ups -----
        # É importante garantir que self.nave_list[0] exista antes de tentar acessá-lo.
        if self.nave_list:
            for power in arcade.check_for_collision_with_list(self.nave_list[0], self.powerup_list):
                if power.tipo == "speed":
                    self.speed_timer = DT_SPEED_BOOST
                elif power.tipo == "life" and len(self.vida_list) < 5:
                    path_ui = os.path.join("spaceshooter", "PNG", "UI")
                    vida = arcade.Sprite(os.path.join(path_ui, "playerLife2_red.png"), ESCALA_VIDA)
                    vida.left = 1.2 * len(self.vida_list) * vida.width
                    vida.bottom = 0
                    self.vida_list.append(vida)
                power.remove_from_sprite_lists()

        # ----- Colisão nave / inimigos -----
        # Verifique se a nave existe antes da colisão.
        if self.nave_list and arcade.check_for_collision_with_list(self.nave_list[0], self.inimigo_list):
            self.game_over = True

        # ----- Movimento dos inimigos e direção -----
        if self.inimigo_list:  # Só calcula min/max se houver inimigos
            x_min = min([inimigo.left for inimigo in self.inimigo_list])
            x_max = max([inimigo.right for inimigo in self.inimigo_list])
            if x_min < 0 or x_max > LARG_TELA:
                for inimigo in self.inimigo_list:
                    # Ajuste para garantir que a mudança de direção aconteça e a velocidade acelere.
                    inimigo.change_x = -inimigo.change_x
                    if abs(inimigo.change_x) < self.vel_inimigo_x * 2: # Evita aceleração infinita
                        inimigo.change_x += math.copysign(A_X_INIMIGO, inimigo.change_x)
                    inimigo.center_y -= V_Y_INIMIGO
        else: # Se não há inimigos, não há movimento a ser calculado
            x_min = 0
            x_max = 0

        # ----- Inimigos atirando -----
        for inimigo in self.inimigo_list:
            if random.randrange(self.p_inimissil) == 0:
                path_laser = os.path.join("spaceshooter", "PNG", "Lasers")
                inimissil = InimissilSprite(os.path.join(path_laser, "laserGreen04.png"), inimigo)
                self.inimissil_list.append(inimissil)

        # ----- Criação de UFO -----
        # Garante que apenas um UFO esteja na tela por vez, se desejado, ou ajuste a lógica.
        if not self.ufo_list and random.randrange(P_UFO) == 0:
            path_png = os.path.join("spaceshooter", "PNG")
            ufo = arcade.Sprite(os.path.join(path_png, "ufoBlue.png"), ESCALA_UFO)
            # Determina de qual lado o UFO virá
            if random.random() < 0.5:
                ufo.change_x = V_X_UFO
                ufo.left = -ufo.width
            else:
                ufo.change_x = -V_X_UFO
                ufo.right = LARG_TELA + ufo.width
            ufo.top = ALT_TELA - 50 # Posição mais baixa para o UFO
            self.ufo_list.append(ufo)

        for ufo in self.ufo_list:
            if (ufo.left >= LARG_TELA and ufo.change_x > 0) or \
               (ufo.right <= 0 and ufo.change_x < 0):
                ufo.remove_from_sprite_lists()

        # ----- Próxima fase -----
        if not self.inimigo_list:
            self.fase += 1
            self.inicia_jogo()

        # Atualiza HUD
        self.score_text.text = str(self.placar)

    # ------------------------ INPUT ------------------------
    def on_key_press(self, key, modifiers):
        # Verifica se a lista de nave não está vazia antes de tentar acessar o elemento 0
        if not self.nave_list:
            return

        nave = self.nave_list[0]
        velocidade = self.atualiza_velocidade_nave()

        if key == arcade.key.P:
            self.pausado = not self.pausado
        elif key == arcade.key.LEFT:
            nave.change_x = -velocidade
        elif key == arcade.key.RIGHT:
            nave.change_x = velocidade
        elif key == arcade.key.SPACE:
            # Disparo ou reinício do jogo
            if self.game_over:
                self.fase = 1
                self.inicia_jogo()
            else:
                # Permite disparo duplo se bonus_ufo estiver ativo, ou um único tiro se não houver mísseis
                if self.bonus_ufo or not self.missil_list:
                    path_laser = os.path.join("spaceshooter", "PNG", "Lasers")
                    missil = MissilSprite(os.path.join(path_laser, "laserRed01.png"), nave)
                    self.missil_list.append(missil)
                    arcade.play_sound(self.snd_shot)

    def on_key_release(self, key, modifiers):
        if not self.nave_list:
            return

        nave = self.nave_list[0]
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            nave.change_x = 0

# ------------------------ MAIN ------------------------

def main():
    window = MeuJogo()
    window.inicia_bg()
    window.inicia_jogo()
    arcade.run()


if __name__ == "__main__":
    main()