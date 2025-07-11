import random
import arcade
import math
import os
import arcade.gui

"""
Invaxians – Versão aprimorada
============================
• Sons de disparo, explosão e música de fundo (arcade.Sound)
• Dificuldade dinâmica (velocidade dos inimigos e frequência de disparo)
• Animações de explosão usando arcade.SpriteList
• Power-ups (velocidade e vida extra) liberados pelos UFOs
• Botões de Iniciar Jogo e Recomeçar
"""

# ------------------------ CONSTANTES GERAIS ------------------------
ESCALA_ESTRELA = 0.5
D_ALPHA_ESTRELA = 3
V_Y_ESTRELA = 3
QTD_ESTRELAS = 100

ESCALA_NAVE = 0.5
V_X_NAVE = 5   # velocidade padrão da nave

ESCALA_VIDA = 0.8
QTD_VIDAS = 3
DT_REVIVE = 200

ESCALA_FASE_P = 0.8
ESCALA_FASE_G = 0.9

V_Y_MISSIL = 9

ESCALA_INIMIGO = 0.4
LINS_INIMIGOS = 5
COLS_INIMIGOS = 7

V_X_INIMIGO_INI = 2    # velocidade mínima dos inimigos
V_Y_INIMIGO = 4
A_X_INIMIGO = 0.1

V_Y_INIMISSIL = 5
P_INIMISSIL_INI = 500    # probabilidade inicial de disparo (quanto menor, mais tiros)

ESCALA_UFO = 0.4
V_X_UFO = 5
P_UFO = 1000
DT_UFO = 200

# Power-ups
ESCALA_POWERUP = 0.5
DT_SPEED_BOOST = 600     # duração do aumento de velocidade da nave (quadros)

# Explosões
ESCALA_EXPLOSAO = 0.7

# Janela
LARG_TELA = 800
ALT_TELA = 600
TIT_TELA = "Invaxians"

# --- CONSTANTE ADICIONADA: MARGEM INFERIOR DA TELA ---
MARGEM_Y_TELA = 40
# -----------------------------------------------------

# Estados do jogo
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

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
        self.bottom = MARGEM_Y_TELA # <--- Usando MARGEM_Y_TELA

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
        y = (ALT_TELA - MARGEM_Y_TELA) - 1.2 * lin * self.height # <--- Usando MARGEM_Y_TELA
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
        self._frame += 0.25   # velocidade da animação
        if self._frame >= len(self.textures):
            self.remove_from_sprite_lists()
        else:
            self.texture = self.textures[int(self._frame)]


class PowerUpSprite(arcade.Sprite):
    """Power-up que cai do céu."""

    def __init__(self, tipo: str, filename, x, y):
        super().__init__(filename, ESCALA_POWERUP)
        self.tipo = tipo   # "speed" ou "life"
        self.center_x = x
        self.center_y = y
        self.change_y = -2   # cai lentamente

# ------------------------ JOGO ------------------------
class MeuJogo(arcade.Window):
    def __init__(self):
        super().__init__(LARG_TELA, ALT_TELA, TIT_TELA)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.base_path)

        # Listas de sprites - Inicialize-as SEMPRE como SpriteList vazias
        self.estrela_list = arcade.SpriteList()
        self.nave_list = arcade.SpriteList()
        self.vida_list = arcade.SpriteList()
        self.fase_list = arcade.SpriteList()
        self.missil_list = arcade.SpriteList()
        self.inimigo_list = arcade.SpriteList()
        self.inimissil_list = arcade.SpriteList()
        self.ufo_list = arcade.SpriteList()
        self.explosao_list = arcade.SpriteList()
        self.powerup_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList() # <--- NOVO: Lista para o sprite de fundo

        # Sons
        path_audio = os.path.join("spaceshooter", "Audio")
        self.snd_shot = arcade.load_sound(os.path.join(path_audio, "laser5.ogg"))
        self.snd_explosion = arcade.load_sound(os.path.join(path_audio, "explosion2.ogg"))
        try:
            self.music = arcade.load_sound(os.path.join(path_audio, "background.ogg"), streaming=True)
            self.music_player = self.music.play(volume=0.4, loop=True)
            self.music_player.pause()
        except FileNotFoundError:
            self.music_player = None

        # Texturas de explosão (pré-carregadas para performance)
        path_exp = os.path.join("spaceshooter", "PNG", "Effects")
        self.texturas_explosao = [
            arcade.load_texture(os.path.join(path_exp, f"explosion0{i}.png")) for i in range(9)
        ]

        # --- CARREGAR TEXTURAS DOS BOTÕES ---
        path_buttons = os.path.join(self.base_path, "spaceshooter", "PNG", "UI", "Buttons")
        self.use_image_buttons = True
        try:
            # Botão de Iniciar
            self.start_tex_normal = arcade.load_texture(os.path.join(path_buttons, "start_button_normal.png"))
            self.start_tex_hover = arcade.load_texture(os.path.join(path_buttons, "start_button_hover.png"))
            self.start_tex_pressed = arcade.load_texture(os.path.join(path_buttons, "start_button_pressed.png"))

            # Botão de Recomeçar
            self.restart_tex_normal = arcade.load_texture(os.path.join(path_buttons, "restart_button_normal.png"))
            self.restart_tex_hover = arcade.load_texture(os.path.join(path_buttons, "restart_button_hover.png"))
            self.restart_tex_pressed = arcade.load_texture(os.path.join(path_buttons, "restart_button_pressed.png"))

        except FileNotFoundError as e:
            print(f"Erro ao carregar textura do botão: {e}. Verifique o caminho e o nome dos arquivos.")
            print("Usando botões de texto como fallback.")
            self.use_image_buttons = False
        # --- FIM DO CARREGAMENTO DE TEXTURAS DOS BOTÕES ---

        # Estados do jogo
        self.placar = 0
        self.game_state = GAME_STATE_MENU
        self.revive = 0
        self.fase = 1
        self.bonus_ufo = 0
        self.pausado = False
        self.speed_timer = 0

        # Dificuldade dinâmica
        self.vel_inimigo_x = V_X_INIMIGO_INI
        self.p_inimissil = P_INIMISSIL_INI

        # Textos
        self.score_text = arcade.Text("0", 5, ALT_TELA - 5, arcade.color.WHITE, 20, anchor_y="top", bold=True, font_name="Courier New")
        self.game_over_text = arcade.Text(
            "GAME OVER", LARG_TELA / 2, ALT_TELA / 2 + 50,
            arcade.color.RED, 60, anchor_x="center", anchor_y="center", bold=True, font_name="Courier New"
        )
        self.pause_text = arcade.Text(
            "PAUSE", LARG_TELA / 2, ALT_TELA / 2,
            arcade.color.GREEN, 60, anchor_x="center", anchor_y="center", bold=True, font_name="Courier New"
        )
        self.title_text = arcade.Text(
            "INVAXIANS", LARG_TELA / 2, ALT_TELA / 2 + 50,
            arcade.color.YELLOW, 60, anchor_x="center", anchor_y="center", bold=True, font_name="Courier New"
        )

        # Tipos de inimigo
        self.tipo_inimigo = [f"enemyGreen{i+1}.png" for i in range(5)]

        self.set_mouse_visible(True)
        # arcade.set_background_color(arcade.color.MIDNIGHT_BLUE) # REMOVA ESTA LINHA OU COMENTE

        # Gerenciador de UI para os botões
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Botões
        self.start_button = None
        self.restart_button = None
        self.setup_buttons()

        self.set_active_buttons(GAME_STATE_MENU)

    def set_active_buttons(self, game_state):
        """Ativa/desativa os botões com base no estado do jogo."""
        self.manager.clear()

        if game_state == GAME_STATE_MENU:
            self.manager.add(self.start_button)
        elif game_state == GAME_STATE_GAME_OVER:
            self.manager.add(self.restart_button)

    def setup_buttons(self):
        """Configura os botões de iniciar e recomeçar."""
        if self.use_image_buttons:
            # Botão de Iniciar Jogo com Imagens
            self.start_button = arcade.gui.UITextureButton(
                texture=self.start_tex_normal,
                texture_hovered=self.start_tex_hover,
                texture_pressed=self.start_tex_pressed,
                center_x=LARG_TELA / 2,
                center_y=ALT_TELA / 2 - 50,
                scale=1.0
            )
            self.start_button.on_click = self.on_start_button_click

            # Botão de Recomeçar com Imagens
            self.restart_button = arcade.gui.UITextureButton(
                texture=self.restart_tex_normal,
                texture_hovered=self.restart_tex_hover,
                texture_pressed=self.restart_tex_pressed,
                center_x=LARG_TELA / 2,
                center_y=ALT_TELA / 2 - 50,
                scale=1.0
            )
            self.restart_button.on_click = self.on_restart_button_click
        else:
            # Fallback para botões de texto se as imagens não forem encontradas
            self.start_button = arcade.gui.UIFlatButton(
                text="Iniciar Jogo",
                center_x=LARG_TELA / 2,
                center_y=ALT_TELA / 2 - 50,
                width=200,
                height=50,
                style={
                    "font_size": 18,
                    "font_name": "Arial",
                    "font_color": arcade.color.WHITE,
                    "bg_color": arcade.color.DARK_GREEN,
                    "border_width": 2,
                    "border_color": arcade.color.WHITE,
                    "bg_color_pressed": arcade.color.LIGHT_GREEN,
                    "font_color_pressed": arcade.color.BLACK,
                }
            )
            self.start_button.on_click = self.on_start_button_click

            self.restart_button = arcade.gui.UIFlatButton(
                text="Recomeçar",
                center_x=LARG_TELA / 2,
                center_y=ALT_TELA / 2 - 50,
                width=200,
                height=50,
                style={
                    "font_size": 18,
                    "font_name": "Arial",
                    "font_color": arcade.color.WHITE,
                    "bg_color": arcade.color.DARK_RED,
                    "border_width": 2,
                    "border_color": arcade.color.WHITE,
                    "bg_color_pressed": arcade.color.LIGHT_RED,
                    "font_color_pressed": arcade.color.BLACK,
                }
            )
            self.restart_button.on_click = self.on_restart_button_click


    def on_start_button_click(self, event):
        """Chamado quando o botão 'Iniciar Jogo' é clicado."""
        self.game_state = GAME_STATE_PLAYING
        self.set_active_buttons(self.game_state)
        self.set_mouse_visible(False)
        self.inicia_jogo()
        if self.music_player:
            self.music_player.play()

    def on_restart_button_click(self, event):
        """Chamado quando o botão 'Recomeçar' é clicado."""
        self.game_state = GAME_STATE_PLAYING
        self.set_active_buttons(self.game_state)
        self.set_mouse_visible(False)
        self.fase = 1
        self.inicia_jogo()
        if self.music_player:
            self.music_player.play()

    # ------------------------ CONFIGURAÇÕES INICIAIS ------------------------
    def inicia_bg(self):
        """Cria as estrelas de fundo e o sprite de imagem de fundo."""
        # Limpa a lista de fundo antes de adicionar um novo sprite, caso seja chamada mais de uma vez
        self.background_list = arcade.SpriteList() 
        path_backgrounds = os.path.join("spaceshooter", "PNG", "Backgrounds")
        try:
            background_sprite = arcade.Sprite(os.path.join(path_backgrounds, "fundo_espaco.png"), scale=1.0)
            background_sprite.center_x = LARG_TELA / 2
            background_sprite.center_y = ALT_TELA / 2
            self.background_list.append(background_sprite) # <--- Adiciona o sprite à lista
        except FileNotFoundError:
            print("AVISO: Imagem de fundo 'fundo_espaco.png' não encontrada. Usando estrelas e cor de fundo padrão.")
            self.background_list = None # Se não houver imagem, define a lista como None para não tentar desenhá-la
            arcade.set_background_color(arcade.color.MIDNIGHT_BLUE) # Fallback para cor

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
        # Não reinicia self.background_list aqui, pois ele é configurado apenas uma vez no inicia_bg
        # ou se a fase reiniciar, o inicia_bg será chamado novamente para recriar as estrelas e o background.

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
        self.placar = 0
        self.score_text.text = str(self.placar)
        self.revive = 0
        self.bonus_ufo = 0
        self.speed_timer = 0
        self.pausado = False

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
        # --- Desenha a lista de fundo primeiro ---
        if self.background_list: # Verifica se a lista não é None (em caso de erro de carregamento)
            self.background_list.draw()
        # --- Fim da lista de fundo ---

        self.estrela_list.draw()

        if self.game_state == GAME_STATE_MENU:
            self.title_text.draw()
        elif self.game_state == GAME_STATE_PLAYING:
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
            if self.pausado:
                self.pause_text.draw()
        elif self.game_state == GAME_STATE_GAME_OVER:
            self.game_over_text.draw()
            self.score_text.draw()

        self.manager.draw()

    # ------------------------ UPDATE ------------------------
    def on_update(self, delta_time: float):
        self.estrela_list.update()

        if self.game_state == GAME_STATE_PLAYING and not self.pausado:
            # Atualizar listas
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
                    if self.nave_list:
                        self.nave_list[0].alpha = 255

            # Timer de bônus do UFO
            if self.bonus_ufo:
                self.bonus_ufo += 1
                if self.bonus_ufo >= DT_UFO:
                    self.bonus_ufo = 0

            # ----- Colisões dos mísseis do jogador -----
            for missil in self.missil_list:
                inimigos_hit = arcade.check_for_collision_with_list(missil, self.inimigo_list)
                if inimigos_hit:
                    missil.remove_from_sprite_lists()
                    for inimigo in inimigos_hit:
                        self.cria_explosao(inimigo.center_x, inimigo.center_y)
                        inimigo.remove_from_sprite_lists()
                        self.placar += 1
                inimissil_hit = arcade.check_for_collision_with_list(missil, self.inimissil_list)
                if inimissil_hit:
                    missil.remove_from_sprite_lists()
                    for im in inimissil_hit:
                        self.cria_explosao(im.center_x, im.center_y)
                        im.remove_from_sprite_lists()
                ufo_hit_this_frame = arcade.check_for_collision_with_list(missil, self.ufo_list)
                if ufo_hit_this_frame:
                    missil.remove_from_sprite_lists()
                    for ufo in ufo_hit_this_frame:
                        if ufo in self.ufo_list:
                            self.cria_explosao(ufo.center_x, ufo.center_y)
                            self.cria_powerup(ufo.center_x, ufo.center_y)
                            ufo.remove_from_sprite_lists()
                if missil.bottom > ALT_TELA:
                    missil.remove_from_sprite_lists()

            # ----- Colisões dos mísseis inimigos -----
            for inimissil in self.inimissil_list:
                if self.nave_list and self.revive == 0 and arcade.check_for_collision_with_list(inimissil, self.nave_list):
                    self.cria_explosao(inimissil.center_x, inimissil.center_y)
                    inimissil.remove_from_sprite_lists()
                    if self.vida_list:
                        self.revive = 1
                        self.nave_list[0].alpha = 64
                        vida = self.vida_list.pop()
                        vida.remove_from_sprite_lists()
                    else:
                        self.game_state = GAME_STATE_GAME_OVER
                        self.set_mouse_visible(True)
                        self.set_active_buttons(self.game_state)
                        if self.music_player:
                            self.music_player.pause()
                if inimissil.top < 0:
                    inimissil.remove_from_sprite_lists()

            # ----- Power-ups -----
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
            if self.nave_list and arcade.check_for_collision_with_list(self.nave_list[0], self.inimigo_list):
                self.game_state = GAME_STATE_GAME_OVER
                self.set_mouse_visible(True)
                self.set_active_buttons(self.game_state)
                if self.music_player:
                    self.music_player.pause()

            # ----- Movimento dos inimigos e direção -----
            if self.inimigo_list:
                x_min = min([inimigo.left for inimigo in self.inimigo_list])
                x_max = max([inimigo.right for inimigo in self.inimigo_list])
                if x_min < 0 or x_max > LARG_TELA:
                    for inimigo in self.inimigo_list:
                        inimigo.change_x = -inimigo.change_x
                        if abs(inimigo.change_x) < self.vel_inimigo_x * 2:
                            inimigo.change_x += math.copysign(A_X_INIMIGO, inimigo.change_x)
                        inimigo.center_y -= V_Y_INIMIGO
            else:
                x_min = 0
                x_max = 0

            # ----- Inimigos atirando -----
            for inimigo in self.inimigo_list:
                if random.randrange(self.p_inimissil) == 0:
                    path_laser = os.path.join("spaceshooter", "PNG", "Lasers")
                    inimissil = InimissilSprite(os.path.join(path_laser, "laserGreen04.png"), inimigo)
                    self.inimissil_list.append(inimissil)

            # ----- Criação de UFO -----
            if not self.ufo_list and random.randrange(P_UFO) == 0:
                path_png = os.path.join("spaceshooter", "PNG")
                ufo = arcade.Sprite(os.path.join(path_png, "ufoBlue.png"), ESCALA_UFO)
                if random.random() < 0.5:
                    ufo.change_x = V_X_UFO
                    ufo.left = -ufo.width
                else:
                    ufo.change_x = -V_X_UFO
                    ufo.right = LARG_TELA + ufo.width
                ufo.top = ALT_TELA - 50
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
        if self.game_state == GAME_STATE_MENU:
            if key == arcade.key.SPACE:
                self.on_start_button_click(None)
            return
        elif self.game_state == GAME_STATE_GAME_OVER:
            if key == arcade.key.SPACE:
                self.on_restart_button_click(None)
            return

        if not self.nave_list:
            return

        nave = self.nave_list[0]
        velocidade = self.atualiza_velocidade_nave()

        if key == arcade.key.P:
            self.pausado = not self.pausado
            if self.music_player:
                if self.pausado:
                    self.music_player.pause()
                else:
                    self.music_player.play()
        elif key == arcade.key.LEFT:
            nave.change_x = -velocidade
        elif key == arcade.key.RIGHT:
            nave.change_x = velocidade
        elif key == arcade.key.SPACE and not self.pausado:
            if self.bonus_ufo or not self.missil_list:
                path_laser = os.path.join("spaceshooter", "PNG", "Lasers")
                missil = MissilSprite(os.path.join(path_laser, "laserRed01.png"), nave)
                self.missil_list.append(missil)
                arcade.play_sound(self.snd_shot)

    def on_key_release(self, key, modifiers):
        if self.game_state != GAME_STATE_PLAYING or not self.nave_list:
            return

        nave = self.nave_list[0]
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            nave.change_x = 0

# ------------------------ MAIN ------------------------

def main():
    window = MeuJogo()
    window.inicia_bg() # Chama para carregar as estrelas e o background
    arcade.run()


if __name__ == "__main__":
    main()