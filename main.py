import textwrap
from abc import ABC, abstractmethod
from datetime import datetime

# --- DOMÍNIO E INTERFACES (Core) ---

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self): pass

    @abstractmethod
    def registrar(self, conta): pass

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.depositar(self.valor):
            conta.historico.gravar_evento(self)

class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.sacar(self.valor):
            conta.historico.gravar_evento(self)

class Historico:
    def __init__(self):
        self._eventos = []

    @property
    def eventos(self):
        return self._eventos

    def gravar_evento(self, transacao):
        self._eventos.append({
            "operacao": transacao.__class__.__name__,
            "quantia": transacao.valor,
            "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        })

# --- ENTIDADES (Model) ---

class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0.0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @property
    def saldo(self): return self._saldo

    @property
    def historico(self): return self._historico

    def sacar(self, valor):
        if valor > self._saldo:
            print("\n❌ Erro: Saldo insuficiente para esta operação.")
        elif valor > 0:
            self._saldo -= valor
            print(f"\n✅ Saque de R$ {valor:.2f} processado!")
            return True
        else:
            print("\n⚠️ Erro: Valor de saque inválido.")
        return False

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print(f"\n✅ Depósito de R$ {valor:.2f} processado!")
            return True
        print("\n⚠️ Erro: Valor de depósito deve ser positivo.")
        return False

class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=1000.0, limite_saques=5):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    def sacar(self, valor):
        uso_saques = len([t for t in self.historico.eventos if t["operacao"] == "Saque"])

        if valor > self._limite:
            print(f"\n❌ Erro: O valor excede seu limite de R$ {self._limite:.2f}.")
        elif uso_saques >= self._limite_saques:
            print("\n❌ Erro: Limite diário de saques atingido.")
        else:
            return super().sacar(valor)
        return False

    def __str__(self):
        return f"TITULAR: {self._cliente.nome} | AG: {self._agencia} | C/C: {self._numero}"

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def efetuar_transacao(self, conta, transacao):
        transacao.registrar(conta)

class PessoaFisica(Cliente):
    def __init__(self, cpf, nome, data_nasc, endereco):
        super().__init__(endereco)
        self.cpf = cpf
        self.nome = nome
        self.data_nasc = data_nasc

# --- CONTROLADORES (Interface) ---

def buscar_cliente(cpf, clientes):
    resultado = [c for c in clientes if c.cpf == cpf]
    return resultado[0] if resultado else None

def obter_conta_principal(cliente):
    if not cliente.contas:
        print("\n⚠️ Este cliente ainda não possui contas ativas.")
        return None
    return cliente.contas[0]

def operacao_deposito(clientes):
    cpf = input("CPF do Cliente: ")
    cliente = buscar_cliente(cpf, clientes)
    if not cliente: return print("\n❌ Cliente não cadastrado.")

    try:
        valor = float(input("Valor do depósito: R$ "))
        conta = obter_conta_principal(cliente)
        if conta:
            cliente.efetuar_transacao(conta, Deposito(valor))
    except ValueError:
        print("\n⚠️ Entrada inválida! Digite um valor numérico.")

def operacao_saque(clientes):
    cpf = input("CPF do Cliente: ")
    cliente = buscar_cliente(cpf, clientes)
    if not cliente: return print("\n❌ Cliente não cadastrado.")

    try:
        valor = float(input("Valor do saque: R$ "))
        conta = obter_conta_principal(cliente)
        if conta:
            cliente.efetuar_transacao(conta, Saque(valor))
    except ValueError:
        print("\n⚠️ Entrada inválida!")

def gerar_extrato(clientes):
    cpf = input("CPF do Cliente: ")
    cliente = buscar_cliente(cpf, clientes)
    if not cliente: return print("\n❌ Cliente não cadastrado.")

    conta = obter_conta_principal(cliente)
    if not conta: return

    print("\n" + "="*30)
    print(" EXTRATO BANCÁRIO ".center(30, " "))
    print("="*30)
    
    eventos = conta.historico.eventos
    if not eventos:
        print("Nenhuma movimentação registrada.")
    else:
        for e in eventos:
            print(f"{e['horario']} - {e['operacao']}: R$ {e['quantia']:>8.2f}")
    
    print("-" * 30)
    print(f"SALDO ATUAL: R$ {conta.saldo:.2f}")
    print("="*30)

def main():
    clientes, contas = [], []
    
    while True:
        menu = f"""
        {"  SISTEMA BANCÁRIO POO  ".center(40, "█")}
        [d]  Depositar       [nu] Novo Cliente
        [s]  Sacar           [nc] Nova Conta
        [e]  Extrato         [lc] Listar Contas
        [q]  Sair
        {"".center(40, "█")}
        => """
        
        escolha = input(textwrap.dedent(menu)).lower()

        if escolha == "d":
            operacao_deposito(clientes)
        elif escolha == "s":
            operacao_saque(clientes)
        elif escolha == "e":
            gerar_extrato(clientes)
        elif escolha == "nu":
            cpf = input("CPF (números): ")
            if buscar_cliente(cpf, clientes):
                print("\n❌ Erro: CPF já registrado.")
                continue
            clientes.append(PessoaFisica(cpf, input("Nome: "), input("Nasc (dd-mm-aaaa): "), input("Endereço: ")))
            print("\n✅ Cliente cadastrado!")
        elif escolha == "nc":
            cpf = input("CPF do Titular: ")
            cliente = buscar_cliente(cpf, clientes)
            if cliente:
                nova_cc = ContaCorrente(len(contas) + 1, cliente)
                contas.append(nova_cc)
                cliente.contas.append(nova_cc)
                print("\n✅ Conta aberta com sucesso!")
            else:
                print("\n❌ Cliente não encontrado.")
        elif escolha == "lc":
            print("\n--- RELAÇÃO DE CONTAS ---")
            for c in contas: print(c)
        elif escolha == "q":
            break

if __name__ == "__main__":
    main()