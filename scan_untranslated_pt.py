import xml.etree.ElementTree as ET
import re
root = ET.parse("NTEGlobal/i18n/lang_pt.ts").getroot()
entries = []
for context in root.findall("context"):
    name = context.find("name").text if context.find("name") is not None else ""
    for message in context.findall("message"):
        src = message.find("source")
        tr = message.find("translation")
        if src is None or tr is None:
            continue
        src_text = src.text or ""
        tr_text = tr.text or ""
        if not tr_text.strip():
            entries.append((name, src_text, tr_text))
        else:
            if re.search(r"\b(the|has|is|if|buy|pay|to|be|join|search|find|and|or|please|continue|cancel|confirm|yes|no|loading|update|version|client|resource|account|login|password|security|install|restart|time|error|network|game|download|retry|prompt|status|pause|play|installing|waiting)\b", tr_text, re.I):
                if not re.search(r"\b(continuar|cancelar|confirmar|sim|nao|não|erro|jogo|instalar|senha|conta|recurso|atualização|atualizacao|carregando|rede|versão|versao|cliente|tempo|espera|download|reiniciar|pausar|carregar|aguarde|usuario|usuário|instalando|aguardando)\b", tr_text, re.I):
                    entries.append((name, src_text, tr_text))
unique = {}
for c,s,t in entries:
    unique[(s,t)] = c
for (s,t),c in list(unique.items())[:500]:
    print(f"[{c}] {s!r} -> {t!r}")
print("--- total", len(unique))
