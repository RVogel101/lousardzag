"""Central IPA source-of-truth for Western Armenian graphemes used in this project.

This module keeps letter-name IPA and letter-sound IPA separate.
All IPA-related scripts should import these maps instead of duplicating data.
"""

from __future__ import annotations

from typing import Dict

# Armenian-script spelling of each letter's traditional name.
LETTER_NAME_ARMENIAN: Dict[str, str] = {
    "\u0561": "\u0561\u0575\u0562",      # ayp
    "\u0562": "\u0562\u0565\u0576",      # pen
    "\u0563": "\u0563\u056b\u0574",      # kim
    "\u0564": "\u0564\u0561",            # ta
    "\u0565": "\u0565\u0579",            # yech
    "\u0566": "\u0566\u0561",            # za
    "\u0567": "\u0567",                  # eh
    "\u0568": "\u0568\u0569",            # et
    "\u0569": "\u0569\u0578",            # to
    "\u056a": "\u056a\u0567",            # zhe
    "\u056b": "\u056b\u0576\u056b",      # ini
    "\u056c": "\u056c\u056b\u0582\u0576",  # lyun
    "\u056d": "\u056d\u0567",            # khe
    "\u056e": "\u056e\u0561",            # dza
    "\u056f": "\u056f\u0565\u0576",      # gen
    "\u0570": "\u0570\u0578",            # ho
    "\u0571": "\u0571\u0561",            # tsa
    "\u0572": "\u0572\u0561\u057f",      # ghat
    "\u0573": "\u0573\u0567",            # je
    "\u0574": "\u0574\u0567\u0576",      # men
    "\u0575": "\u0575\u056b",            # yi
    "\u0576": "\u0576\u0578\u0582",      # nu
    "\u0577": "\u0577\u0561",            # sha
    "\u0578": "\u0578",                  # vo
    "\u0579": "\u0579\u0561",            # cha
    "\u057a": "\u057a\u0567",            # be
    "\u057b": "\u057b\u0567",            # che
    "\u057c": "\u057c\u0561",            # rra
    "\u057d": "\u057d\u0567",            # se
    "\u057e": "\u057e\u0565\u0582",      # vev
    "\u057f": "\u057f\u056b\u0582\u0576",  # dyun
    "\u0580": "\u0580\u0567",            # re
    "\u0581": "\u0581\u0585",            # tso
    "\u0582": "\u0570\u056b\u0582\u0576",  # yiwn
    "\u0583": "\u0583\u056b\u0582\u0580",  # pyur
    "\u0584": "\u0584\u0567",            # ke
    "\u0585": "\u0585",                  # o
    "\u0586": "\u0586\u0567",            # fe
}

# Spoken names of Armenian letters (grapheme names), in IPA.
LETTER_NAME_IPA: Dict[str, str] = {
    "ա": "ɑjpʰ",
    "բ": "pʰɛn",
    "գ": "kʰim",
    "դ": "tʰɑ",
    "ե": "jɛtʃʰ",
    "զ": "zɑ",
    "է": "ɛ",
    "ը": "ətʰ",
    "թ": "tʰɔ",
    "ժ": "ʒɛ",
    "ի": "ini",
    "լ": "lʏn",
    "խ": "χɛ",
    "ծ": "dzɑ",
    "կ": "ɡɛn",
    "հ": "ho",
    "ձ": "tsʰɑ",
    "ղ": "ʁɑd",
    "ճ": "dʒɛ",
    "մ": "mɛn",
    "յ": "hi",
    "ն": "nu",
    "շ": "ʃɑ",
    "ո": "ʋɔ",
    "չ": "tʃʰɑ",
    "պ": "bɛ",
    "ջ": "tʃʰɛ",
    "ռ": "ɾɑ",
    "ս": "sɛ",
    "վ": "vɛv",
    "տ": "dʏn",
    "ր": "ɾɛ",
    "ց": "tsʰɔ",
    "ւ": "hʏn",
    "փ": "pʰʏɾ",
    "ք": "kʰɛ",
    "օ": "o",
    "ֆ": "fɛ",
}

# Base letter sounds (phoneme values), in IPA.
# Context-sensitive alternates are stored separately below.
LETTER_SOUND_IPA: Dict[str, str] = {
    "ա": "ɑ",
    "բ": "pʰ",
    "գ": "kʰ",
    "դ": "tʰ",
    "ե": "ɛ",
    "զ": "z",
    "է": "ɛ",
    "ը": "ə",
    "թ": "tʰ",
    "ժ": "ʒ",
    "ի": "i",
    "լ": "l",
    "խ": "χ",
    "ծ": "dz",
    "կ": "ɡ",
    "հ": "h",
    "ձ": "tsʰ",
    "ղ": "ʁ",
    "ճ": "dʒ",
    "մ": "m",
    "յ": "h",
    "ն": "n",
    "շ": "ʃ",
    "ո": "ɔ",
    "չ": "tʃʰ",
    "պ": "b",
    "ջ": "tʃʰ",
    "ռ": "ɾ",
    "ս": "s",
    "վ": "v",
    "տ": "d",
    "ր": "ɾ",
    "ց": "tsʰ",
    "ւ": "v",
    "փ": "pʰ",
    "ք": "kʰ",
    "օ": "o",
    "ֆ": "f",
}

# Word-initial alternates requested by user.
LETTER_SOUND_IPA_WORD_INITIAL: Dict[str, str] = {
    "ե": "jɛ",
    "ո": "ʋɔ",
}

# Multi-character diphthong sounds (vowel + vowel combinations).
DIPHTHONG_SOUND_IPA: Dict[str, str] = {
    "ու": "u",
    "իւ": "ju",
    "եա": "ɛɑ",
    "ոյ": "uj",
    "այ": "aj",
}

# Ligatures (special graphemes).
LIGATURE_SOUND_IPA: Dict[str, str] = {
    "և": "jɛv",
}
