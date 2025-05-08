import pygame
import sys
import requests
import random

# --- Settings ---
TILE = 32
W, H = 640, 480
FPS = 60

# --- Narrative classes ---
class SceneNode:
    def __init__(self, text, choices=None, effect=None):
        self.text = text
        self.choices = choices or []
        self.effect = effect

# LLaMA interaction via requests
def get_npc_response(prompt):
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=20
        )
        if res.ok:
            return res.json().get("response", "").strip()
    except Exception as e:
        print(f"Errore nella comunicazione con Ollama: {e}")
    return "Non riesco a rispondere al momento."

# --- Story graph ---
def build_story():
    s = {}
    s['risveglio'] = SceneNode(
        "Ti svegli. Cosa fai?",
        [('Vai in ufficio', 'ufficio_setup'), ('Rimani a casa', 'casa')]
    )
    s['ufficio'] = SceneNode(
        "Sei in ufficio da TuckerSoft.",
        [('Accetta il contratto', 'finale1'), ('Rifiuta l\'offerta', 'rifuto_offerta')]
    )
    s['casa'] = SceneNode(
        "Sei a casa.",
        [('Parla con il padre', 'padre'), ('Taci', 'sogni')]
    )
    s['ufficio_setup'] = SceneNode("")
    s['tetto'] = SceneNode("")
    s['rifuto_offerta'] = SceneNode(
        "Torna a casa per lavorare in autonomia.",
        [('Continua', 'ritorno_casa')]
    )
    s['padre'] = SceneNode(
        "",
        [('Ricordi distorti sulla madre', 'ricordi'), ('Appare la voce: Distruggi il computer', 'distruggi')],
        effect=lambda: get_npc_response("Il giocatore incontra Padre. Cosa dice l'NPC?")
    )
    s['ricordi'] = SceneNode("I ricordi sulla madre sono distorti.", [('Prosegui', 'ritorno')])
    s['distruggi'] = SceneNode("Una voce ti ordina: Distruggi il computer.", [('Distruggi', 'finale5')])
    s['sogni'] = SceneNode("Inizi a sognare incubi ricorrenti.", [('Continua', 'ritorno')])
    s['ritorno'] = SceneNode("Il codice si modifica da solo e il libro cambia.", [('Prosegui', 'colin')])
    s['ritorno_casa'] = SceneNode("Sei di nuovo a casa.", [('Prosegui', 'colin')])
    s['colin'] = SceneNode(
        "",
        [('Segui Colin sul tetto', 'tetto_setup'), ('Non lo segui', 'gioco')],
        effect=lambda: get_npc_response("Il giocatore incontra Colin. Cosa dice l'NPC?")
    )
    s['tetto_setup'] = SceneNode("")
    s['tetto'] = SceneNode(
        "Sei sul tetto con Colin.",
        [('Salta tu', 'finale2'), ('Salto io', 'salto')]
    )
    s['salto'] = SceneNode("Colin sparisce, realtà alterata.", [('Continua', 'controllo')])
    s['gioco'] = SceneNode("Il gioco prende controllo della tastiera.", [('Resisti', 'controllo')])
    s['controllo'] = SceneNode("Sei osservato da Netflix/Futura.", [('Accetta la verità', 'consapevolezza')])
    s['consapevolezza'] = SceneNode(
        "Capisci di essere in un gioco.",
        [('Uccidi il padre', 'finale3'), ('Completa il gioco', 'finale4')]
    )
    finales = {
        'finale1': 'Finale: Fallimento commerciale.',
        'finale2': 'Finale: Loop mentale.',
        'finale3': 'Finale: Omicidio del padre.',
        'finale4': 'Finale: Libertà ottenuta.',
        'finale5': 'Finale segreto: Consapevolezza.'
    }
    for key, text in finales.items():
        s[key] = SceneNode(text)
    return s

# --- Map loaders ---
def load_house():
    walls = []
    houses = [(5,3,4,3), (12,8,3,4)]
    for hx, hy, hw, hh in houses:
        for i in range(hw):
            for j in range(hh):
                walls.append(pygame.Rect((hx+i)*TILE, (hy+j)*TILE, TILE, TILE))
    triggers = {
        'risveglio': pygame.Rect(3*TILE, 2*TILE, TILE, TILE),
        'padre':     pygame.Rect(4*TILE, 10*TILE, TILE, TILE),
        'colin':     pygame.Rect(6*TILE, 8*TILE, TILE, TILE)
    }
    return walls, triggers

def load_office():
    walls = []
    desks = [(3,3,1,2), (6,2,2,1), (10,4,3,1)]
    for dx, dy, dw, dh in desks:
        for i in range(dw):
            for j in range(dh):
                walls.append(pygame.Rect((dx+i)*TILE, (dy+j)*TILE, TILE, TILE))
    triggers = {'ufficio': pygame.Rect(8*TILE, 2*TILE, TILE, TILE)}
    return walls, triggers

def load_rooftop():
    walls = []
    for i in range(0, W, TILE):
        walls.append(pygame.Rect(i, 0, TILE, TILE))
        walls.append(pygame.Rect(i, 5*TILE, TILE, TILE))
    for j in range(0, 6*TILE, TILE):
        walls.append(pygame.Rect(0, j, TILE, TILE))
        walls.append(pygame.Rect(10*TILE, j, TILE, TILE))
    triggers = {'tetto': pygame.Rect(5*TILE, 5*TILE, TILE, TILE)}
    return walls, triggers

# --- NPC class ---
class NPC:
    def __init__(self, name, img, x, y, roam_rect=None):
        self.name = name
        self.img = img
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.roam = roam_rect
        self.cooldown = 0

    def update(self, walls):
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        if self.roam and random.random() < 0.02:
            dx, dy = random.choice([(TILE,0),(-TILE,0),(0,TILE),(0,-TILE),(0,0)])
            newpos = self.rect.move(dx, dy)
            if self.roam.contains(newpos) and not any(newpos.colliderect(w) for w in walls):
                self.rect = newpos
                self.cooldown = 20

    def draw(self, surf):
        surf.blit(self.img, self.rect.topleft)

    def try_talk(self, player_rect):
        if self.rect.colliderect(player_rect):
            return get_npc_response(f"Il giocatore incontra {self.name}. Cosa dice l'NPC?")
        return None

# --- Game setup ---
pygame.init()
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 24)

player_img = pygame.transform.scale(pygame.image.load('player.png'), (TILE, TILE))
wall_img   = pygame.transform.scale(pygame.image.load('house.png'), (TILE, TILE))
npc_img    = pygame.transform.scale(pygame.image.load('npc.png'), (TILE, TILE))

def setup_npcs(map_name):
    npcs = []
    if map_name == 'house':
        npcs.append(NPC("Padre", npc_img, 4*TILE, 10*TILE))
    elif map_name == 'roof':
        npcs.append(NPC("Colin", npc_img, 5*TILE, 5*TILE))
    return npcs

story = build_story()
mode = 'world'
current_scene = None
current_map = 'house'
walls, triggers = load_house()
npcs = setup_npcs(current_map)
player = pygame.Rect(2*TILE, 2*TILE, TILE, TILE)
history = []

# --- Narrative drawing ---
def draw_scene_text(key):
    global current_scene, mode, current_map, walls, triggers, npcs
    if key == 'ufficio_setup':
        current_map = 'office'
        walls, triggers = load_office()
        npcs = setup_npcs(current_map)
        key = 'ufficio'
    elif key == 'tetto_setup':
        current_map = 'roof'
        walls, triggers = load_rooftop()
        npcs = setup_npcs(current_map)
        key = 'tetto'
    elif key == 'rifuto_offerta':
        current_map = 'house'
        walls, triggers = load_house()
        npcs = setup_npcs(current_map)
        key = 'rifuto_offerta'
    current_scene = key
    node = story[current_scene]
    if node.effect:
        npc_text = node.effect()
    node.text = npc_text + "\n\n" + "Cosa vuoi fare adesso?"

    history.append(current_scene)
    mode = 'finale' if current_scene.startswith('finale') else 'narrative'

def draw_text_box():
    node = story[current_scene]
    box = pygame.Surface((W, 200)); box.set_alpha(220); box.fill((0,0,0))
    screen.blit(box, (0, H-200))
    words = node.text.split(' ')
    lines, cur = [], ''
    for w in words:
        test = f"{cur} {w}".strip()
        if FONT.size(test)[0] < W-40:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    for i, line in enumerate(lines):
        screen.blit(FONT.render(line, True, (255,255,255)), (20, H-180 + i*30))
    for i, (lbl, _) in enumerate(node.choices):
        screen.blit(FONT.render(f"{i+1}. {lbl}", True, (200,200,100)), (40, H-100 + i*30))

# --- Main loop ---
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if mode == 'world' and e.type == pygame.KEYDOWN:
            dx = (e.key == pygame.K_RIGHT and TILE) - (e.key == pygame.K_LEFT and TILE)
            dy = (e.key == pygame.K_DOWN and TILE) - (e.key == pygame.K_UP and TILE)
            if dx or dy:
                newp = player.move(dx, dy)
                if not any(newp.colliderect(w) for w in walls):
                    player = newp
            if e.key == pygame.K_SPACE:
                interacted = False
                for npc in npcs:
                    resp = npc.try_talk(player)
                    if resp:
                        story_key = npc.name.lower()
                        draw_scene_text(story_key)
                        interacted = True
                        break
                if not interacted:
                    for trg, rect in triggers.items():
                        if player.colliderect(rect):
                            draw_scene_text(trg)
                            break
        elif mode == 'narrative' and e.type == pygame.KEYDOWN:
            if pygame.K_1 <= e.key <= pygame.K_9:
                idx = e.key - pygame.K_1
                node = story[current_scene]
                if idx < len(node.choices):
                    _, dest = node.choices[idx]
                    draw_scene_text(dest)
            elif e.key == pygame.K_ESCAPE:
                mode = 'world'

    if mode == 'finale':
        screen.fill((255,255,255))
        end_surf = FONT.render("The End", True, (0,0,0))
        screen.blit(end_surf, ((W-end_surf.get_width())//2, 50))
        y = 120
        for key in history:
            txt = story[key].text
            line_surf = FONT.render(txt, True, (0,0,0))
            screen.blit(line_surf, (50, y))
            y += 25
    else:
        screen.fill((100,200,100))
        for yy in range(0, H, TILE):
            for xx in range(0, W, TILE):
                pygame.draw.rect(screen, (50,180,50), (xx,yy,TILE,TILE), 1)
        for rect in triggers.values():
            pygame.draw.rect(screen, (200,200,50), rect)
        for w in walls:
            screen.blit(wall_img, w.topleft)
        screen.blit(player_img, player.topleft)
        for npc in npcs:
            npc.update(walls)
            npc.draw(screen)
        if mode == 'narrative' and current_scene:
            draw_text_box()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
