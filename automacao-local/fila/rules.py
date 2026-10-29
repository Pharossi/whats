import re
import unicodedata

def plain(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn').strip()

def classify(text):
    t=plain(text)
    if re.search(r'\b(sair|pare|parar|remova|remover|descadastrar)\b|nao (me |nos )?(envie|mande|contate)|nao quero receber',t):
        return 'OPT_OUT'
    if re.search(r'\b(taxa|taxas|condicoes|proposta)\b|tenho interesse|quero saber',t):
        return 'ATENDIMENTO_HUMANO'
    if re.fullmatch(r'(nao operamos|nao opera|nao trabalhamos com antecipacao)[.! ]*',t):
        return 'NAO_OPERA'
    if re.fullmatch(r'(operamos com banco|opera com banco|somente com banco)[.! ]*',t):
        return 'OPERA_COM_BANCO'
    if re.fullmatch(r'(operamos|opera|sim,? operamos)[.! ]*',t):
        return 'OPERA'
    return 'INCONCLUSIVO'

def permitted(contact, blocked):
    return bool(contact['reviewed'] and contact['consent_source'] and contact['draft'].strip()
                and not contact['paused'] and not contact['opted_out'] and not blocked)
