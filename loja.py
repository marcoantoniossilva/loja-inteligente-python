import face_recognition
import secrets
import random
import faker
import simpy
import json

FOTOS_CLIENTES = [
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\angela1.jpeg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\tyrell1.jpeg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\price1.jpg",

    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\darlene1.jpg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\darlene2.jpg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\darlene3.jpg",

    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\elliot1.jpg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\elliot2.jpg",
    "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\faces\\elliot3.jpg"
]
ARQUIVO_CONFIGURACAO = "C:\\Users\\Win10\\Documents\\GitHub\\loja-inteligente-python\\configuracao.json"

PROBABILIDADE_DE_SER_INADIMPLENTE = 5
PROBABILIDADE_TORNAR_INADIMPLENTE = 15
PROBABILIDADE_DEIXAR_INADIMPLENCIA = 40
PROBABILIDADE_DE_SE_TORNAR_VIP = 10

TEMPO_ENTRE_VISITANTES = 150


def preparar():
    global configuracao
    
    configuracao = None
    with open(ARQUIVO_CONFIGURACAO, "r") as arquivo_configuracao:
        configuracao = json.load(arquivo_configuracao)
        if configuracao:
            print("configuracao carregada. versao da simulacao:", configuracao["versao"])

    global clientes_reconhecidos
    clientes_reconhecidos = {}

    global clientes_inadimplentes
    clientes_inadimplentes = {}

    global clientes_VIP
    clientes_VIP = {}

    global gerador_dados_falsos
    gerador_dados_falsos = faker.Faker(locale="pt_BR")

def simular_visita():
    visitante = {
        "foto": random.choice(FOTOS_CLIENTES),
        "dados": None
    }

    return visitante

def reconhecer_cliente(visitante):
    global configuracao
    global gerador_dados_falsos

    print("iniciando reconhecimento de cliente...")
    foto_visitante = face_recognition.load_image_file(visitante["foto"])
    encoding_foto_visitante = face_recognition.face_encodings(foto_visitante)[0]

    reconhecido = False
    for cadastro in configuracao["cadastros"]:
        fotos_banco = cadastro["fotos"]
        total_reconhecimentos = 0

        for foto in fotos_banco:
            foto_banco = face_recognition.load_image_file(foto)
            encoding_foto_banco = face_recognition.face_encodings(foto_banco)[0]

            foto_reconhecida = face_recognition.compare_faces([encoding_foto_visitante], encoding_foto_banco)[0]
            if foto_reconhecida:
                total_reconhecimentos += 1

        if total_reconhecimentos/len(fotos_banco) > 0.7:
            reconhecido = True

            visitante["dados"] = {}
            visitante["dados"]["nome"] = gerador_dados_falsos.name()
            visitante["dados"]["idade"] = random.randint(18, 100)
            visitante["dados"]["endereco"] = gerador_dados_falsos.address()
            visitante["dados"]["renda"] = random.randint(1100, 6000)

    return reconhecido, visitante

def imprimir_dados(cliente):
    print("nome:", cliente["dados"]["nome"])
    print("idade:", cliente["dados"]["idade"])
    print("endereco:", cliente["dados"]["endereco"])
    print("renda:", cliente["dados"]["renda"],"\n")

def reconhecer_visitante(env):
    global clientes_reconhecidos

    while True:
        print("reconhecendo um cliente em ciclo/tempo", env.now)

        visitante = simular_visita()
        reconhecido, cliente = reconhecer_cliente(visitante)
        if reconhecido:
            id_atendimento = secrets.token_hex(nbytes=16).upper()
            clientes_reconhecidos[id_atendimento] = cliente

            print("um cliente foi reconhecido, imprimindo os dados...")
            imprimir_dados(cliente)
        else:
            print("nao foi reconhecido um cliente\n")

        yield env.timeout(TEMPO_ENTRE_VISITANTES)


def identificar_inadimplencia(env):
    global clientes_reconhecidos
    global clientes_inadimplentes

    while True:
        if len(clientes_reconhecidos):
            print("verificando situacao de inadimplencia em ciclo/tempo", env.now)

            for id_atendimento, cliente in list(clientes_reconhecidos.items()):
                inadimplencia_reconhecida = (random.randint(1, 100) <= PROBABILIDADE_DE_SER_INADIMPLENTE)
                if inadimplencia_reconhecida:
                    clientes_inadimplentes[id_atendimento] = cliente
                    clientes_reconhecidos.pop(id_atendimento) #se for inadimplente, automaticamente e cliente reconhecido.

                    print("ATENÇÃO! cliente", cliente["dados"]["nome"], "em situacao de inadimplencia!\n")
        yield env.timeout(TEMPO_ENTRE_VISITANTES+30)

def verificar_perfil(env):
    global clientes_reconhecidos
    
    while True:
        if len(clientes_reconhecidos):
            print("verificando perfil de cliente em ciclo/tempo", env.now)
            for cliente in clientes_reconhecidos.values():
                renda = cliente["dados"]["renda"]
                if renda >= 5000:
                    print("cliente", cliente["dados"]["nome"], "e VIP.\n")
                else:
                    print("cliente", cliente["dados"]["nome"], "nao e VIP por ter renda baixa.\n")
                
        yield env.timeout(TEMPO_ENTRE_VISITANTES+30)


def atualizar_perfil(env):
    global clientes_reconhecidos
    global clientes_inadimplentes
    global clientes_VIP

    while True:
        if len(clientes_reconhecidos) or len(clientes_inadimplentes):
            print("atualizando perfil em ciclo/tempo", env.now)
            if len(clientes_reconhecidos):
                for id_atendimento, cliente in list(clientes_reconhecidos.items()):
                        tornou_inadimplente = (random.randint(1, 100) <= PROBABILIDADE_TORNAR_INADIMPLENTE)
                        if tornou_inadimplente:
                            clientes_inadimplentes[id_atendimento] = cliente
                            clientes_reconhecidos.pop(id_atendimento)
                            print("cliente", cliente["dados"]["nome"], " tornou-se inadimplente\n")
                        else:
                            tornou_vip = (random.randint(1, 100) <= PROBABILIDADE_DE_SE_TORNAR_VIP)
                            if tornou_vip:
                                clientes_VIP[id_atendimento] = cliente
                                clientes_reconhecidos.pop(id_atendimento)
                                print("cliente", cliente["dados"]["nome"], " tornou-se VIP\n")

            if len(clientes_inadimplentes):
                for id_atendimento, cliente in list(clientes_inadimplentes.items()):
                        deixou_inadimplencia = (random.randint(1, 100) <= PROBABILIDADE_DEIXAR_INADIMPLENCIA)
                        if deixou_inadimplencia:
                            clientes_reconhecidos[id_atendimento] = cliente
                            clientes_inadimplentes.pop(id_atendimento)

                            print("cliente", cliente["dados"]["nome"], " deixou de ser inadimplente\n")   
            
            yield env.timeout(TEMPO_ENTRE_VISITANTES+30)

if __name__ == "__main__":
    try:
        preparar()

        env = simpy.Environment()
        env.process(reconhecer_visitante(env))
        env.process(identificar_inadimplencia(env))
        env.process(verificar_perfil(env))
        env.process(atualizar_perfil(env))
        env.run(until=1000)
    except KeyboardInterrupt:
            print("Interrompido pelo usuário.")