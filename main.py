"""
Script de controle interativo para o sensor de cor TCS34725 via I2C no Raspberry Pi.
Permite leitura única, leitura contínua e salvamento dos dados em arquivo, com validação de erro e tratamento de entradas.
Agora inclui um canal extra 'infrared' (simulado).
"""

import smbus
import time
import os
from datetime import datetime

# Endereço I2C do TCS34725
TCS34725_ADDR = 0x29
I2C_BUS = 1  # Ajuste conforme sua placa

# Caminho do arquivo de log (pode ser configurado por variável de ambiente)
CAMINHO_ARQUIVO = os.getenv("CAMINHO_ARQUIVO", "/home/pi/cor_log.txt")

# Registradores do TCS34725
COMMAND_BIT = 0x80
REG_ENABLE = 0x00
REG_ATIME  = 0x01
REG_CONTROL= 0x0F
REG_CDATAL = 0x14

ENABLE_PON = 0x01
ENABLE_AEN = 0x02

bus = smbus.SMBus(I2C_BUS)

def inicializar_sensor():
    """Inicializa o sensor TCS34725."""
    print("Inicializando sensor TCS34725...")
    bus.write_byte_data(TCS34725_ADDR, COMMAND_BIT | REG_ENABLE, ENABLE_PON)
    time.sleep(0.01)
    bus.write_byte_data(TCS34725_ADDR, COMMAND_BIT | REG_ENABLE, ENABLE_PON | ENABLE_AEN)
    # Tempo de integração padrão (~700ms)
    bus.write_byte_data(TCS34725_ADDR, COMMAND_BIT | REG_ATIME, 0x00)
    # Ganho padrão (4x)
    bus.write_byte_data(TCS34725_ADDR, COMMAND_BIT | REG_CONTROL, 0x01)
    time.sleep(0.7)
    print("Sensor pronto.")

def ler_cor():
    """
    Lê os valores de cor do sensor TCS34725 via I2C.
    Retorna clear, red, green, blue, infrared (simulado).
    """
    try:
        data = bus.read_i2c_block_data(TCS34725_ADDR, COMMAND_BIT | REG_CDATAL, 8)
        clear = (data[1] << 8) | data[0]
        red   = (data[3] << 8) | data[2]
        green = (data[5] << 8) | data[4]
        blue  = (data[7] << 8) | data[6]
        # Canal extra: infravermelho estimado (clear - (R+G+B))
        infrared = max(0, clear - (red + green + blue))
        return clear, red, green, blue, infrared
    except Exception as e:
        print("Erro ao ler TCS34725:", e)
        return None, None, None, None, None

def mostrar_leitura(clear, red, green, blue, infrared):
    """Exibe os valores de cor lidos."""
    print("\nLeitura de cor:")
    print(f" - Clear  : {clear}")
    print(f" - Red    : {red}")
    print(f" - Green  : {green}")
    print(f" - Blue   : {blue}")
    print(f" - Infrared (simulado): {infrared}")

def menu_interativo():
    """Exibe o menu de opções."""
    print("\n" + "="*45)
    print("CONTROLE INTERATIVO DO SENSOR TCS34725")
    print("="*45)
    print("1 - Leitura única (RGB + Infrared)")
    print("2 - Leitura contínua (tempo real) [Ctrl+C para parar]")
    print("3 - Salvar leitura no arquivo")
    print("0 - Sair")
    print("-"*45)

def obter_entrada_usuario(prompt, tipo=int, validacao=None):
    """Solicita e valida entrada do usuário."""
    while True:
        try:
            entrada = input(prompt)
            valor = tipo(entrada)
            if validacao and not validacao(valor):
                print("Opção inválida!")
                continue
            return valor
        except ValueError:
            print(f"Entrada inválida! Digite um {tipo.__name__} válido.")
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário")
            return None

def salvar_leitura(clear, red, green, blue, infrared):
    """Salva uma linha de leitura com timestamp no arquivo."""
    if None in (clear, red, green, blue, infrared):
        print("Não foi possível obter leitura válida do sensor. Nada salvo.")
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] Clear:{clear} Red:{red} Green:{green} Blue:{blue} Infrared:{infrared}\n"
    try:
        with open(CAMINHO_ARQUIVO, "a", encoding="utf-8") as f:
            f.write(linha)
        print(f"Leitura salva em {CAMINHO_ARQUIVO}")
    except Exception as e:
        print("Erro ao salvar leitura:", e)

if __name__ == "__main__":
    print("Iniciando controle do sensor TCS34725 em Python...")
    inicializar_sensor()
    try:
        while True:
            menu_interativo()
            opcao = obter_entrada_usuario("Digite sua opção: ", int, lambda x: x in [0,1,2,3])
            if opcao is None or opcao == 0:
                print("Saindo do programa...")
                break
            elif opcao == 1:
                clear, red, green, blue, infrared = ler_cor()
                if None in (clear, red, green, blue, infrared):
                    print("Não foi possível obter leitura válida do sensor.")
                else:
                    mostrar_leitura(clear, red, green, blue, infrared)
            elif opcao == 2:
                print("\nLeitura contínua (Ctrl+C para parar)...")
                try:
                    while True:
                        clear, red, green, blue, infrared = ler_cor()
                        if None in (clear, red, green, blue, infrared):
                            print("Erro na leitura. Pulando...")
                        else:
                            mostrar_leitura(clear, red, green, blue, infrared)
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nLeitura contínua interrompida.")
            elif opcao == 3:
                clear, red, green, blue, infrared = ler_cor()
                if None in (clear, red, green, blue, infrared):
                    print("Não foi possível obter leitura válida do sensor.")
                else:
                    mostrar_leitura(clear, red, green, blue, infrared)
                    salvar_leitura(clear, red, green, blue, infrared)
    except KeyboardInterrupt:
        print("\nFinalizado pelo usuário.")