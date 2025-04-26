import requests

class Scelta:
    def __init__(self, testo, scena_destinazione=None, effetto=None, usa_llm=False, personaggio=None, contesto=None):
        self.testo = testo
        self.scena_destinazione = scena_destinazione
        self.effetto = effetto
        self.usa_llm = usa_llm
        self.personaggio = personaggio
        self.contesto = contesto

class Scena:
    def __init__(self, nome, descrizione):
        self.nome = nome
        self.descrizione = descrizione
        self.scelte = []

    def aggiungi_scelta(self, scelta):
        self.scelte.append(scelta)

    def mostra(self):
        print(f"\n[{self.nome.upper()}]\n{self.descrizione}\n")
        for i, scelta in enumerate(self.scelte):
            print(f"{i+1}. {scelta.testo}")

class Giocatore:
    def __init__(self, nome):
        self.nome = nome
        self.lucidita = 100
        self.inventario = []
        self.storia_scelte = []

    def aggiorna_lucidita(self, delta):
        self.lucidita = max(0, min(100, self.lucidita + delta))

    def aggiungi_oggetto(self, oggetto):
        if oggetto not in self.inventario:
            self.inventario.append(oggetto)

    def registra_scelta(self, scena):
        self.storia_scelte.append(scena)

# Funzione per parlare con l'IA

def dialoga_con_llm(nome_pg, contesto, messaggio, modello="llama3.2"):
    prompt = f"""
    Sei il personaggio {nome_pg} in un gioco testuale.
    Contesto: {contesto}
    Il giocatore dice: "{messaggio}"
    Rispondi in tono coerente con il tuo ruolo.
    """
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": modello, "prompt": prompt, "stream": False}
    )
    return res.json()["response"].strip()

def gioca(mappa_scene, scena_iniziale, giocatore):
    scena_corrente = mappa_scene[scena_iniziale]

    while True:
        giocatore.registra_scelta(scena_corrente.nome)
        print(f"\nLucidità mentale: {giocatore.lucidita}/100")
        scena_corrente.mostra()

        if not scena_corrente.scelte:
            print("\nFine del gioco.")
            break

        try:
            scelta = int(input("\nScegli un'opzione: ")) - 1
            scelta_attuale = scena_corrente.scelte[scelta]

            if scelta_attuale.usa_llm:
                domanda = input(f"\nParla con {scelta_attuale.personaggio}: ")
                risposta = dialoga_con_llm(
                    nome_pg=scelta_attuale.personaggio,
                    contesto=scelta_attuale.contesto,
                    messaggio=domanda
                )
                print(f"\n{scelta_attuale.personaggio.upper()}: {risposta}")

            if scelta_attuale.effetto == "finale":
                print("\nHai raggiunto un finale: " + scelta_attuale.testo)
                break
            if scelta_attuale.effetto == "lucidita--":
                giocatore.aggiorna_lucidita(-20)
                print("\nLa tua lucidità mentale diminuisce...")
            if scelta_attuale.effetto == "lucidita++":
                giocatore.aggiorna_lucidita(10)
                print("\nTi senti più lucido...")

            scena_corrente = mappa_scene[scelta_attuale.scena_destinazione]
        except (ValueError, IndexError):
            print("Scelta non valida. Riprova.")

def crea_mappa_scene():
    # Scene principali
    risveglio = Scena("risveglio", "Ti svegli. Una strana inquietudine ti attraversa.")
    ufficio = Scena("ufficio", "Arrivi da Tuckersoft. Ti offrono un contratto.")
    fallimento = Scena("fallimento", "Accetti il contratto. Il gioco fallisce miseramente.")
    autonomia = Scena("autonomia", "Rifiuti l'offerta e torni a casa per lavorare da solo.")
    casa = Scena("casa", "Resti a casa. Il silenzio è opprimente.")
    padre = Scena("padre", "Parli con tuo padre. I ricordi sulla mamma sono confusi.")
    voce = Scena("voce", "Una voce sussurra: 'Distruggi il computer'.")
    sogni = Scena("sogni", "Incubi continui ti trascinano verso la follia.")
    ritorno_casa = Scena("ritorno_casa", "Il codice si modifica da solo. Bandersnatch cambia ogni volta che lo leggi.")
    chiamata_colin = Scena("chiamata_colin", "Colin ti chiama. Vuole parlarti.")
    tetto = Scena("tetto", "Siete sul tetto. Colin ti fissa intensamente.")
    salto_tu = Scena("salto_tu", "Colin salta. Ti ritrovi intrappolato in un loop.")
    salto_io = Scena("salto_io", "Salti. La realtà cambia. Colin sparisce.")
    gioco_controlla = Scena("gioco_controlla", "Non hai seguito Colin. La tastiera scrive da sola.")
    controllo_esterno = Scena("controllo_esterno", "Scopri che sei osservato da Netflix o Futura.")
    consapevolezza = Scena("consapevolezza", "Ti rendi conto di essere dentro un gioco.")

    # Finali
    finale_commerciale = Scena("finale_commerciale", "Finale: Fallimento commerciale.")
    finale_loop = Scena("finale_loop", "Finale: Intrappolato in un loop mentale.")
    finale_omicidio = Scena("finale_omicidio", "Finale: Uccidi tuo padre.")
    finale_liberta = Scena("finale_liberta", "Finale: Completi Bandersnatch e ti liberi.")
    finale_segreto = Scena("finale_segreto", "Finale segreto: Consapevolezza metanarrativa.")

    # Collegamenti
    risveglio.aggiungi_scelta(Scelta("Vai in ufficio", "ufficio"))
    risveglio.aggiungi_scelta(Scelta("Rimani a casa", "casa"))

    ufficio.aggiungi_scelta(Scelta("Accetta il contratto", "fallimento", effetto="finale"))
    ufficio.aggiungi_scelta(Scelta("Rifiuta l'offerta", "autonomia"))

    casa.aggiungi_scelta(Scelta("Parla con tuo padre", "padre"))
    casa.aggiungi_scelta(Scelta("Taci", "sogni", effetto="lucidita--"))

    padre.aggiungi_scelta(Scelta("Ascolta la voce", "voce", effetto="lucidita--"))
    voce.aggiungi_scelta(Scelta("Distruggi il computer", "finale_segreto", effetto="finale"))

    sogni.aggiungi_scelta(Scelta("Resisti agli incubi", "ritorno_casa", effetto="lucidita--"))

    autonomia.aggiungi_scelta(Scelta("Continua a programmare", "ritorno_casa"))

    ritorno_casa.aggiungi_scelta(Scelta("Rispondi a Colin", "chiamata_colin"))

    chiamata_colin.aggiungi_scelta(Scelta("Parla con Colin", "tetto", usa_llm=True, personaggio="Colin", contesto="Sei sul tetto. Colin parla del libero arbitrio e del multiverso."))
    chiamata_colin.aggiungi_scelta(Scelta("Ignora la chiamata", "gioco_controlla", effetto="lucidita--"))

    tetto.aggiungi_scelta(Scelta("Salta tu", "salto_tu", effetto="finale"))
    tetto.aggiungi_scelta(Scelta("Salto io", "salto_io"))

    salto_io.aggiungi_scelta(Scelta("Indaga", "controllo_esterno"))
    gioco_controlla.aggiungi_scelta(Scelta("Lotta per il controllo", "controllo_esterno"))

    controllo_esterno.aggiungi_scelta(Scelta("Accetta", "consapevolezza"))

    consapevolezza.aggiungi_scelta(Scelta("Uccidi tuo padre", "finale_omicidio", effetto="finale"))
    consapevolezza.aggiungi_scelta(Scelta("Completa Bandersnatch", "finale_liberta", effetto="finale"))

    return {
        "risveglio": risveglio,
        "ufficio": ufficio,
        "fallimento": fallimento,
        "autonomia": autonomia,
        "casa": casa,
        "padre": padre,
        "voce": voce,
        "sogni": sogni,
        "ritorno_casa": ritorno_casa,
        "chiamata_colin": chiamata_colin,
        "tetto": tetto,
        "salto_tu": salto_tu,
        "salto_io": salto_io,
        "gioco_controlla": gioco_controlla,
        "controllo_esterno": controllo_esterno,
        "consapevolezza": consapevolezza,
        "finale_commerciale": finale_commerciale,
        "finale_loop": finale_loop,
        "finale_omicidio": finale_omicidio,
        "finale_liberta": finale_liberta,
        "finale_segreto": finale_segreto
    }

def main():
    print("""
            BANDERSNATCH EDITION
    Un gioco testuale ispirato a Black Mirror

    Anno 1984. Sei uno sviluppatore che sta creando
    un gioco basato su un libro maledetto...
    """)

    nome_giocatore = input("Come ti chiami, sviluppatore? ")
    giocatore = Giocatore(nome_giocatore)
    mappa_scene = crea_mappa_scene()

    print("\nLa tua avventura sta per iniziare...")
    gioca(mappa_scene, "risveglio", giocatore)

    print("\nIl tuo percorso:")
    for i, scena in enumerate(giocatore.storia_scelte):
        print(f"{i+1}. {scena}")

    print("\nGrazie per aver giocato!")

if __name__ == "__main__":
    main()
