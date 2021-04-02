import discord, json, threading, time
from discord.ext import commands
from discord.utils import find
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains 
#from selenium.webdriver.common.keys import Keys
intents = discord.Intents.default()
intents.members = True

driver = webdriver.Firefox()

client = commands.Bot(command_prefix = "^")

def findTweet(driver, elements, lastPost):
  driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
  for elem in elements:
    paren = elem.get_attribute("style").text.index("(")
    px = elem.get_attribute("style").text.index("px")
    if int(elem.get_attribute("style").text[paren, px-1]) > lastPost:
      return elem
    if elem == elements[len(elements)]:
      return findTweet(driver, driver.find_elements_by_xpath("//div[contains(@style, 'translateY')]"), lastPost)

def clearCounts():
  with open("counts.json", "r") as f:
    counts = json.load(f)

  for guild in client.guilds:
    for site in counts[str(guild.id)]:
      counts[str(guild.id)] = []

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

timer = threading.Timer(86400, clearCounts)

@client.event
async def on_guild_join(guild):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  with open("counts.json", "r") as f:
    counts = json.load(f)
  
  prefixes[str(guild.id)] = "^"
  counts[str(guild.id)] = {"reddit":[], "twitter":{}, "facebook":[], "instagram":[], "tumblr":[], "twitch":[], "4chan":[], "ifunny":[]}

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=2)

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  general = find(lambda x: x.name == "general",  guild.text_channels)
  if general and general.permissions_for(guild.me).send_messages:
    embed=discord.Embed(title="**Hello!**", description="Thank you for inviting me to your server! I'm still in my developmental stages so if you find any bugs, have any suggestions, or would like some help, please join my support server. Any input would be greatly appreciated! https://discord.gg/cBNQpV6rwh", color=discord.Colour.orange())
    await general.send(embed=embed)

@client.event
async def on_guild_remove(guild):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  with open("counts.json", "r") as f:
    counts = json.load(f)
  
  prefixes.pop(str(guild.id))
  counts.pop(str(guild.id))

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=2)

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

@client.event
async def on_ready():
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  with open("counts.json", "r") as f:
    counts = json.load(f)

  for guild in client.guilds:
    if str(guild.id) not in prefixes.keys():
      prefixes[str(guild.id)] = "^"
    if str(guild.id) not in counts.keys():
      counts[str(guild.id)] = {"reddit":[], "twitter":{}, "facebook":[], "instagram":[], "tumblr":[], "twitch":[], "4chan":[]}

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=2)

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  print("Bot is ready")
      
@client.command()
async def ping(context):
  await context.send(f"bot latency = {round(client.latency * 1000)}ms")

@client.command()
async def changeprefix(context, prefix):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  prefixes[str(context.guild.id)] = prefix

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=2)

  await context.send("Prefix is now " + prefix)

@client.command()
async def reddit(context, sub = "", category = "", subcategory = ""):
  url = "https://www.reddit.com/"
  if sub != "":
    url = url + "r/" + sub + "/"
    if category != "":
      url = url + category + "/"
    if category == "top":
      url = url + "?t=" + subcategory + "/"
  
  if driver.current_url != url:
    print(driver.current_url)
    async with context.channel.typing():
      driver.get(url)

  if driver.find_element_by_tag_name("h3").text == "You must be 18+ to view this community":
    if context.channel.is_nsfw() == True:
      try:
        driver.find_element_by_xpath("//button[contains(@role, 'button')]").click()
      except:
        pass
    else:
      await context.send("NSFW posts can only be sent in an NSFW channel.")
      return None

  post = ""
  
  with open("counts.json", "r") as f:
    counts = json.load(f)

  for elem in driver.find_elements_by_xpath("//div[contains(@id, 't3_')]"):
    post = elem.get_attribute("id")
    if post.startswith("t3_") and len(post) == 9 and post not in counts[str(context.guild.id)]["reddit"]:
      try:
        elem.find_element_by_class_name("rewiG9XNj_xqkQDcyR88j")
        print("hi")
        counts[str(context.guild.id)]["reddit"].append(post)
      except:
        break

  print("id: " + post)

  try:
    content = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, post)))
    driver.execute_script("arguments[0].scrollIntoView();", content)
  except:
    await context.send(url + " took too long to respond")
    driver.quit()

  body = ""
  image = None

  title = content.find_element_by_tag_name("h3").text
  print(title)

  for p in content.find_elements_by_tag_name("p"):
    t = p.text
    body = body + t
    body = body + "\n"
  try:
    link = content.find_element_by_xpath(".//a[@post='[object Object]']")
    url = link.get_attribute("href")
    print(link)
    print(url)
    body = body + "["+ link.text +"](" + url + ")"
  except:
    pass
  try:
    image = content.find_element_by_xpath(".//img[@alt='Post image']").get_attribute("src")
  except:
    try:
      image = content.find_element_by_xpath(".//video[@preload='auto']").get_attribute("poster")
    except:
      try: 
        image = content.find_element_by_xpath(".//*[contains(@class, 'media-element')]").find_element_by_css_selector("source").get_attribute("src")
      except:
        try:
          link = content.find_element_by_class_name("ytp-cued-thumbnail-overlay-image").get_attribute("style")
          image = link[link.index("(")+2:link.index(")", 2)-1]   
        except:
          try:
            link = content.find_element_by_xpath(".//div[@role='img']").get_attribute("style")
            image = link[link.index("(")+2:link.index(")", 2)-1]
          except:
            pass

  if len(title) > 256:
    title = title[:253] + "..."
    if title[253] == " ":
      del title[253]
  if len(body) > 2048:
    body = body[:2045] + "..."
    if body[2045] == " ":
      del body[2045]

  embed=discord.Embed(title=title, description=body, url="https://reddit.com/"+post[3:], color=discord.Colour.red())
  
  if image:
    embed.set_image(url=image)
  
  counts[str(context.guild.id)]["reddit"].append(post)
  
  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  await context.send(embed=embed)

@client.command()
async def twitter(context, account=""):
  url = "https://twitter.com/" + account
  if account == "":
    await context.send("Missing Account")
  
  print(url)

  if driver.current_url != url:
    print(driver.current_url)
    async with context.channel.typing():
      driver.get(url)

  with open("counts.json", "r") as f:
    counts = json.load(f)
  
  try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "css-4rbku5 css-1dbjc4n r-1awozwy r-1pz39u2 r-1loqt21 r-6koalj r-16y2uox r-1777fci r-4wgw6l")))
  except:
    await context.send(url + " took too long to respond")
    driver.quit()

  if account in counts[str(context.guild.id)]["twitter"].keys():
    content = findTweet(driver, driver.find_elements_by_xpath("//div[contains(@style, 'translateY')]"), counts[str(context.guild.id)]["twitter"][account])
  else:
    counts[str(context.guild.id)][account] = -1
    findTweet(driver, driver.find_elements_by_xpath("//div[contains(@style, 'translateY')]"), -1)
  counts[str(context.guild.id)]["twitter"][account] = int(content.text[content.text.index("("): content.text.index("px")-1])

  try:
    content = WebDriverWait(driver, 30).until(EC.presence_of_element_located(content))
    driver.execute_script("arguments[0].scrollIntoView();", content)
  except:
    await context.send(url + " took too long to respond")
    driver.quit()

  try:
    titleContent = WebDriverWait(driver, 30).until(EC.presence_of_element_located(content.find_element_by_class_name("css-901oao css-bfa6kz r-18jsvk2 r-1qd0xha r-a023e6 r-b88u0q r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0")))
    driver.execute_script("arguments[0].scrollIntoView();", titleContent)
  except:
    await context.send(url + " took too long to respond")
    driver.quit()

  title = titleContent.find_element_by_class_name("css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0").text

  try:
    descriptionContent = WebDriverWait(driver, 30).until(EC.presence_of_element_located(content.find_element_by_class_name("css-901oao r-18jsvk2 r-1qd0xha r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-bnwqim r-qvutc0")))
    driver.execute_script("arguments[0].scrollIntoView();", descriptionContent)
  except:
    await context.send(url + " took too long to respond")
    driver.quit()

  description = ""
  for elem in descriptionContent.find_elements_by_class_name("css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"):
    description = description + elem.text

  embed=discord.Embed(title=title, description=description, url="https://twitter.com/"+account, color=discord.Colour.blue())

  try:
    img = content.find_element_by_class_name("css-9pa8cd").get_attribute("src")
    embed.set_image(url=img[img.index("https"):])
  except:
    pass

  await context.send(embed=embed)

@client.command()
async def ifunny(context, *category):
  category = "-".join(category)
  print(category)
  if category:
    url = "https://ifunny.co/" + category
  else:
    url = "https://ifunny.co/"

  if driver.current_url != url:
    print(driver.current_url)
    async with context.channel.typing():
      driver.get(url)

  try:
    driver.find_element_by_class_name("media__image")
  except:
    element = driver.find_element_by_xpath("//div[@class='mode__button js-mode-toggler ']")
    driver.execute_script("arguments[0].click();", element)
    print("test")

  extranneous = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "media__image")))

  with open("counts.json", "r") as f:
    counts = json.load(f)

  content = None
  for elem in driver.find_elements_by_class_name("post"):
    if elem.get_attribute("data-id") not in counts[str(context.guild.id)]["ifunny"]:
      content = elem
      driver.execute_script("arguments[0].scrollIntoView();", content)
      counts[str(context.guild.id)]["ifunny"].append(elem.get_attribute("data-id"))
      break

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  embed=discord.Embed(title=None, description=None, url="https://ifunny.co/picture/"+content.get_attribute("data-id")+"?gallery=featured", color=discord.Colour.blue())

  img = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "media__image")))
 
  embed.set_image(url=img.get_attribute("src"))

  await context.send(embed=embed)

@client.command()
async def instagram(context, *user):
  user = "-".join(user)
  if user:
    url = "https://www.instagram.com/" + user
  else:
    url = "https://www.instagram.com/"

  if driver.current_url != url:
    print(driver.current_url)
    async with context.channel.typing():
      driver.get("https://www.instagram.com")
      try:
        content = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "loginForm")))
        driver.find_element_by_name("username").send_keys("discordsocialmediabot")
        driver.find_element_by_name("password").send_keys("""password""")
        for button in content.find_elements_by_tag_name("button"):
          if button.text != "Show" and button.text != "Log in with Facebook":
            button.click()
        button = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "JErX0")))
        button.find_element_by_tag_name("button").click()
        content = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "mt3GC")))
        for button in content.find_elements_by_tag_name("button"):
          if button.text == "Not Now":
            button.click()
      except:
        pass
      driver.get(url)

  WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ySN3v")))

  with open("counts.json", "r") as f:
    counts = json.load(f)
  
  link = None
  for elem in driver.find_elements_by_xpath("//a[contains(@href, '/p/')]"):
    link = elem.get_attribute("href")
    if link not in counts[str(context.guild.id)]["instagram"]:
      driver.get(link)
      counts[str(context.guild.id)]["instagram"].append(link)
      break

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  img = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "FFVAD"))).get_attribute("src")

  description = ""
  for text in driver.find_element_by_class_name("C4VMK").find_elements_by_xpath(".//*"):
    if (text.tag_name == "span" or text.tag_name == "a") and text.text != user and text.get_attribute("class") != " xil3i" and text.tag_name != "br":
      print(text.get_attribute("class") + " " + text.tag_name)
      print("hi")
      description = description + text.text

  embed=discord.Embed(title="**"+user+"**", description=description, url=link, color=discord.Colour.blue())

  embed.set_image(url=img)
 
  await context.send(embed=embed)

@client.command()
async def tumblr(context, *blog):
  blog = "-".join(blog)
  if blog:
    url = "https://www.tumblr.com/blog/view/" + blog
  else:
    url = "https://www.tumblr.com/explore/trending"

  if driver.current_url != url:
    print(driver.current_url)
    async with context.channel.typing():
      driver.get("https://www.tumblr.com")
      try:
        pass
      except:
        pass
      driver.get(url)

  content = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "_29w6l")))
  content.find_element_by_class_name("_1gW7L").send_keys("""email""")
  content.find_element_by_class_name("Hi_aW").click()
  content = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, "_29w6l")))
  driver.find_element_by_name("password").send_keys("""password""")
  content.find_element_by_class_name("Hi_aW").click()

  content = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "cfpPU")))

  with open("counts.json", "r") as f:
    counts = json.load(f)
  
  driver.execute_script("arguments[0].scrollIntoView();", content)
  content = None
  for elem in driver.find_elements_by_class_name("_1DxdS"):
    if elem.get_attribute("data-id") not in counts[str(context.guild.id)]["tumblr"]:
      counts[str(context.guild.id)]["tumblr"].append(elem.get_attribute("data-id"))
      content = elem
      driver.execute_script("arguments[0].scrollIntoView();", content)
      break

  with open("counts.json", "w") as f:
    json.dump(counts, f, indent=2)

  description = ""
  for elem in content.find_elements_by_class_name("_2m1qj"):
    description = description + elem.text

  embed=discord.Embed(title="**"+blog+"**", description=description, url="https://www.tumblr.com/blog/view/" + blog, color=discord.Colour.blue())

  try:
    srcset = content.find_element_by_xpath(".//img[@role, img]").get_attribute("srcset")
    embed.set_image(url=srcset[srcset.rindex(","):srcset.rindex("g")])
  except:
    try:
      embed.set_image(url=content.find_element_by_tag_name("source").get_attribute("src"))
    except:
      pass

  await context.send(embed=embed)

client.run("""token""")
