import pandas as pd

from src.common.dicionario import Dicionario as dic
from src.common.date import *


def get_response(titulo, tipo_grafico, dados):
    if type(dados) != dict:
        dados = dados.to_dict()

    return {
        "title": titulo,
        "chartType": tipo_grafico,
        "data": dados
    }


def pedidos_por_estado(dados: pd.DataFrame, somenteEntregues: bool = False):
    '''
    RF__01 Quantidade de pedidos por estado   OK
    ADICIONAR Somente já entregues            OK
    '''
    if somenteEntregues:
        dados = dados.loc[dados[dic.status] == dic.entregue]

    dados = dados[dic.estado_destino].value_counts()
    return get_response("Quantidade de pedidos por estado", "bar", dados)


def pedidos_por_cidade(dados: pd.DataFrame, somenteEntregues: bool = False):
    '''
    RF__02 Quantidade de pedidos por cidade   OK
    ADICIONAR Somente já entregues            OK
    '''
    if somenteEntregues:
        dados = dados.loc[dados[dic.status] == dic.entregue]

    dados = dados[dic.cidade_destino].value_counts().head(10)
    return get_response("10 cidades com mais pedidos", "bar", dados)


def taxa_reincidencia(dados: pd.DataFrame, clientes: bool = False):
    ''' 
    RF_03 Reincidencia de compra
    'clientes' = False: Retorna a % de clientes que compraram mais de 1 vez.    OK
    'clientes' = True : Retorna o json de clientes que compraram mais de 1 vez. OK
    Exemplo json: {"nome" : QtdCompras}
    '''
    resultado = dados[dic.destinatario].value_counts()

    if clientes:
        response = get_response("Clientes reincidentes", "table", resultado)

    else:
        novos = 0
        reincidentes = 0

        for k, v in resultado.items():
            if v == 1:
                novos += 1
            else:
                reincidentes += 1

        response = {
            "Clientes que fizeram apenas 1 compra": novos,
            "Clientes que voltaram a comprar": reincidentes,
        }

    return get_response("Taxa de reincidência", "pie", response)


def genero_predominante(
    planilhaClientes: pd.DataFrame, 
    planilhaPedidos: pd.DataFrame, 
    apenasCadastrados: bool = False, 
    somenteEntregues: bool = False
):
    '''
    RF_04 Gênero predominante
    Quantidade de clientes que fizeram um pedido
    ADICIONAR: Somente pedidos já entregues
    '''

    if apenasCadastrados:
        result = planilhaClientes[dic.genero].value_counts()

    else:
        if somenteEntregues:
            planilhaPedidos = planilhaPedidos.loc[planilhaPedidos[dic.status] == dic.entregue]
        result = planilhaClientes.loc[planilhaClientes[dic.id].isin(planilhaPedidos[dic.cliente_id])]
        result = result[dic.genero].value_counts()

    result = result.rename({
        'F': 'Mulheres',
        'M': 'Homens'
    })
    return get_response("Gênero dos clientes", "pie", result)


def faixa_etaria(planilhaClientes: pd.DataFrame, passo: int = 5):
    '''
    RF_05 Faixa Etária OK
    '''
    index = []  # [0, 0, 0, 1, 1, 1, 2, 2, 2]
    chaves = []  # ['0-2', '3-5', '6-8']
    response = {}
    count = 0

    for i in range(0, 121, passo):
        for j in range(passo):
            index.append(count)

        count += 1
        chave = str(i)

        if passo > 1:
            chave += '-' + str(i + passo-1)

        chaves.append(chave)

    for cliente in range(len(planilhaClientes)):
        dataNascimento = planilhaClientes[dic.data_nascimento][cliente]
        idade = calcula_idade(dataNascimento)

        if idade < 122:
            pos = index[idade]
            chave = chaves[pos]

            if (chave in response) == False:
                response[chave] = 0

            response[chave] += 1

    return get_response("Faixa Etária", "bar", response)


def cadastros_periodo(
    planilhaClientes: pd.DataFrame, 
    dataInicial: str = None, 
    dataFinal: str = None, 
    tempo: str = "Meses"
):
    '''
    RF_06 Períodos com mais cadastros em MESES
    Geral               OK
    Período definido    OK
    Meses e Anos        OK
    '''
    # dataInicial = dataInicial.split('T')[0]
    # dataFinal = dataFinal.split('T')[0]
    response = {}
    for cliente in range(len(planilhaClientes)):
        dataCriacao = planilhaClientes[dic.data_cadastro][cliente].split()[0]

        if tempo == "Meses":
            dataCriacao = dataCriacao[:7]

        elif tempo == "Anos":
            dataCriacao = dataCriacao[:4]

        if (dataInicial != None):
            if entre_datas(dataInicial, dataCriacao, dataFinal, tempo):
                if (dataCriacao in response) == False:
                    response[dataCriacao] = 0
                response[dataCriacao] += 1
        else:
            if (dataCriacao in response) == False:
                response[dataCriacao] = 0
            response[dataCriacao] += 1
    return get_response("Cadastros por período", "line", response)


def faturamento_periodo(
    planilhaPedidos: pd.DataFrame, 
    tempo: str = 'Dias', 
    dataInicial: str = None, 
    dataFinal: str = None
):
    '''
    RF_07 Faturamento por período
    Por ano     OK
    Por mês     OK
    Por dias    OK
    Truncar     FAZER
    '''
    response = {}
    # dataInicial = dataInicial.split('T')[0]
    # dataFinal = dataFinal.split('T')[0]
    for pedido in range(len(planilhaPedidos)):
        status = planilhaPedidos[dic.status][pedido]

        if status == dic.entregue or status == "Pedido Enviado":
            data = planilhaPedidos[dic.data_criacao][pedido].split(' ')[0]

            chave = ''
            if (tempo == 'Dias'):
                chave = data

            elif tempo == 'Meses':
                chave = data[:7]    # YYYY-MM

            elif tempo == 'Anos':
                chave = data[:4]

            valorPedido = float(planilhaPedidos[dic.valor_total][pedido])

            if(dataInicial != None):
                if entre_datas(dataInicial, chave, dataFinal, tempo):
                    if (chave in response.keys()) == False:
                        response[chave] = 0

                    response[chave] += valorPedido

            else:
                if (chave in response.keys()) == False:
                    response[chave] = 0

                response[chave] += valorPedido

    return get_response("Faturamento por período", "line", response)


'''
RF_08 
'''


def cancelamentos_periodo(
    planilhaPedidos: pd.DataFrame, 
    dataInicial: str = None, 
    dataFinal: str = None, 
    tempo: str = "Meses"
):
    '''
    RF_09 Cancelamento por período
    '''
    # dataInicial = dataInicial.split('T')[0]
    # dataFinal = dataFinal.split('T')[0]
    response = {}
    for pedido in range(len(planilhaPedidos)):
        dataCriacao = planilhaPedidos[dic.data_criacao][pedido].split()[0]

        if tempo == "Meses":
            dataCriacao = dataCriacao[:7]
        elif tempo == "Anos":
            dataCriacao = dataCriacao[:4]

        status = planilhaPedidos[dic.status][pedido]
        if status == dic.cancelado:
            if (dataInicial != None):
                if entre_datas(dataInicial, dataCriacao, dataFinal, tempo):
                    if (dataCriacao in response) == False:
                        response[dataCriacao] = 0
                    response[dataCriacao] += 1
            else:
                if (dataCriacao in response) == False:
                    response[dataCriacao] = 0
                response[dataCriacao] += 1
    return get_response("Cancelamentos por período", "line", response)


def metodo_pagamento_aprovacoes(dados: pd.DataFrame):
    '''
    RF__10 Taxa de cancelamento por método de pagamento
    RF__11 Preferência por método de pegamento
    '''
    meiosPagamento = set(dados[dic.tipo_pagamento].values)
    infoPagamentos = {}

    for tipo in meiosPagamento:
        qtdUsos = len(dados.loc[dados[dic.tipo_pagamento] == tipo])
        qtdAprovados = len(dados.loc[(dados[dic.tipo_pagamento] == tipo) & (
            dados[dic.status] == dic.entregue)])

        infoPagamentos[tipo] = {
            "usos": qtdUsos,
            "aprovados": qtdAprovados
        }

    return get_response("Preferência por método de pagamento", "bar", infoPagamentos)


def metodo_envio_preferencia(planilhaPedidos: pd.DataFrame):
    '''
    RF_12 Preferencia pelos meios de envio
    Total   
    Melhoria: Por período FAZER
    '''
    response = {}

    for pedido in range(len(planilhaPedidos)):
        if planilhaPedidos[dic.status][pedido] == dic.entregue:
            metodoEnvio = planilhaPedidos[dic.metodo_envio][pedido]

            if (metodoEnvio in response.keys()) == False:
                response[metodoEnvio] = 0

            response[metodoEnvio] += 1
    return get_response("Preferência por método de envio", "pie", response)