import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import config
import websockets
import asyncio
import json
opts = Options()
opts.add_argument(config.USERAGENT)


def pageFinder(soupResult):
    return soupResult.findAll("div", class_="card card-hover card-visited wordwrap job-link")

print(f"Server listen on {config.SOCKET_PORT}")
connected = set()

async def echo(websocket,path):
    print("A client connected")
    connected.add(websocket)
    try:
        async  for message in websocket:
            print("Received message from client"+message)
            print(json.loads(message)['type'])
            if json.loads(message)['type'] == 'pingstart':
                while True:
                    if "search_input" in json.loads(message): currentUrl="https://www.work.ua/ru/jobs-{}/".format(json.loads(message)["search_input"])
                    else: currentUrl = "https://www.work.ua/ru/jobs-front-end+%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA/"
                    r = requests.get(currentUrl, headers=config.HEADER_CONFIG)
                    soup = BeautifulSoup(r.text, "lxml")
                    page_count = int(soup.find("ul", class_="pagination hidden-xs").find_all("a")[-2].text.strip())
                    print(page_count)
                    for pages in range(1, page_count + 1):
                        page_request = requests.get("{}?page={}".format(currentUrl, pages), headers=config.HEADER_CONFIG)
                        soupPage = BeautifulSoup(page_request.text, "lxml")
                        #            print(pageFinder(soupPage))
                        for cards in pageFinder(soupPage):
                            imgRender = cards.find("img")
                            attentionArr = []
                            if imgRender != None: imgResult = imgRender['src']
                            else: imgResult = "None"
                            for attention in cards.findAll("b"): attentionArr.append(attention.text)
                            await websocket.send(json.dumps([json.dumps({'page_count': page_count, 'data': {
                                "title": cards.find("h2").find("a").text,
                                "link": cards.find("h2").find("a")['href'],
                                "description": cards.find("p", class_="overflow text-muted add-top-sm cut-bottom").text.strip(),
                                "time": cards.find("span", class_="text-muted small").text,
                                "attentionTags": attentionArr,
                                "img": imgResult
                            }})]))
                    print("Reloading...")
                    await asyncio.sleep(2)
    except websocket.exceptions.ConnectionClosed as e:
        print("Client disconnected")
        print(e)
    finally:
        connected.remove(websocket)

start = websockets.serve(echo, config.SOCKET_URL, config.SOCKET_PORT)

asyncio.get_event_loop().run_until_complete(start)
asyncio.get_event_loop().run_forever()