"""Carrega o modelo de chat a partir da variável de ambiente MODELO e imprime o trace do agente.

Exemplo:  MODELO="openai:gpt-4.1"  +  OPENAI_API_KEY="..."
"""
import os

from langchain.chat_models import init_chat_model


def carregar_modelo():
    modelo = os.environ.get("MODELO")
    if not modelo:
        raise RuntimeError(
            'Defina a variável MODELO no formato "provedor:modelo", ex.: MODELO="openai:gpt-4.1", '
            "e a chave de API do provedor (ex.: OPENAI_API_KEY)."
        )
    return init_chat_model(modelo)


def mostrar_trace(resultado):
    """Mostra cada mensagem trocada no loop do agente (pedido de tool, resultado e resposta final)."""
    for msg in resultado["messages"]:
        print(f"--- {msg.type} ---")
        if msg.content:
            print(msg.content)
        for call in getattr(msg, "tool_calls", None) or []:
            print(f"  -> tool_call: {call['name']}({call['args']})")
    print()
