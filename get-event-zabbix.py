import json
from dotenv import dotenv_values
from flask import Flask
from flask_cors import CORS
from zabbix_api import ZabbixAPI

# Load environment variables from .env file
env_vars = dotenv_values()

URL = "https://zabbix.devops.rentcars.com/api_jsonrpc.php"
USERNAME = env_vars.get("USERNAME")
PASSWORD = env_vars.get("PASSWORD")

app = Flask(__name__)
CORS(app)

@app.route('/geteventzabbix')
def getEventZabbix():
    # Conectar ao Zabbix API
    try:
        zapi = ZabbixAPI(URL, timeout=180)
        zapi.login(USERNAME, PASSWORD)
        print("Connected to Zabbix API Version %s" % zapi.api_version())
    except Exception as e:
        print("Failed to connect to Zabbix API, error: %s" % e)
        exit()

    # Obter os hosts
    hosts = zapi.host.get({
        "output": "extend",
        "filter": {"host": "name"},
        "selectGroups": "extend"
    })

    # Obter o hostgroup do web cenário
    hostgroup = zapi.hostgroup.get({
        "output": "extend",
        "filter": {"name": "Monitoramento de Web Cenário"}
    })

    # Verificar se o hostgroup foi encontrado
    if hostgroup:
        hostgroup_id = hostgroup[0]['groupid']

        # Obter os hosts do hostgroup
        hosts = zapi.host.get({
            "output": ["hostid", "host"],
            "groupids": hostgroup_id
        })

        print("hosts:", hosts)

    # Obter as triggers dos hosts
    for host in hosts:
        # Triggers com problemas
        triggers_with_problems = zapi.trigger.get({
            "output": ["description", "priority"],
            "filter": {"value": 1}, # 1 = Problema
            "hostids": host['hostid'],
            "sortfield": "priority",
            "sortorder": "DESC",
            "min_severity": 4,
            "monitored": True,
            "skipDependent": True,
            "expandDescription": True
        })

        # Triggers OK
        triggers_ok = zapi.trigger.get({
            "output": ["description", "priority"],
            "filter": {"value": 0}, # 0 = OK
            "hostids": host['hostid'],
            "sortfield": "priority",
            "sortorder": "DESC",
            "min_severity": 4,
            "monitored": True,
            "skipDependent": True,
            "expandDescription": True
        })
        
    # Criar uma lista de todas as triggers
    all_triggers = []
    for trigger in triggers_with_problems:
        all_triggers.append({
            'host': host['host'],
            'description': trigger['description'],
            'priority': trigger['priority'],
            'status': 'Problema'
        })

    for trigger in triggers_ok:
        all_triggers.append({
            'host': host['host'],
            'description': trigger['description'],
            'priority': trigger['priority'],
            'status': 'OK'
        })

    desired_hostid = "10715"

    # Obter o ID do host desejado
    hostgroups = zapi.hostgroup.get({
        "output": "extend",
        "hostids": desired_hostid
    })

    # Filtrar pelo hostid desejado
    hosts = [host for host in hosts if host['hostid'] == desired_hostid]

    # Obter os cenários de monitoramento da web do host
    if (hosts):    
        httptests = zapi.httptest.get({
            "output": "extend",
            "hostids": desired_hostid,
            "selectSteps": ["url"]  # Aqui estamos ajustando a saída para incluir apenas o campo 'url'
        })

        # Conjunto para armazenar as URLs únicas
        unique_urls = set()

        # Adicionar a URL de cada etapa de cada cenário de monitoramento da web ao conjunto
        for httptest in httptests:
            if httptest['hostid'] == desired_hostid:  # Verificar se o hostid corresponde
                for step in httptest['steps']:
                    unique_urls.add(step['url'])

    descriptions_problem = [linha_problem['description'].lower().split('\"')[1].split('rentcars.com')[-1].split('rentcars')[-1] if '\"' in linha_problem['description'] else linha_problem['description'].lower().split('rentcars.com')[-1].split('rentcars')[-1] for linha_problem in triggers_with_problems]

    # Verificar se httptests está vazio
    if httptests:
        # Cria uma lista de URLs
        url_list = []
        for httptest in httptests:
            # print("httptest: ", httptest)  # Debug: imprimir httptest
            for step in httptest['steps']:
                # print("step: ", step)  # Debug: imprimir step
                if 'url' in step:
                    url_list.append(step['url'])
                else:
                    print("A chave 'url' não está presente em step: ", step)

    description_list = descriptions_problem
    
    description_url_dict = {}
    
    def add_description_url(description, url):
        description_url_dict[description] = url

    printed = set()  # Conjunto para armazenar descrições e URLs já impressas

    # Converter listas para conjuntos
    description_set = set(description_list)
    url_set = set(url_list)

    # Encontrar a interseção dos dois conjuntos
    common = description_set & url_set

    # Iterar sobre as descrições e URLs
    # Primeiro, preencha o conjunto 'printed' com todas as descrições e URLs
    for description in description_list:
        description = description.lstrip()  # Remover espaços em branco apenas no início da descrição
        for url in url_list:
            # Se a descrição e a URL não têm hífen, também adicionar ao dicionário e imprimir
            if description in url and not ((description == 'admin' and (url == 'https://admin-produto.rentcars.com/' or url == 'https://integracao-sap-admin.rentcars.com/status')) or (description == 'facade' and (url == 'https://facade-commercial.rentcars.com/status' or url == 'https://facade-operacional.rentcars.com/status')) or (description == 'integrator' and url == 'https://integrator-front.rentcars.com/api/health') or (description == 'marketplace' and url == 'https://marketplace-promotions.rentcars.com/api/healthcheck')):
                description_url_dict[description] = url
                if (description, url) not in printed:
                    print(f"A descrição '{description}' está presente na URL: {url}")
                    printed.add((description, url))
            # Verificar as URLs estáticas
            elif (description == "api-docs-backend" and url == "https://api-docs-api.rentcars.com/api-docs/status") or (description == "api-docs-frontend" and url == "https://api-docs.rentcars.com/") or (description == "fortune-back" and url == "https://api-fortune.rentcars.com/ping") or (description == "fortune-front" and url == "http://fortune.rentcars.com/login/") or (description == "graylog" and url == "http://logs.mobicars.com.br/") or (description == "lapi" and url == "https://api-localidades.rentcars.com/status") or (description == "mobile" and url == "https://m.rentcars.com/pt-br/" ) or (description == "operacional front" and url == "http://operacional.rentcars.com/") or (description == "painel locadora" and url == "https://painel.rentcars.com/login") or (description == "proxmox" and url == "https://172.16.254.41:8006/") or (description == "site" and url == "https://www.rentcars.com/pt-br/") or (description == "wp-carro-assinatura" and url == "https://assinatura.rentcars.com/") or (description == "wp-customer-choice-awards" and url == "https://awards.rentcars.com/") or (description == "remi-repo" and url == "https://rpms.remirepo.net/"):
                description_url_dict[description] = url
                if (description, url) not in printed:
                    print(f"A descrição '{description}' está presente na URL: {url}")
                    printed.add((description, url))
    
    allCardsJSON = []
    problemCardsJSON = []

    if triggers_with_problems:
        for description, url in sorted(printed, key=lambda x: x[0]):
            problemCardsJSON.append({
                "description": description,
                "url": url,
            })

    descriptions = [linha['description'].lower().split('\"')[1].split('rentcars.com')[-1].split('rentcars')[-1] if '\"' in linha['description'] else linha['description'].lower().split('rentcars.com')[-1].split('rentcars')[-1] for linha in triggers_ok]
    
    # Verificar se httptests está vazio
    if not httptests:
        print("httptests está vazio")
    else:
        # Cria uma lista de URLs
        url_list = []
        for httptest in httptests:
            print("httptest: ", httptest)  # Debug: imprimir httptest
            for step in httptest['steps']:
                print("step: ", step)  # Debug: imprimir step
                if 'url' in step:
                    url_list.append(step['url'])
                else:
                    print("A chave 'url' não está presente em step: ", step)

    # Correlacionar descrições com URLs
    description_list = descriptions

    printed = set()  # Conjunto para armazenar descrições e URLs já impressas

    # Converter listas para conjuntos
    description_set = set(description_list)
    url_set = set(url_list)

    # Encontrar a interseção dos dois conjuntos
    common = description_set & url_set

    # Iterar sobre as descrições e URLs
    # Primeiro, preencha o conjunto 'printed' com todas as descrições e URLs
    for description in description_list:
        description = description.lstrip()  # Remover espaços em branco apenas no início da descrição
        for url in url_list:
            # Se a descrição e a URL não têm hífen, também adicionar ao dicionário e imprimir
            if description in url and not ((description == 'admin' and (url == 'https://admin-produto.rentcars.com/' or url == 'https://integracao-sap-admin.rentcars.com/status')) or (description == 'facade' and (url == 'https://facade-commercial.rentcars.com/status' or url == 'https://facade-operacional.rentcars.com/status')) or (description == 'integrator' and url == 'https://integrator-front.rentcars.com/api/health') or (description == 'marketplace' and url == 'https://marketplace-promotions.rentcars.com/api/healthcheck')):
                description_url_dict[description] = url
                if (description, url) not in printed:
                    print(f"A descrição '{description}' está presente na URL: {url}")
                    printed.add((description, url))
            # Verificar as URLs estáticas
            elif (description == "api-docs-backend" and url == "https://api-docs-api.rentcars.com/api-docs/status") or (description == "api-docs-frontend" and url == "https://api-docs.rentcars.com/") or (description == "fortune-back" and url == "https://api-fortune.rentcars.com/ping") or (description == "fortune-front" and url == "http://fortune.rentcars.com/login/") or (description == "graylog" and url == "http://logs.mobicars.com.br/") or (description == "lapi" and url == "https://api-localidades.rentcars.com/status") or (description == "mobile" and url == "https://m.rentcars.com/pt-br/" ) or (description == "operacional front" and url == "http://operacional.rentcars.com/") or (description == "painel locadora" and url == "https://painel.rentcars.com/login") or (description == "proxmox" and url == "https://172.16.254.41:8006/") or (description == "site" and url == "https://www.rentcars.com/pt-br/") or (description == "wp-carro-assinatura" and url == "https://assinatura.rentcars.com/") or (description == "wp-customer-choice-awards" and url == "https://awards.rentcars.com/") or (description == "remi-repo" and url == "https://rpms.remirepo.net/"):
                description_url_dict[description] = url
                if (description, url) not in printed:
                    print(f"A descrição '{description}' está presente na URL: {url}")
                    printed.add((description, url))
    
    okCardsJSON = []
    for description, url in sorted(printed, key=lambda x: x[0]):
        okCardsJSON.append({
            "description": description,
            "url": url,
        })

    allCardsJSON.append({
        "problemCards": problemCardsJSON,
        "okCards": okCardsJSON
    })

    return json.dumps(allCardsJSON)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090)