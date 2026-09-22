"""
https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
ISO 639 is a standardized nomenclature used to classify languages. Each language is
assigned a two-letter (639-1) and three-letter (639-2 and 639-3) lowercase
abbreviation, amended in later versions of the nomenclature.

This list contains all of:
ISO 639-1: two-letter codes, one per language for ISO 639 macrolanguage

And some of:
ISO 639-2/T: three-letter codes, for the same languages as 639-1.
ISO 639-2/B: three-letter codes, mostly the same as 639-2/T, but with some codes
derived from English names rather than native names of languages.
ISO 639-3: three-letter codes, the same as 639-2/T for languages, but with distinct
codes for each variety of an ISO 639 macrolanguage.
"""

from typing import Any

_NAMES = "names"
_639_1 = "639-1"
_639_2T = "639-2/T"
_639_2B = "639-2/B"
_639_3 = "639-3"

LANGUAGES: list[dict[str, Any]] = [
    {
        _NAMES: ["Abkhazian"],
        _639_1: "ab",
        _639_2T: "abk",
        _639_2B: "abk",
        _639_3: {
            "abk": "Abkhazian",
        },
    },
    {
        _NAMES: ["Afar"],
        _639_1: "aa",
        _639_2T: "aar",
        _639_2B: "aar",
        _639_3: {
            "aar": "Afar",
        },
    },
    {
        _NAMES: ["Afrikaans"],
        _639_1: "af",
        _639_2T: "afr",
        _639_2B: "afr",
        _639_3: {
            "afr": "Afrikaans",
        },
    },
    {
        _NAMES: ["Akan"],
        _639_1: "ak",
        _639_2T: "aka",
        _639_2B: "aka",
        _639_3: {"aka": "Akan", "fat": "Fanti", "twi": "Twi"},
    },
    {
        _NAMES: ["Albanian"],
        _639_1: "sq",
        _639_2T: "sqi",
        _639_2B: "alb",
        _639_3: {
            "sqi": "Albanian",
            "aae": "Arbëreshë Albanian",
            "aat": "Arvanitika Albanian",
            "aln": "Gheg Albanian",
            "als": "Tosk Albanian",
        },
    },
    {
        _NAMES: ["Amharic"],
        _639_1: "am",
        _639_2T: "amh",
        _639_2B: "amh",
        _639_3: {
            "amh": "Amharic",
        },
    },
    {
        _NAMES: ["Arabic"],
        _639_1: "ar",
        _639_2T: "ara",
        _639_2B: "ara",
        _639_3: {
            "ara": "Arabic",
            "aao": "Algerian Saharan Arabic",
            "abh": "Tajiki Arabic",
            "abv": "Baharna Arabic",
            "acm": "Mesopotamian Arabic",
            "acq": "Ta'izzi-Adeni Arabic",
            "acw": "Hijazi Arabic",
            "acx": "Omani Arabic",
            "acy": "Cypriot Arabic",
            "adf": "Dhofari Arabic",
            "aeb": "Tunisian Arabic",
            "aec": "Saidi Arabic",
            "afb": "Gulf Arabic",
            "apc": "Levantine Arabic",
            "apd": "Sudanese Arabic",
            "arb": "Standard Arabic",
            "arq": "Algerian Arabic",
            "ars": "Najdi Arabic",
            "ary": "Moroccan Arabic",
            "arz": "Egyptian Arabic",
            "auz": "Uzbeki Arabic",
            "avl": "Eastern Egyptian Bedawi Arabic",
            "ayh": "Hadrami Arabic",
            "ayl": "Libyan Arabic",
            "ayn": "Sanaani Arabic",
            "ayp": "North Mesopotamian Arabic",
            "pga": "Sudanese Creole Arabic",
            "shu": "Chadian Arabic",
            "ssh": "Shihhi Arabic",
        },
    },
    {
        _NAMES: ["Aragonese"],
        _639_1: "an",
        _639_2T: "arg",
        _639_2B: "arg",
        _639_3: {
            "arg": "Aragonese",
        },
    },
    {
        _NAMES: ["Armenian"],
        _639_1: "hy",
        _639_2T: "hye",
        _639_2B: "arm",
        _639_3: {
            "hye": "Armenian",
        },
    },
    {
        _NAMES: ["Assamese"],
        _639_1: "as",
        _639_2T: "asm",
        _639_2B: "asm",
        _639_3: {
            "asm": "Assamese",
        },
    },
    {
        _NAMES: ["Avaric"],
        _639_1: "av",
        _639_2T: "ava",
        _639_2B: "ava",
        _639_3: {
            "ava": "Avaric",
        },
    },
    {
        _NAMES: ["Avestan"],
        _639_1: "ae",
        _639_2T: "ave",
        _639_2B: "ave",
        _639_3: {
            "ave": "Avestan",
        },
    },
    {
        _NAMES: ["Aymara"],
        _639_1: "ay",
        _639_2T: "aym",
        _639_2B: "aym",
        _639_3: {
            "aym": "Aymara",
            "ayc": "Southern Aymara",
            "ayr": "Central Aymara",
        },
    },
    {
        _NAMES: ["Azerbaijani"],
        _639_1: "az",
        _639_2T: "aze",
        _639_2B: "aze",
        _639_3: {
            "aze": "Azerbaijani",
            "azb": "South Azerbaijani",
            "azj": "North Azerbaijani",
        },
    },
    {
        _NAMES: ["Bambara"],
        _639_1: "bm",
        _639_2T: "bam",
        _639_2B: "bam",
        _639_3: {
            "bam": "Bambara",
        },
    },
    {
        _NAMES: ["Bashkir"],
        _639_1: "ba",
        _639_2T: "bak",
        _639_2B: "bak",
        _639_3: {
            "bak": "Bashkir",
        },
    },
    {
        _NAMES: ["Basque"],
        _639_1: "eu",
        _639_2T: "eus",
        _639_2B: "baq",
        _639_3: {
            "eus": "Basque",
        },
    },
    {
        _NAMES: ["Belarusian"],
        _639_1: "be",
        _639_2T: "bel",
        _639_2B: "bel",
        _639_3: {
            "bel": "Belarusian",
        },
    },
    {
        _NAMES: ["Bengali"],
        _639_1: "bn",
        _639_2T: "ben",
        _639_2B: "ben",
        _639_3: {
            "ben": "Bengali",
        },
    },
    {
        _NAMES: ["Bislama"],
        _639_1: "bi",
        _639_2T: "bis",
        _639_2B: "bis",
        _639_3: {
            "bis": "Bislama",
        },
    },
    {
        _NAMES: ["Bosnian"],
        _639_1: "bs",
        _639_2T: "bos",
        _639_2B: "bos",
        _639_3: {
            "bos": "Bosnian",
        },
    },
    {
        _NAMES: ["Breton"],
        _639_1: "br",
        _639_2T: "bre",
        _639_2B: "bre",
        _639_3: {
            "bre": "Breton",
        },
    },
    {
        _NAMES: ["Bulgarian"],
        _639_1: "bg",
        _639_2T: "bul",
        _639_2B: "bul",
        _639_3: {
            "bul": "Bulgarian",
        },
    },
    {
        _NAMES: ["Burmese"],
        _639_1: "my",
        _639_2T: "mya",
        _639_2B: "bur",
        _639_3: {
            "mya": "Burmese",
        },
    },
    {
        _NAMES: ["Catalan", "Valencian"],
        _639_1: "ca",
        _639_2T: "cat",
        _639_2B: "cat",
        _639_3: {
            "cat": "Catalan",
        },
    },
    {
        _NAMES: ["Chamorro"],
        _639_1: "ch",
        _639_2T: "cha",
        _639_2B: "cha",
        _639_3: {
            "cha": "Chamorro",
        },
    },
    {
        _NAMES: ["Chechen"],
        _639_1: "ce",
        _639_2T: "che",
        _639_2B: "che",
        _639_3: {
            "che": "Chechen",
        },
    },
    {
        _NAMES: ["Chichewa", "Chewa", "Nyanja"],
        _639_1: "ny",
        _639_2T: "nya",
        _639_2B: "nya",
        _639_3: {
            "nya": "Chichewa",
        },
    },
    {
        _NAMES: ["Chinese"],
        _639_1: "zh",
        _639_2T: "zho",
        _639_2B: "chi",
        _639_3: {
            "zho": "Chinese",
            "cdo": "Min Dong Chinese",
            "cjy": "Jinyu Chinese",
            "cmn": "Mandarin Chinese",
            "cnp": "Northern Ping Chinese",
            "cpx": "Pu-Xian Chinese",
            "csp": "Southern Ping Chinese",
            "czh": "Huizhou Chinese",
            "czo": "Min Zhong Chinese",
            "gan": "Gan Chinese",
            "hak": "Hakka Chinese",
            "hnm": "Hainanese",
            "hsn": "Xiang Chinese",
            "luh": "Leizhou Chinese",
            "lzh": "Literary Chinese",
            "mnp": "Min Bei Chinese",
            "nan": "Min Nan Chinese",
            "sjc": "Shaojiang Chinese",
            "wuu": "Wu Chinese",
            "yue": "Yue Chinese",
        },
    },
    {
        _NAMES: [
            "Church Slavic",
            "Old Slavonic",
            "Church Slavonic",
            "Old Bulgarian",
            "Old Church Slavonic",
        ],
        _639_1: "cu",
        _639_2T: "chu",
        _639_2B: "chu",
        _639_3: {
            "chu": "Old Slavonic",
        },
    },
    {
        _NAMES: ["Chuvash"],
        _639_1: "cv",
        _639_2T: "chv",
        _639_2B: "chv",
        _639_3: {
            "chv": "Chuvash",
        },
    },
    {
        _NAMES: ["Cornish"],
        _639_1: "kw",
        _639_2T: "cor",
        _639_2B: "cor",
        _639_3: {
            "cor": "Cornish",
        },
    },
    {
        _NAMES: ["Corsican"],
        _639_1: "co",
        _639_2T: "cos",
        _639_2B: "cos",
        _639_3: {
            "cos": "Corsican",
        },
    },
    {
        _NAMES: ["Cree"],
        _639_1: "cr",
        _639_2T: "cre",
        _639_2B: "cre",
        _639_3: {
            "cre": "Cree",
            "crj": "Southern East Cree",
            "crk": "Plains Cree",
            "crl": "Northern East Cree",
            "crm": "Moose Cree",
            "csw": "Swampy Cree",
            "cwd": "Woods Cree",
        },
    },
    {
        _NAMES: ["Croatian"],
        _639_1: "hr",
        _639_2T: "hrv",
        _639_2B: "hrv",
        _639_3: {
            "hrv": "Croatian",
        },
    },
    {
        _NAMES: ["Czech"],
        _639_1: "cs",
        _639_2T: "ces",
        _639_2B: "cze",
        _639_3: {
            "ces": "Czech",
        },
    },
    {
        _NAMES: ["Danish"],
        _639_1: "da",
        _639_2T: "dan",
        _639_2B: "dan",
        _639_3: {
            "dan": "Danish",
        },
    },
    {
        _NAMES: ["Divehi", "Dhivehi", "Maldivian"],
        _639_1: "dv",
        _639_2T: "div",
        _639_2B: "div",
        _639_3: {
            "div": "Divehi",
        },
    },
    {
        _NAMES: ["Dutch", "Flemish"],
        _639_1: "nl",
        _639_2T: "nld",
        _639_2B: "dut",
        _639_3: {
            "nld": "Dutch",
        },
    },
    {
        _NAMES: ["Dzongkha"],
        _639_1: "dz",
        _639_2T: "dzo",
        _639_2B: "dzo",
        _639_3: {
            "dzo": "Dzongkha",
        },
    },
    {
        _NAMES: ["English"],
        _639_1: "en",
        _639_2T: "eng",
        _639_2B: "eng",
        _639_3: {
            "eng": "English",
        },
    },
    {
        _NAMES: ["Esperanto"],
        _639_1: "eo",
        _639_2T: "epo",
        _639_2B: "epo",
        _639_3: {
            "epo": "Esperanto",
        },
    },
    {
        _NAMES: ["Estonian"],
        _639_1: "et",
        _639_2T: "est",
        _639_2B: "est",
        _639_3: {
            "est": "Estonian",
            "ekk": "Standard Estonian",
            "vro": "Võro",
        },
    },
    {
        _NAMES: ["Ewe"],
        _639_1: "ee",
        _639_2T: "ewe",
        _639_2B: "ewe",
        _639_3: {
            "ewe": "Ewe",
        },
    },
    {
        _NAMES: ["Faroese"],
        _639_1: "fo",
        _639_2T: "fao",
        _639_2B: "fao",
        _639_3: {
            "fao": "Faroese",
        },
    },
    {
        _NAMES: ["Fijian"],
        _639_1: "fj",
        _639_2T: "fij",
        _639_2B: "fij",
        _639_3: {
            "fij": "Fijian",
        },
    },
    {
        _NAMES: ["Finnish"],
        _639_1: "fi",
        _639_2T: "fin",
        _639_2B: "fin",
        _639_3: {
            "fin": "Finnish",
        },
    },
    {
        _NAMES: ["French"],
        _639_1: "fr",
        _639_2T: "fra",
        _639_2B: "fre",
        _639_3: {
            "fra": "French",
        },
    },
    {
        _NAMES: ["Western Frisian"],
        _639_1: "fy",
        _639_2T: "fry",
        _639_2B: "fry",
        _639_3: {
            "fry": "Western Frisian",
        },
    },
    {
        _NAMES: ["Fulah"],
        _639_1: "ff",
        _639_2T: "ful",
        _639_2B: "ful",
        _639_3: {
            "ful": "Fulah",
            "ffm": "Maasina Fulfulde",
            "fub": "Adamawa Fulfulde",
            "fuc": "Pulaar",
            "fue": "Borgu Fulfulde",
            "fuf": "Pular",
            "fuh": "Western Niger Fulfulde",
            "fui": "Bagirmi Fulfulde",
            "fuq": "Central-Eastern Niger Fulfulde",
            "fuv": "Nigerian Fulfulde",
        },
    },
    {
        _NAMES: ["Gaelic", "Scottish Gaelic"],
        _639_1: "gd",
        _639_2T: "gla",
        _639_2B: "gla",
        _639_3: {
            "gla": "Gaelic",
        },
    },
    {
        _NAMES: ["Galician"],
        _639_1: "gl",
        _639_2T: "glg",
        _639_2B: "glg",
        _639_3: {
            "glg": "Galician",
        },
    },
    {
        _NAMES: ["Ganda"],
        _639_1: "lg",
        _639_2T: "lug",
        _639_2B: "lug",
        _639_3: {
            "lug": "Ganda",
        },
    },
    {
        _NAMES: ["Georgian"],
        _639_1: "ka",
        _639_2T: "kat",
        _639_2B: "geo",
        _639_3: {
            "kat": "Georgian",
        },
    },
    {
        _NAMES: ["German"],
        _639_1: "de",
        _639_2T: "deu",
        _639_2B: "ger",
        _639_3: {
            "deu": "German",
        },
    },
    {
        _NAMES: ["Greek", "Modern (1453-)"],
        _639_1: "el",
        _639_2T: "ell",
        _639_2B: "gre",
        _639_3: {
            "ell": "Greek",
        },
    },
    {
        _NAMES: ["Kalaallisut", "Greenlandic"],
        _639_1: "kl",
        _639_2T: "kal",
        _639_2B: "kal",
        _639_3: {
            "kal": "Kalaallisut",
        },
    },
    {
        _NAMES: ["Guarani"],
        _639_1: "gn",
        _639_2T: "grn",
        _639_2B: "grn",
        _639_3: {
            "grn": "Guarani",
            "gnw": "Western Bolivian Guaraní",
            "gug": "Paraguayan Guaraní",
            "gui": "Eastern Bolivian Guaraní",
            "gun": "Mbyá Guaraní",
            "nhd": "Chiripá",
        },
    },
    {
        _NAMES: ["Gujarati"],
        _639_1: "gu",
        _639_2T: "guj",
        _639_2B: "guj",
        _639_3: {
            "guj": "Gujarati",
        },
    },
    {
        _NAMES: ["Haitian", "Haitian Creole"],
        _639_1: "ht",
        _639_2T: "hat",
        _639_2B: "hat",
        _639_3: {
            "hat": "Haitian",
        },
    },
    {
        _NAMES: ["Hausa"],
        _639_1: "ha",
        _639_2T: "hau",
        _639_2B: "hau",
        _639_3: {
            "hau": "Hausa",
        },
    },
    {
        _NAMES: ["Hebrew"],
        _639_1: "he",
        _639_2T: "heb",
        _639_2B: "heb",
        _639_3: {
            "heb": "Hebrew",
        },
    },
    {
        _NAMES: ["Herero"],
        _639_1: "hz",
        _639_2T: "her",
        _639_2B: "her",
        _639_3: {
            "her": "Herero",
        },
    },
    {
        _NAMES: ["Hindi"],
        _639_1: "hi",
        _639_2T: "hin",
        _639_2B: "hin",
        _639_3: {
            "hin": "Hindi",
        },
    },
    {
        _NAMES: ["Hiri Motu"],
        _639_1: "ho",
        _639_2T: "hmo",
        _639_2B: "hmo",
        _639_3: {
            "hmo": "Hiri Motu",
        },
    },
    {
        _NAMES: ["Hungarian"],
        _639_1: "hu",
        _639_2T: "hun",
        _639_2B: "hun",
        _639_3: {
            "hun": "Hungarian",
        },
    },
    {
        _NAMES: ["Icelandic"],
        _639_1: "is",
        _639_2T: "isl",
        _639_2B: "ice",
        _639_3: {
            "isl": "Icelandic",
        },
    },
    {
        _NAMES: ["Ido"],
        _639_1: "io",
        _639_2T: "ido",
        _639_2B: "ido",
        _639_3: {
            "ido": "Ido",
        },
    },
    {
        _NAMES: ["Igbo"],
        _639_1: "ig",
        _639_2T: "ibo",
        _639_2B: "ibo",
        _639_3: {
            "ibo": "Igbo",
        },
    },
    {
        _NAMES: ["Indonesian"],
        _639_1: "id",
        _639_2T: "ind",
        _639_2B: "ind",
        _639_3: {
            "ind": "Indonesian",
        },
    },
    {
        _NAMES: ["Interlingua (International Auxiliary Language Association)"],
        _639_1: "ia",
        _639_2T: "ina",
        _639_2B: "ina",
        _639_3: {
            "ina": "Interlingua (International Auxiliary Language Association)",
        },
    },
    {
        _NAMES: ["Interlingue", "Occidental"],
        _639_1: "ie",
        _639_2T: "ile",
        _639_2B: "ile",
        _639_3: {
            "ile": "Interlingue",
        },
    },
    {
        _NAMES: ["Inuktitut"],
        _639_1: "iu",
        _639_2T: "iku",
        _639_2B: "iku",
        _639_3: {
            "iku": "Inuktitut",
            "ike": "Eastern Canadian Inuktitut",
            "ikt": "Inuinnaqtun",
        },
    },
    {
        _NAMES: ["Inupiaq"],
        _639_1: "ik",
        _639_2T: "ipk",
        _639_2B: "ipk",
        _639_3: {
            "ipk": "Inupiaq",
            "esi": "North Alaskan Inupiatun",
            "esk": "Northwest Alaska Inupiatun",
        },
    },
    {
        _NAMES: ["Irish"],
        _639_1: "ga",
        _639_2T: "gle",
        _639_2B: "gle",
        _639_3: {
            "gle": "Irish",
        },
    },
    {
        _NAMES: ["Italian"],
        _639_1: "it",
        _639_2T: "ita",
        _639_2B: "ita",
        _639_3: {
            "ita": "Italian",
        },
    },
    {
        _NAMES: ["Japanese"],
        _639_1: "ja",
        _639_2T: "jpn",
        _639_2B: "jpn",
        _639_3: {
            "jpn": "Japanese",
        },
    },
    {
        _NAMES: ["Javanese"],
        _639_1: "jv",
        _639_2T: "jav",
        _639_2B: "jav",
        _639_3: {
            "jav": "Javanese",
        },
    },
    {
        _NAMES: ["Kannada"],
        _639_1: "kn",
        _639_2T: "kan",
        _639_2B: "kan",
        _639_3: {
            "kan": "Kannada",
        },
    },
    {
        _NAMES: ["Kanuri"],
        _639_1: "kr",
        _639_2T: "kau",
        _639_2B: "kau",
        _639_3: {
            "kau": "Kanuri",
            "kby": "Manga Kanuri",
            "knc": "Central Kanuri",
            "krt": "Tumari Kanuri",
        },
    },
    {
        _NAMES: ["Kashmiri"],
        _639_1: "ks",
        _639_2T: "kas",
        _639_2B: "kas",
        _639_3: {
            "kas": "Kashmiri",
        },
    },
    {
        _NAMES: ["Kazakh"],
        _639_1: "kk",
        _639_2T: "kaz",
        _639_2B: "kaz",
        _639_3: {
            "kaz": "Kazakh",
        },
    },
    {
        _NAMES: ["Central Khmer"],
        _639_1: "km",
        _639_2T: "khm",
        _639_2B: "khm",
        _639_3: {
            "khm": "Central Khmer",
        },
    },
    {
        _NAMES: ["Kikuyu", "Gikuyu"],
        _639_1: "ki",
        _639_2T: "kik",
        _639_2B: "kik",
        _639_3: {
            "kik": "Kikuyu",
        },
    },
    {
        _NAMES: ["Kinyarwanda"],
        _639_1: "rw",
        _639_2T: "kin",
        _639_2B: "kin",
        _639_3: {
            "kin": "Kinyarwanda",
        },
    },
    {
        _NAMES: ["Kirghiz", "Kyrgyz"],
        _639_1: "ky",
        _639_2T: "kir",
        _639_2B: "kir",
        _639_3: {
            "kir": "Kirghiz",
        },
    },
    {
        _NAMES: ["Komi"],
        _639_1: "kv",
        _639_2T: "kom",
        _639_2B: "kom",
        _639_3: {
            "kom": "Komi",
            "koi": "Komi-Permyak",
            "kpv": "Komi-Zyrian",
        },
    },
    {
        _NAMES: ["Kongo"],
        _639_1: "kg",
        _639_2T: "kon",
        _639_2B: "kon",
        _639_3: {
            "kon": "Kongo",
            "kng": "Koongo",
            "kwy": "San Salvador Kongo",
            "ldi": "Laari",
        },
    },
    {
        _NAMES: ["Korean"],
        _639_1: "ko",
        _639_2T: "kor",
        _639_2B: "kor",
        _639_3: {
            "kor": "Korean",
        },
    },
    {
        _NAMES: ["Kuanyama", "Kwanyama"],
        _639_1: "kj",
        _639_2T: "kua",
        _639_2B: "kua",
        _639_3: {
            "kua": "Kuanyama",
        },
    },
    {
        _NAMES: ["Kurdish"],
        _639_1: "ku",
        _639_2T: "kur",
        _639_2B: "kur",
        _639_3: {
            "kur": "Kurdish",
            "ckb": "Central Kurdish",
            "kmr": "Northern Kurdish",
            "sdh": "Southern Kurdish",
        },
    },
    {
        _NAMES: ["Lao"],
        _639_1: "lo",
        _639_2T: "lao",
        _639_2B: "lao",
        _639_3: {
            "lao": "Lao",
        },
    },
    {
        _NAMES: ["Latin"],
        _639_1: "la",
        _639_2T: "lat",
        _639_2B: "lat",
        _639_3: {
            "lat": "Latin",
        },
    },
    {
        _NAMES: ["Latvian"],
        _639_1: "lv",
        _639_2T: "lav",
        _639_2B: "lav",
        _639_3: {
            "lav": "Latvian",
            "ltg": "Latgalian",
            "lvs": "Standard Latvian",
        },
    },
    {
        _NAMES: ["Limburgan", "Limburger", "Limburgish"],
        _639_1: "li",
        _639_2T: "lim",
        _639_2B: "lim",
        _639_3: {
            "lim": "Limburgan",
        },
    },
    {
        _NAMES: ["Lingala"],
        _639_1: "ln",
        _639_2T: "lin",
        _639_2B: "lin",
        _639_3: {
            "lin": "Lingala",
        },
    },
    {
        _NAMES: ["Lithuanian"],
        _639_1: "lt",
        _639_2T: "lit",
        _639_2B: "lit",
        _639_3: {
            "lit": "Lithuanian",
        },
    },
    {
        _NAMES: ["Luba-Katanga"],
        _639_1: "lu",
        _639_2T: "lub",
        _639_2B: "lub",
        _639_3: {
            "lub": "Luba-Katanga",
        },
    },
    {
        _NAMES: ["Luxembourgish", "Letzeburgesch"],
        _639_1: "lb",
        _639_2T: "ltz",
        _639_2B: "ltz",
        _639_3: {
            "ltz": "Luxembourgish",
        },
    },
    {
        _NAMES: ["Macedonian"],
        _639_1: "mk",
        _639_2T: "mkd",
        _639_2B: "mac",
        _639_3: {
            "mkd": "Macedonian",
        },
    },
    {
        _NAMES: ["Malagasy"],
        _639_1: "mg",
        _639_2T: "mlg",
        _639_2B: "mlg",
        _639_3: {
            "mlg": "Malagasy",
            "bhr": "Bara Malagasy",
            "bmm": "Northern Betsimisaraka Malagasy",
            "bzc": "Southern Betsimisaraka Malagasy",
            "msh": "Masikoro Malagasy",
            "plt": "Plateau Malagasy",
            "skg": "Sakalava Malagasy",
            "tdx": "Tandroy-Mahafaly Malagasy",
            "tkg": "Tesaka Malagasy",
            "txy": "Tanosy Malagasy",
            "xmv": "Antankarana Malagasy",
            "xmw": "Tsimihety Malagasy",
        },
    },
    {
        _NAMES: ["Malay"],
        _639_1: "ms",
        _639_2T: "msa",
        _639_2B: "may",
        _639_3: {
            "msa": "Malay",
            "bjn": "Banjar",
            "btj": "Bacanese Malay",
            "bve": "Berau Malay",
            "bvu": "Bukit Malay",
            "coa": "Cocos Islands Malay",
            "dup": "Duano",
            "hji": "Haji",
            "ind": "Indonesian",
            "jak": "Jakun",
            "jax": "Jambi Malay",
            "kvb": "Kubu",
            "kvr": "Kerinci",
            "kxd": "Brunei",
            "lce": "Loncong",
            "lcf": "Lubu",
            "liw": "Col",
            "max": "North Moluccan Malay",
            "meo": "Kedah Malay",
            "mfa": "Pattani Malay",
            "mfb": "Bangka",
            "min": "Minangkabau",
            "mqg": "Kota Bangun Kutai Malay",
            "msi": "Sabah Malay",
            "mui": "Musi",
            "orn": "Orang Kanaq",
            "ors": "Orang Seletar",
            "pel": "Pekal",
            "pse": "Central Malay",
            "tmw": "Temuan",
            "urk": "Urak Lawoi'",
            "vkk": "Kaur",
            "vkt": "Tenggarong Kutai Malay",
            "xmm": "Manado Malay",
            "zlm": "Malay (individual language)",
            "zmi": "Negeri Sembilan Malay",
            "zsm": "Standard Malay",
        },
    },
    {
        _NAMES: ["Malayalam"],
        _639_1: "ml",
        _639_2T: "mal",
        _639_2B: "mal",
        _639_3: {
            "mal": "Malayalam",
        },
    },
    {
        _NAMES: ["Maltese"],
        _639_1: "mt",
        _639_2T: "mlt",
        _639_2B: "mlt",
        _639_3: {
            "mlt": "Maltese",
        },
    },
    {
        _NAMES: ["Manx"],
        _639_1: "gv",
        _639_2T: "glv",
        _639_2B: "glv",
        _639_3: {
            "glv": "Manx",
        },
    },
    {
        _NAMES: ["Maori"],
        _639_1: "mi",
        _639_2T: "mri",
        _639_2B: "mao",
        _639_3: {
            "mri": "Maori",
        },
    },
    {
        _NAMES: ["Marathi"],
        _639_1: "mr",
        _639_2T: "mar",
        _639_2B: "mar",
        _639_3: {
            "mar": "Marathi",
        },
    },
    {
        _NAMES: ["Marshallese"],
        _639_1: "mh",
        _639_2T: "mah",
        _639_2B: "mah",
        _639_3: {
            "mah": "Marshallese",
        },
    },
    {
        _NAMES: ["Mongolian"],
        _639_1: "mn",
        _639_2T: "mon",
        _639_2B: "mon",
        _639_3: {
            "mon": "Mongolian",
            "khk": "Halh Mongolian",
            "mvf": "Peripheral Mongolian",
        },
    },
    {
        _NAMES: ["Nauru"],
        _639_1: "na",
        _639_2T: "nau",
        _639_2B: "nau",
        _639_3: {
            "nau": "Nauru",
        },
    },
    {
        _NAMES: ["Navajo", "Navaho"],
        _639_1: "nv",
        _639_2T: "nav",
        _639_2B: "nav",
        _639_3: {
            "nav": "Navajo",
        },
    },
    {
        _NAMES: ["North Ndebele"],
        _639_1: "nd",
        _639_2T: "nde",
        _639_2B: "nde",
        _639_3: {
            "nde": "North Ndebele",
        },
    },
    {
        _NAMES: ["South Ndebele"],
        _639_1: "nr",
        _639_2T: "nbl",
        _639_2B: "nbl",
        _639_3: {
            "nbl": "South Ndebele",
        },
    },
    {
        _NAMES: ["Ndonga"],
        _639_1: "ng",
        _639_2T: "ndo",
        _639_2B: "ndo",
        _639_3: {
            "ndo": "Ndonga",
        },
    },
    {
        _NAMES: ["Nepali"],
        _639_1: "ne",
        _639_2T: "nep",
        _639_2B: "nep",
        _639_3: {
            "nep": "Nepali",
            "dty": "Dotyali",
            "npi": "Nepali",
        },
    },
    {
        _NAMES: ["Norwegian"],
        _639_1: "no",
        _639_2T: "nor",
        _639_2B: "nor",
        _639_3: {
            "nor": "Norwegian",
            "nno": "Norwegian Nynorsk",
            "nob": "Norwegian Bokmål",
        },
    },
    {
        _NAMES: ["Sichuan Yi", "Nuosu"],
        _639_1: "ii",
        _639_2T: "iii",
        _639_2B: "iii",
        _639_3: {
            "iii": "Sichuan Yi",
        },
    },
    {
        _NAMES: ["Occitan"],
        _639_1: "oc",
        _639_2T: "oci",
        _639_2B: "oci",
        _639_3: {
            "oci": "Occitan",
        },
    },
    {
        _NAMES: ["Ojibwa"],
        _639_1: "oj",
        _639_2T: "oji",
        _639_2B: "oji",
        _639_3: {
            "oji": "Ojibwa",
            "ciw": "Chippewa",
            "ojb": "Northwestern Ojibwa",
            "ojc": "Central Ojibwa",
            "ojg": "Eastern Ojibwa",
            "ojs": "Severn Ojibwa",
            "ojw": "Western Ojibwa",
            "otw": "Ottawa",
        },
    },
    {
        _NAMES: ["Oriya"],
        _639_1: "or",
        _639_2T: "ori",
        _639_2B: "ori",
        _639_3: {
            "ori": "Oriya",
            "ory": "Odia",
            "spv": "Sambalpuri",
        },
    },
    {
        _NAMES: ["Oromo"],
        _639_1: "om",
        _639_2T: "orm",
        _639_2B: "orm",
        _639_3: {
            "orm": "Oromo",
            "gax": "Borana-Arsi-Guji Oromo",
            "gaz": "West Central Oromo",
            "hae": "Eastern Oromo",
            "orc": "Orma",
        },
    },
    {
        _NAMES: ["Ossetian", "Ossetic"],
        _639_1: "os",
        _639_2T: "oss",
        _639_2B: "oss",
        _639_3: {
            "oss": "Ossetian",
        },
    },
    {
        _NAMES: ["Pali"],
        _639_1: "pi",
        _639_2T: "pli",
        _639_2B: "pli",
        _639_3: {
            "pli": "Pali",
        },
    },
    {
        _NAMES: ["Pashto", "Pushto"],
        _639_1: "ps",
        _639_2T: "pus",
        _639_2B: "pus",
        _639_3: {
            "pus": "Pashto",
            "pbt": "Southern Pashto",
            "pbu": "Northern Pashto",
            "pst": "Central Pashto",
        },
    },
    {
        _NAMES: ["Persian"],
        _639_1: "fa",
        _639_2T: "fas",
        _639_2B: "per",
        _639_3: {
            "fas": "Persian",
            "pes": "Iranian Persian",
            "prs": "Dari",
        },
    },
    {
        _NAMES: ["Polish"],
        _639_1: "pl",
        _639_2T: "pol",
        _639_2B: "pol",
        _639_3: {
            "pol": "Polish",
        },
    },
    {
        _NAMES: ["Portuguese"],
        _639_1: "pt",
        _639_2T: "por",
        _639_2B: "por",
        _639_3: {
            "por": "Portuguese",
        },
    },
    {
        _NAMES: ["Punjabi", "Panjabi"],
        _639_1: "pa",
        _639_2T: "pan",
        _639_2B: "pan",
        _639_3: {
            "pan": "Punjabi",
        },
    },
    {
        _NAMES: ["Quechua"],
        _639_1: "qu",
        _639_2T: "que",
        _639_2B: "que",
        _639_3: {
            "que": "Quechua",
            "qub": "Huallaga Huánuco Quechua",
            "qud": "Calderón Highland Quichua",
            "quf": "Lambayeque Quechua",
            "qug": "Chimborazo Highland Quichua",
            "quh": "South Bolivian Quechua",
            "quk": "Chachapoyas Quechua",
            "qul": "North Bolivian Quechua",
            "qup": "Southern Pastaza Quechua",
            "qur": "Yanahuanca Pasco Quechua",
            "qus": "Santiago del Estero Quichua",
            "quw": "Tena Lowland Quichua",
            "qux": "Yauyos Quechua",
            "quy": "Ayacucho Quechua",
            "quz": "Cusco Quechua",
            "qva": "Ambo-Pasco Quechua",
            "qvc": "Cajamarca Quechua",
            "qve": "Eastern Apurímac Quechua",
            "qvh": "Huamalíes-Dos de Mayo Huánuco Quechua",
            "qvi": "Imbabura Highland Quichua",
            "qvj": "Loja Highland Quichua",
            "qvl": "Cajatambo North Lima Quechua",
            "qvm": "Margos-Yarowilca-Lauricocha Quechua",
            "qvn": "North Junín Quechua",
            "qvo": "Napo Lowland Quechua",
            "qvp": "Pacaraos Quechua",
            "qvs": "San Martín Quechua",
            "qvw": "Huaylla Wanca Quechua",
            "qvz": "Northern Pastaza Quichua",
            "qwa": "Corongo Ancash Quechua",
            "qwc": "Classical Quechua",
            "qwh": "Huaylas Ancash Quechua",
            "qws": "Sihuas Ancash Quechua",
            "qxa": "Chiquián Ancash Quechua",
            "qxc": "Chincha Quechua",
            "qxh": "Panao Huánuco Quechua",
            "qxl": "Salasaca Highland Quichua",
            "qxn": "Northern Conchucos Ancash Quechua",
            "qxo": "Southern Conchucos Ancash Quechua",
            "qxp": "Puno Quechua",
            "qxr": "Cañar Highland Quichua",
            "qxt": "Santa Ana de Tusi Pasco Quechua",
            "qxu": "Arequipa-La Unión Quechua",
            "qxw": "Jauja Wanca Quechua",
        },
    },
    {
        _NAMES: ["Romanian", "Moldavian", "Moldovan"],
        _639_1: "ro",
        _639_2T: "ron",
        _639_2B: "rum",
        _639_3: {
            "ron": "Romanian",
        },
    },
    {
        _NAMES: ["Romansh"],
        _639_1: "rm",
        _639_2T: "roh",
        _639_2B: "roh",
        _639_3: {
            "roh": "Romansh",
        },
    },
    {
        _NAMES: ["Rundi"],
        _639_1: "rn",
        _639_2T: "run",
        _639_2B: "run",
        _639_3: {
            "run": "Rundi",
        },
    },
    {
        _NAMES: ["Russian"],
        _639_1: "ru",
        _639_2T: "rus",
        _639_2B: "rus",
        _639_3: {
            "rus": "Russian",
        },
    },
    {
        _NAMES: ["Northern Sami"],
        _639_1: "se",
        _639_2T: "sme",
        _639_2B: "sme",
        _639_3: {
            "sme": "Northern Sami",
        },
    },
    {
        _NAMES: ["Samoan"],
        _639_1: "sm",
        _639_2T: "smo",
        _639_2B: "smo",
        _639_3: {
            "smo": "Samoan",
        },
    },
    {
        _NAMES: ["Sango"],
        _639_1: "sg",
        _639_2T: "sag",
        _639_2B: "sag",
        _639_3: {
            "sag": "Sango",
        },
    },
    {
        _NAMES: ["Sanskrit"],
        _639_1: "sa",
        _639_2T: "san",
        _639_2B: "san",
        _639_3: {
            "san": "Sanskrit",
        },
    },
    {
        _NAMES: ["Sardinian"],
        _639_1: "sc",
        _639_2T: "srd",
        _639_2B: "srd",
        _639_3: {
            "srd": "Sardinian",
            "sdc": "Sassarese Sardinian",
            "sdn": "Gallurese Sardinian",
            "src": "Logudorese Sardinian",
            "sro": "Campidanese Sardinian",
        },
    },
    {
        _NAMES: ["Serbian"],
        _639_1: "sr",
        _639_2T: "srp",
        _639_2B: "srp",
        _639_3: {
            "srp": "Serbian",
        },
    },
    {
        _NAMES: ["Shona"],
        _639_1: "sn",
        _639_2T: "sna",
        _639_2B: "sna",
        _639_3: {
            "sna": "Shona",
        },
    },
    {
        _NAMES: ["Sindhi"],
        _639_1: "sd",
        _639_2T: "snd",
        _639_2B: "snd",
        _639_3: {
            "snd": "Sindhi",
        },
    },
    {
        _NAMES: ["Sinhala", "Sinhalese"],
        _639_1: "si",
        _639_2T: "sin",
        _639_2B: "sin",
        _639_3: {
            "sin": "Sinhala",
        },
    },
    {
        _NAMES: ["Slovak"],
        _639_1: "sk",
        _639_2T: "slk",
        _639_2B: "slo",
        _639_3: {
            "slk": "Slovak",
        },
    },
    {
        _NAMES: ["Slovenian"],
        _639_1: "sl",
        _639_2T: "slv",
        _639_2B: "slv",
        _639_3: {
            "slv": "Slovenian",
        },
    },
    {
        _NAMES: ["Somali"],
        _639_1: "so",
        _639_2T: "som",
        _639_2B: "som",
        _639_3: {
            "som": "Somali",
        },
    },
    {
        _NAMES: ["Southern Sotho"],
        _639_1: "st",
        _639_2T: "sot",
        _639_2B: "sot",
        _639_3: {
            "sot": "Southern",
        },
    },
    {
        _NAMES: ["Spanish", "Castilian"],
        _639_1: "es",
        _639_2T: "spa",
        _639_2B: "spa",
        _639_3: {
            "spa": "Spanish",
        },
    },
    {
        _NAMES: ["Sundanese"],
        _639_1: "su",
        _639_2T: "sun",
        _639_2B: "sun",
        _639_3: {
            "sun": "Sundanese",
        },
    },
    {
        _NAMES: ["Swahili"],
        _639_1: "sw",
        _639_2T: "swa",
        _639_2B: "swa",
        _639_3: {
            "swa": "Swahili",
            "swc": "Congo Swahili",
            "swh": "Swahili",
        },
    },
    {
        _NAMES: ["Swati"],
        _639_1: "ss",
        _639_2T: "ssw",
        _639_2B: "ssw",
        _639_3: {
            "ssw": "Swati",
        },
    },
    {
        _NAMES: ["Swedish"],
        _639_1: "sv",
        _639_2T: "swe",
        _639_2B: "swe",
        _639_3: {
            "swe": "Swedish",
        },
    },
    {
        _NAMES: ["Tagalog"],
        _639_1: "tl",
        _639_2T: "tgl",
        _639_2B: "tgl",
        _639_3: {
            "tgl": "Tagalog",
        },
    },
    {
        _NAMES: ["Tahitian"],
        _639_1: "ty",
        _639_2T: "tah",
        _639_2B: "tah",
        _639_3: {
            "tah": "Tahitian",
        },
    },
    {
        _NAMES: ["Tajik"],
        _639_1: "tg",
        _639_2T: "tgk",
        _639_2B: "tgk",
        _639_3: {
            "tgk": "Tajik",
        },
    },
    {
        _NAMES: ["Tamil"],
        _639_1: "ta",
        _639_2T: "tam",
        _639_2B: "tam",
        _639_3: {
            "tam": "Tamil",
        },
    },
    {
        _NAMES: ["Tatar"],
        _639_1: "tt",
        _639_2T: "tat",
        _639_2B: "tat",
        _639_3: {
            "tat": "Tatar",
        },
    },
    {
        _NAMES: ["Telugu"],
        _639_1: "te",
        _639_2T: "tel",
        _639_2B: "tel",
        _639_3: {
            "tel": "Telugu",
        },
    },
    {
        _NAMES: ["Thai"],
        _639_1: "th",
        _639_2T: "tha",
        _639_2B: "tha",
        _639_3: {
            "tha": "Thai",
        },
    },
    {
        _NAMES: ["Tibetan"],
        _639_1: "bo",
        _639_2T: "bod",
        _639_2B: "tib",
        _639_3: {
            "bod": "Tibetan",
        },
    },
    {
        _NAMES: ["Tigrinya"],
        _639_1: "ti",
        _639_2T: "tir",
        _639_2B: "tir",
        _639_3: {
            "tir": "Tigrinya",
        },
    },
    {
        _NAMES: ["Tonga (Tonga Islands)"],
        _639_1: "to",
        _639_2T: "ton",
        _639_2B: "ton",
        _639_3: {
            "ton": "Tonga (Tonga Islands)",
        },
    },
    {
        _NAMES: ["Tsonga"],
        _639_1: "ts",
        _639_2T: "tso",
        _639_2B: "tso",
        _639_3: {
            "tso": "Tsonga",
        },
    },
    {
        _NAMES: ["Tswana"],
        _639_1: "tn",
        _639_2T: "tsn",
        _639_2B: "tsn",
        _639_3: {
            "tsn": "Tswana",
        },
    },
    {
        _NAMES: ["Turkish"],
        _639_1: "tr",
        _639_2T: "tur",
        _639_2B: "tur",
        _639_3: {
            "tur": "Turkish",
        },
    },
    {
        _NAMES: ["Turkmen"],
        _639_1: "tk",
        _639_2T: "tuk",
        _639_2B: "tuk",
        _639_3: {
            "tuk": "Turkmen",
        },
    },
    {
        _NAMES: ["Twi"],
        _639_1: "tw",
        _639_2T: "twi",
        _639_2B: "twi",
        _639_3: {
            "twi": "Twi",
        },
    },
    {
        _NAMES: ["Uighur", "Uyghur"],
        _639_1: "ug",
        _639_2T: "uig",
        _639_2B: "uig",
        _639_3: {
            "uig": "Uighur",
        },
    },
    {
        _NAMES: ["Ukrainian"],
        _639_1: "uk",
        _639_2T: "ukr",
        _639_2B: "ukr",
        _639_3: {
            "ukr": "Ukrainian",
        },
    },
    {
        _NAMES: ["Urdu"],
        _639_1: "ur",
        _639_2T: "urd",
        _639_2B: "urd",
        _639_3: {
            "urd": "Urdu",
        },
    },
    {
        _NAMES: ["Uzbek"],
        _639_1: "uz",
        _639_2T: "uzb",
        _639_2B: "uzb",
        _639_3: {
            "uzb": "Uzbek",
            "uzn": "Northern Uzbek",
            "uzs": "Southern Uzbek",
        },
    },
    {
        _NAMES: ["Venda"],
        _639_1: "ve",
        _639_2T: "ven",
        _639_2B: "ven",
        _639_3: {
            "ven": "Venda",
        },
    },
    {
        _NAMES: ["Vietnamese"],
        _639_1: "vi",
        _639_2T: "vie",
        _639_2B: "vie",
        _639_3: {
            "vie": "Vietnamese",
        },
    },
    {
        _NAMES: ["Volapük"],
        _639_1: "vo",
        _639_2T: "vol",
        _639_2B: "vol",
        _639_3: {
            "vol": "Volapük",
        },
    },
    {
        _NAMES: ["Walloon"],
        _639_1: "wa",
        _639_2T: "wln",
        _639_2B: "wln",
        _639_3: {
            "wln": "Walloon",
        },
    },
    {
        _NAMES: ["Welsh"],
        _639_1: "cy",
        _639_2T: "cym",
        _639_2B: "wel",
        _639_3: {
            "cym": "Welsh",
        },
    },
    {
        _NAMES: ["Wolof"],
        _639_1: "wo",
        _639_2T: "wol",
        _639_2B: "wol",
        _639_3: {
            "wol": "Wolof",
        },
    },
    {
        _NAMES: ["Xhosa"],
        _639_1: "xh",
        _639_2T: "xho",
        _639_2B: "xho",
        _639_3: {
            "xho": "Xhosa",
        },
    },
    {
        _NAMES: ["Yiddish"],
        _639_1: "yi",
        _639_2T: "yid",
        _639_2B: "yid",
        _639_3: {
            "yid": "Yiddish",
            "ydd": "Eastern Yiddish",
            "yih": "Western Yiddish",
        },
    },
    {
        _NAMES: ["Yoruba"],
        _639_1: "yo",
        _639_2T: "yor",
        _639_2B: "yor",
        _639_3: {
            "yor": "Yoruba",
        },
    },
    {
        _NAMES: ["Zhuang", "Chuang"],
        _639_1: "za",
        _639_2T: "zha",
        _639_2B: "zha",
        _639_3: {
            "zha": "Zhuang",
            "zch": "Central Hongshuihe Zhuang",
            "zeh": "Eastern Hongshuihe Zhuang",
            "zgb": "Guibei Zhuang",
            "zgm": "Minz Zhuang",
            "zgn": "Guibian Zhuang",
            "zhd": "Dai Zhuang",
            "zhn": "Nong Zhuang",
            "zlj": "Liujiang Zhuang",
            "zln": "Lianshan Zhuang",
            "zlq": "Liuqian Zhuang",
            "zqe": "Qiubei Zhuang",
            "zyb": "Yongbei Zhuang",
            "zyg": "Yang Zhuang",
            "zyj": "Youjiang Zhuang",
            "zyn": "Yongnan Zhuang",
            "zzj": "Zuojiang Zhuang",
        },
    },
    {
        _NAMES: ["Zulu"],
        _639_1: "zu",
        _639_2T: "zul",
        _639_2B: "zul",
        _639_3: {
            "zul": "Zulu",
        },
    },
]

LANGUAGES_BY_NAMES = {
    key.casefold(): lang for lang in LANGUAGES for key in lang[_NAMES]
}
LANGUAGES_BY_639_1 = {lang[_639_1]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_2T = {lang[_639_2T]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_2B = {lang[_639_2B]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_3 = {
    key.casefold(): lang for lang in LANGUAGES for key in lang[_639_3]
}
LANGUAGES_BY_NAME_AND_639_1_AND_639_2T = {
    lang["names"][0]: (lang[_639_1], lang[_639_2T]) for lang in LANGUAGES
}

LANGUAGES_INDEXED_BY: dict[str, dict[Any, dict[str, Any]]] = {
    _NAMES: LANGUAGES_BY_NAMES,
    _639_1: LANGUAGES_BY_639_1,
    _639_2T: LANGUAGES_BY_639_2T,
    _639_2B: LANGUAGES_BY_639_2B,
    _639_3: LANGUAGES_BY_639_3,
}
