import time, json, os, requests, urllib
import bs4 as BeautifulSoup
from datetime import datetime, timedelta

NDAYS = 6
CONFIG_FILE = 'config.json'

def open_and_load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            return json.loads(config_file.read())
    else:
        print "File [%s] doesn't exist, aborting." % (CONFIG_FILE)
        sys.exit(1)

def get_cookie():
    r = requests.get('https://teleservices.paris.fr/srtm/initApplicationWeb.action')
    #print r.cookies['JSESSIONID']
    return r.cookies

def login(cookies, user, passwd):
    payload = { 'login': user, 'password': passwd }
    r = requests.post('https://teleservices.paris.fr/srtm/authentificationConnexion.action',
                      cookies=cookies, data = payload)
    return 'Rechercher un court' in r.text

def auth(user, passwd):
    cookies = get_cookie()
    r = login(cookies, user, passwd)
    return cookies

def search(cookies, jour):
    payload = { 'provenanceCriteres': 'true', 'libellePlageHoraire=': 'journee', 'nomCourt': '',
                'actionInterne': 'recherche', 'champ': '', 'recherchePreferee': 'on', 'tennisArrond': '',
                'arrondissement': '', 'arrondissement2': '', 'arrondissement3': '', 
                'dateDispo': jour, 'plageHoraireDispo': '8@21', 'revetement': '', 'court': '' }
    r = requests.post('https://teleservices.paris.fr/srtm/reservationCreneauListe.action',
                      cookies=cookies, data = payload)
    return r.text

def alert(config, txt, fulltxt):
    payload = { 'token': config['slack-token'],
                'channel': config['slack-channel'],
                'as_user': 'true',
                'text': txt,
                'attachments': '[{ "text": "%s"} ]' % fulltxt }
    r = requests.post('https://slack.com/api/chat.postMessage', data = payload)

def parse(html, config):
    soup = BeautifulSoup.BeautifulSoup(html)
    #print soup.prettify().encode('ascii', 'replace')
    tbl = soup.find_all('table', 'normal')
    if (len(tbl) > 0):
        trs = tbl[0].find_all('tr')
        if len(trs) > 0:
            fulltxt = ''
            for tr in trs:
                tds = tr.find_all('td')
                if (len(tds) > 0):
                    fulltxt = fulltxt + "%s: %s %s %s\n" % (tds[0].string, tds[2].string, tds[3].string, tds[4].string) 
            print fulltxt
            alert(config, 'found %d court' % len(trs), fulltxt)


def main():
    config = open_and_load_config()
    dt = datetime.now() + timedelta(days=NDAYS)
    d = dt.strftime("%d/%m/%Y")
    print d
    if (True):
        cookies = auth(config['tennis-login'], config['tennis-pass'])
        res = search(cookies, d)
    else:
        with open('res.html', 'r') as content_file:
            res = content_file.read()
    parse(res, config)

if __name__ == "__main__":
    main()
