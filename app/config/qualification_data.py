# config/qualification_data.py

kt = {
    "Ehitusjuht, TASE 6": {
        "costs": {
            "oneActivity": {
                "firstTime": 372.10,
                "renewal": 303.78
            },
            "extraActivity": {
                "firstTime": 79.31,
                "renewal": 54.83
            },
        },
        "Üldehituslik ehitamine": [
            "Kivi- ja betoonkonstruktsioonide ehitamine",
            "Puitkonstruktsioonide ehitamine",
            "Teraskonstruktsioonide ehitamine",
            "Lammutustööde tegemine",
            "Fassaaditööde tegemine"
        ],
        "Sisekliima tagamise süsteemide ehitamine": [
            "Küttesüsteemide ehitamine",
            "Jahutussüsteemide ehitamine",
            "Ventilatsioonisüsteemide ehitamine"
        ],
        "Hoonesisese ja selle juurde kuuluva vee- ja kanalisatsioonisüsteemi ehitamine": [
            "Valikkompetentsid puuduvad"
        ],
        "Ühisveevärgi või kanalisatsiooni ehitamine": [
            "Valikkompetentsid puuduvad"
        ],
        "[OJV] Üldehitusliku ehitamise omanikujärelevalve tegemine": [
            "Valikkompetentsid puuduvad"
        ],
        "[OJV] Sisekliima tagamise süsteemide ehitamise omanikujärelevalve tegemine": [
            "Valikkompetentsid puuduvad"
        ],
        "[OJV] Hoonesisese ja selle juurde kuuluva veevarustus- ja kanalisatsioonisüsteemi ehitamise omanikujärelevalve tegemine": [
            "Valikkompetentsid puuduvad"
        ]
    },
    "Ehituse tööjuht, TASE 5": {
        "costs": {
            "oneActivity": {
                "firstTime": 372.10,
                "renewal": 303.78
            },
            "extraActivity": {
                "firstTime": 79.31,
                "renewal": 54.83
            },
        },
        "Üldehituslik ehitamine": [
            "Kivikonstruktsioonide ehitamine",
            "Betoonkonstruktsioonide ehitamine",
            "Puitkonstruktsioonide ehitamine",
            "Monteeritavate ehituskonstruktsioonide paigaldamine"
        ],
        "Sisekliima tagamise süsteemide ehitamine": [
            "Küttesüsteemide ehitamine",
            "Jahutussüsteemide ehitamine",
            "Ventilatsioonisüsteemide ehitamine"
        ],
        "Hoonesisese ja selle juurde kuuluva vee- ja kanalisatsioonisüsteemi ehitamine": [
            "Valikkompetentsid puuduvad"
        ],
        "Eriehitustööde tegemine": [
            "Lamekatuste ehitamine",
            "Kaldkatuste ehitamine",
            "Ehitusplekksepatööde tegemine"
        ],
        "Ehitusviimistlustööde tegemine": [
            "Maalritööde tegemine",
            "Plaatimistööde tegemine",
            "Põrandakatmistööde tegemine",
            "Krohvimistööde tegemine"
        ]
    },
    "Oskustööline, TASE 4": {
        "costs": {
            "eriehitustööd": {
                "firstTime": 311.10,
                "renewal": 76.86
            },
            "muudTegevusalad": {
                "oneActivity": {
                    "firstTime": 103.70,
                    "renewal": 63.44
                },
                "extraActivity": {
                    "firstTime": 75.64,
                    "renewal": None
                }
            }
        },
        "Üldehitus ja ehitusviimistlus": [
            "Betoonkonstruktsioonide ehitaja",
            "Ehituspuusepp",
            "Müürsepp",
            "Maaler",
            "Plaatija",
            "Põrandakatja",
            "Krohvija"
        ],
        "Keskkonnatehnika": [
            "Kütte- ja jahutussüsteemide lukksepp",
            "Veevärgilukksepp",
            "Ventilatsioonilukksepp"
        ]
    }
}

QUALIFICATION_LEVEL_STYLES = {
    "Ehitusjuht, TASE 6": {
        "abbr": "EJ6",
        "class": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
    },
    "Ehituse tööjuht, TASE 5": {
        "abbr": "ETJ5", # As seen in evaluator.py
        "class": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
    },
    "Oskustööline, TASE 4": {
        "abbr": "OT4",
        "class": "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
    },
    # Add a fallback for any other cases
    "default": {
        "abbr": "N/A",
        "class": "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
    }
}