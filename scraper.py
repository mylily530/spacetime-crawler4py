import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import http.client
import os

urls_visited = []
blacklisted = []
dead_urls = []
file_of_all_links_found = "all_found_links.txt"
longest_page = ["empty", 0]


def scraper(url, resp):
    #If we have a 3XX code we want to redirect to the actual page
    redirect_status_codes = [301, 302, 307, 308]
    if resp.status in redirect_status_codes:
        url, resp = redirected_page(url)

    links = extract_next_links(url, resp)

    #take a link and check if it's inside of the set
    
    new_links = only_new_links(links, file_of_all_links_found)
    
    return [link for link in new_links if is_valid(link)]


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    



    ###Code that was added to get all the URLs from a site, test parsing the site's text, and printing everything.
    ###Most is just a test and can be removed later, the important part here is knowing how to tokenize the page and the URLs for this function
    ####Last 4 functions in this file are helper, tokenize and url grab
    if resp.status != 200:
        return list()
    
    urlList = getURLs(resp.raw_response.content)
    TokenList = tokenize(resp.raw_response.content)

    #report Question #2 Doesn't work 
    tokenListLen = len(TokenList)
    if tokenListLen >= longest_page[1]:
        longest_page[1] == tokenListLen
        longest_page[0] == resp.raw_response.url
    
    TokenCount = computeWordFrequencies(TokenList)
    storeWordFrequencies(TokenCount) #report Question #3


    printFrequencies(TokenCount)
    print("These are the URLs found:")
    for url in urlList:
        print(url)

    return urlList



def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    #print("WE are in is_valid_url_NOW!")

    try:

        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
            

    
        #check to make sure that netloc is correct and that we can continue to check the path below (aka we don't want to return True too soon)
        # domains = {"ics", "cs", "informatics", "stat"}
        domains = {"ics"}
        SplitNetlock = parsed.netloc.split(".")
        if len(SplitNetlock) <= 2:
            return False
        if not (SplitNetlock[-1] == "edu" and SplitNetlock[-2] == "uci" and SplitNetlock[-3] in domains):
            return False

        url_type = not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        if url_type == False:
            return False
        



        #check if URL blacklisted  
        if check_for_trap(url, urls_visited):
            blacklisted.append(url)
            return False
    
        #right now im just getting the actual page and downlaoding all the pages which
        #i dont want to do but i can't seem to find the heading that relate to length that ive heard about
        #this is why GET is being used instead of HEAD
        if parsed.scheme == 'https':
            connect = http.client.HTTPSConnection(parsed.netloc)
        else:
            connect = http.client.HTTPConnection(parsed.netloc)
        
        expected_length = None

        try:
            #Get the page content
            connect.request("GET", parsed.path)
            response = connect.getresponse()
            content = response.read()
            
            #get the page text and remove uneccesary whitespace
            soup = BeautifulSoup(content, 'html.parser')
            pageText = soup.get_text()
            cleanedText = re.sub(r'\s+', ' ', pageText).strip()

            #get expected length
            expected_length = len(cleanedText)
            print(f"{expected_length}: got content length ")
            
            if expected_length != None:
                if check_not_dead_url(url, response, expected_length) == False:
                    return False
        
                if file_too_large(expected_length):
                    return False

                if exact_duplicates(expected_length):
                    return False
            
        except Exception as e:
                print(f"Error {url}: {e}")

        finally:
                connect.close()

        #this is a file that will tell us the length of the longest file and is usefull for checking exact duplicates
        if expected_length != None:
            with open("valid_url.txt", "a", encoding="utf-8") as file:
                if expected_length != None:
                    file.write(f"{url} {expected_length}\n")
                else:
                    file.write(f"{url}\n")
        return True
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def only_new_links(input_links, file_of_all_links_found) -> list:
    return_links = []
    if os.path.exists(file_of_all_links_found):
        with open(file_of_all_links_found, "r") as file:
            all_links = file.readlines()
        
        all_links = [link.strip() for link in all_links]
    else:
        all_links = []
        
    #find new links only
    for link in input_links:
        if link not in all_links: 
            return_links.append(link)

    # Append new links to the file at the end
    with open(file_of_all_links_found, "a+") as file:
        for new_link in return_links:
            file.write(new_link + "\n")  # Add a newline after each link

    return return_links


def redirected_page(url):
    """
    fetch the redirct link and make that the normal link
    """
    parsed_url = urlparse(url)

    if parsed_url.scheme == 'https':
        connect = http.client.HTTPSConnection(parsed_url.netloc)
    else:
        connect = http.client.HTTPConnection(parsed_url.netloc)
    
    connect.request("GET", parsed_url.path)
    response = connect.getresponse()
    location_header=response.getheader('Location')
    
    if location_header:
            redirected_url = urljoin(url, location_header) #absolute url
            new_parsed_url = urlparse(redirected_url) #redirect to get resp
            if new_parsed_url.scheme == 'https':
                new_connect = http.client.HTTPSConnection(new_parsed_url.netloc)
            else:
                new_connect = http.client.HTTPConnection(new_parsed_url.netloc)

            new_connect.request("GET", new_parsed_url.path)
            new_response = new_connect.getresponse()

    return redirected_url, new_response




def tokenize(TextFilePath) -> list:
    """
    Project 1 function that takes a html page and cleans it up
    -returns a List of tokens
    """
    TokenList = []
    pattern = re.compile("^[a-z0-9]+$")
    page = TextFilePath.decode('utf-8')
    clean = BeautifulSoup(page, "lxml")
    text = clean.get_text()
    for line in text.split("\n"):
        lowerline = line.lower()
        tempWord = ''
        for character in lowerline:
            if pattern.match(character):
                tempWord = tempWord + character
            else:
                if tempWord != '':
                    TokenList.append(tempWord)
                tempWord = ''
        if tempWord != '':
            TokenList.append(tempWord)
    return TokenList




def computeWordFrequencies(TokenList: list) -> map:
    """
    Counts the word count from a recieved list 
    -returns a map of words and their counts
    """
    tokenCount = {}
    for word in TokenList: 
        if word in tokenCount:
            tokenCount[word] = tokenCount[word] + 1
        else: 
            tokenCount[word] = 1
    return tokenCount

def storeWordFrequencies(tokenMap: map) -> None:
    """
    sotre words frequencies in a file by getting the words and adding new words on then appending back to file
    """
    #fetch old data
    filename = "WordFrequency.txt"
    old_data = {}
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                word, count = line.strip().split()
                old_data[word] = int(count)

    #update count with new items
    for word, count in tokenMap.items(): #t o get word and count
        if word in old_data:
            old_data[word] += count
        else:
            old_data[word] = count
    
    #update count and sort it in the file
    sorting = sorted(sorted(tokenMap.keys(), key = lambda word:word.lower()), key = lambda count: tokenMap[count], reverse = True)

    with open(filename, "w", encoding="utf-8") as file:
        for word in sorting:
            file.write(f"{word} {old_data[word]}\n")


def printFrequencies(tokenCount: map):
    """
    Prints out a sorted list of words and their counts starting from Largest count
    """
    sorting = sorted(sorted(tokenCount.keys(), key = lambda word:word.lower()), key = lambda count: tokenCount[count], reverse = True)
    for i in sorting:
        print(i + " => " + str(tokenCount[i]))
    return


def getURLs(siteBytes: bytes) -> list:
    """
    decodes a html file and removes the fragment
    -returns a list of urls without fragment found on the page
    """
    content_str = siteBytes.decode('utf-8', errors='ignore')
    htmlParsed = BeautifulSoup(content_str, "lxml")
    urls = [a['href'] for a in htmlParsed.find_all('a', href=True)]
    cleanURLs = []
    for url in urls:
        toAdd = url.split('#')[0]
        if toAdd != '':
            cleanURLs.append(toAdd)
    return cleanURLs

#TODO:
def check_for_trap(url, visited_urls_list) -> list:
    """
    #Crawler behavior Requirements: Detect and avoid infinite traps
    Check Url against the list of urls (from recent time (say last 100 urls)
    if a certain threshold is achieved (say 5) then we want to blacklist url and get out of the trap

    """

    #Check for repeated URLs in history 
    if visited_urls_list.count(url) > 5:
        print(f"Blacklisted URL: {url}")
        return True
    
    visited_urls_list.append(url)

    #Keeping the most recent URLs
    if len(visited_urls_list) > 100:
        visited_urls_list.pop(0)

    #URL is valid and not blacklisted
    return False 

def exact_duplicates(expected_length):
    """
    #Crawler behavior Requirements: Detect and avoid sets of similar pages with no information
    find out how many bytes the file is.
    Check it against the files that have already been accepted 
    #if its duplicate return True
    """
    print("EXACT DUPES")
    with open("valid_url.txt", "r", encoding="utf-8") as file:
        all_lines = file.readlines()

    all_lines = [line.strip().split(" ")[-1] for line in all_lines] #takes the last value aka the lengths of all the 
    if str(expected_length) in all_lines:
        return True
    else:
        
        return False
    

def file_too_large(expected_length) -> bool:
    """
    Requirement: Detect and avoid crawling very large files, especially if they have low information value
    """
    print("LARGE FILE")
    if expected_length >= 2000000:
        print("~20MB")
        return True

    return False
    

    
def check_not_dead_url(url, response, expected_length) ->bool:
    """
    #Crawler behavior Requirements: Detect and avoid dead URLs that return a 200 status but no data
    Check url and make sure that even if the url is accessible 
    (Http request returns 200) that we can actually access it
    
    -Check that it's not empty or that there isn't like a 404 error text
    -return boolean False (dead), True (We want to read it)
    """
    
    try:
        print("DEAD URL")
        #Empty page
        if expected_length == 0:
            #print("Empty Page")
            dead_urls.append(url)
            return True
        
        #page with less than 100 words (number can be changed)
        if expected_length <= 100: 
            dead_urls.append(url)
            return True
            
        return True
    except http.client.HTTPException as e:
        print(f"HTTPException for {url}: {e}")

    if expected_length <= 100:
        print(f"this is the length {expected_length} maybe manually check for now! {url} ")
        return True
        
    return False
        
#Crawler behavior Requirements: Detect redirects and if the page redirects your crawler, index the redirected content
#Crawler behabior Requirements: Detect and avoid crawling very large files, especially if they have low information value (Anyone have any good ideas on how to do this?)