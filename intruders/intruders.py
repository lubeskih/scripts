import subprocess, itertools, time, sqlite3
import requests
from bs4 import BeautifulSoup as bs

country_codes = {'MK': 0, 'RS': 0, 'BG': 0, 'GR': 0, 'AL': 0,
            'US': 0, 'CA': 0, 'DE': 0, 'FR': 0, 'ES': 0,
            'SE': 0, 'RU': 0, 'IN': 0, 'CN': 0, 'JP': 0,
            'MY': 0, 'GB': 0, 'OTHER_COUNTRY_CODES': 0, 'UNREGISTERED_DOMAINS': 0, 
            'TOTAL_FOREIGN_DOMAINS': 0}

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 
        'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 
        't', 'u', 'v', 'w', 'x', 'y', 'z']

database_saves = 0

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return None

def create_tables(conn):
    cur = conn.cursor()

    try:
        cur.execute('''CREATE TABLE full_log (domain_name text, address text, register_date text, expire_date text)''')

        cur.execute('''CREATE TABLE clean_log (address text, totalRegistered int)''')

        cur.execute('''CREATE TABLE unregistered_domains_log (unregistered text)''')

        cur.execute('''CREATE TABLE alive (domain_name text, status text, title text, alive text)''')
        
    except Exception as e:
        print(e)

    return None

def fetch_domain_names(conn):
    cur = conn.cursor()
    cur.execute('SELECT domain_name FROM full_log WHERE address="CN"')

    list_of_domains = []

    for domain in cur.fetchall():
        list_of_domains.append(domain)

    return list_of_domains

def ping_domains(domains, conn):
    cur = conn.cursor()
    
    for domain in domains:
        domain = domain[0]
        fulldomain_name = "http://" + domain
    
        print(f"Sending a GET request to {domain}...")

        try:
            request = requests.get(fulldomain_name, timeout=3, allow_redirects=False)
            status = request.status_code
            title = str(bs(request.content, features="html.parser").title.string)
            
            query = f"INSERT INTO alive VALUES ('{domain}', '{status}', '{title}', 'YES')"
            cur.execute(query)
        except Exception as e:
            query = f"INSERT INTO alive VALUES ('{domain}', '/', '/', 'NO')"
            cur.execute(query)

            print(f"Domain {domain} is not responding: {e} ")

    return None

def fetch_domain_data(domain):
    command = f"whois {domain} | grep 'domain:\|registered:\|expire:\|address:'"

    try :
        return str((subprocess.check_output(command, shell=True)), 'UTF-8')
    except Exception as e:
        return None


def beautify_output(output):
    output = output.splitlines()

    for line in output:
        if line.startswith("domain:"):
            domain_name = line.partition(':')[2].strip()

        if line.startswith("address:"):
            country_code = line.partition(':')[2].strip()
            
            if country_code in country_codes:
                country_codes[country_code] += 1
                break
            elif len(country_code) == 2 and country_code.isupper():
                country_codes["OTHER_COUNTRY_CODES"] += 1
                break
            else:
                pass

        if line.startswith("registered:"):
            register_date = line.partition(':')[2].strip()

        if line.startswith("expire:"):
            expire_date = line.partition(':')[2].strip()

    return domain_name, country_code, register_date, expire_date

def write_full_data_to_db(domain_name, country_code, register_date, expire_date, conn):
    cur = conn.cursor()
    query = f"INSERT INTO full_log VALUES ('{domain_name}', '{country_code}', '{register_date}', '{expire_date}')"
    global database_saves

    try:
        cur.execute(query)
    except Exception as e:
        print(e)
        return None
    
    database_saves += 1
    print(f"{database_saves} {domain_name} was successfully written in the database")
    return True

def write_clean_data_to_db(conn):
    cur = conn.cursor()
    
    total_foreign_domains = 0
    skip_address = ["MK", "UNREGISTERED_DOMAINS"]

    for address in country_codes:
        if address in skip_address:
            pass
        else:
            total_foreign_domains += country_codes[address]

    country_codes['TOTAL_FOREIGN_DOMAINS'] = total_foreign_domains

    for address in country_codes:
        try:
            query = f"INSERT INTO clean_log VALUES ('{address}', '{country_codes[address]}')"
            cur.execute(query)
            print("The clean log was successfully written in the database")
        except Exception as e:
            print(e)

    return None

def log_unregistered_domain(domain, conn):
    cur = conn.cursor()
    global database_saves

    country_codes["UNREGISTERED_DOMAINS"] += 1

    query = f"INSERT INTO unregistered_domains_log VALUES ('{domain}')"
    cur.execute(query)
    
    database_saves += 1
    print(f"{database_saves} {domain} is UNREGISTERED.")

    return None

def combine_fetch_write(conn):
    cur = conn.cursor()

    for (x, y) in itertools.product(letters, repeat = 2):
        domain = x + y + ".mk"
        output = fetch_domain_data(domain) # get data for the domain

        if output:
            domain_name, country_code, register_date, expire_date = beautify_output(output)
            write_full_data_to_db(domain_name, country_code, register_date, expire_date, conn)
        else:
            log_unregistered_domain(domain, conn)

    write_clean_data_to_db(conn)

    return None

def main():
    database = "mk_domains.db"
    conn = create_connection(database)
    
    with conn:
        create_tables(conn)

        combine_fetch_write(conn)

        domain_names = fetch_domain_names(conn)
        ping_domains(domain_names, conn)

    print("All good. Go on.")

    return None

main()