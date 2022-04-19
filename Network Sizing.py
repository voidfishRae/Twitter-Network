#Assignment 2

import twitter
import networkx as nx


#API/Consumer Key - J6RRpbg1SxOGFWRXD3GjX70Nk
#API Key/Consumer Secret - DnPjwYKwIW52dYwEkETEcAbT0R5a5kw3AC7OxMeHOYvGr0Ehah
#Bearer Token - AAAAAAAAAAAAAAAAAAAAAKk%2BZgEAAAAAx4APasVGDqrBuqt%2BO6Lhzxe2G5U%3DaHCNqqifADDvv5fCgW8A5gcxeZv9XHJpw6sEld7vuywWmLksaF
#OAuth/Access Token - 913183673171705856-B6AYdhk92ARtQdmPvV1ifVZ3NlD9gcB
#OAuth/Access Token Secret - IKgsdrR4jo2tAMQN0BxCQJrpOa5gxDKuc3ocjA1Pkyuaz

#Connect to twitter
def oauth_login():
    CONSUMER_KEY = "J6RRpbg1SxOGFWRXD3GjX70Nk"
    CONSUMER_SECRET = "DnPjwYKwIW52dYwEkETEcAbT0R5a5kw3AC7OxMeHOYvGr0Ehah"
    OAUTH_TOKEN = "913183673171705856-B6AYdhk92ARtQdmPvV1ifVZ3NlD9gcB"
    OAUTH_TOKEN_SECRET = "IKgsdrR4jo2tAMQN0BxCQJrpOa5gxDKuc3ocjA1Pkyuaz"

    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
    twitter_api = twitter.Twitter(auth=auth)

    return twitter_api

#Retrieve person

#####################
#From Cookbook Example 17
def get_user_profile(twitter_api, screen_names=None, user_ids=None):
   
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None),     "Must have screen_names or user_ids, but not both"
    
    items_to_info = {}

    items = screen_names or user_ids
    
    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.
        
        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup, 
                                            screen_name=items_str)
        else: # user_ids
            response = make_twitter_request(twitter_api.users.lookup, 
                                            user_id=items_str)
    
        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else: # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info
    #return response



import sys
import time
from urllib.error import URLError
from http.client import BadStatusLine
import json

def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 
    
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
    
        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes
    
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429: 
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'                  .format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
#######################

#Retrieve Friends
######################
#From Cookbook Example 19
from functools import partial
from sys import maxsize as maxint


def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None),     "Must have screen_name or user_id, but not both"
    
    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters
    
    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, 
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, 
                                count=5000)

    friends_ids, followers_ids = [], []
    
    for twitter_api_func, limit, ids, label in [
                    [get_friends_ids, friends_limit, friends_ids, "friends"], 
                    [get_followers_ids, followers_limit, followers_ids, "followers"]
                ]:
        
        if limit == 0: continue
        
        cursor = -1
        while cursor != 0:
        
            # Use make_twitter_request via the partially bound callable...
            if screen_name: 
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']
        
            print('Fetched {0} total {1} ids for {2}'.format(len(ids),                  label, (user_id or screen_name)),file=sys.stderr)
        
            # XXX: You may want to store data during each iteration to provide an 
            # an additional layer of protection from exceptional circumstances
        
            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]
##################################
    

#Determine Reciprocal Friends
def reciprocal_friends(friends_followers):
    friends = friends_followers[0]
    followers = friends_followers[1]
    
    #list comprehension to create a list of reciprocal friends
    reciprocal = [x for x in friends for y in followers if x == y]

    return reciprocal

#Select the 5 most popular reciprocal friends
def top_five(twitter_api, reciprocals):
    users = get_user_profile(twitter_api, user_ids = reciprocals)
    
    #most_popular = sorted(reciprocals, key = lambda user:(user["followers_count"]), reverse = True)

    most_popular = {id:users[id]['followers_count'] for id in users.keys()}

    sorted_most_popular = sorted(most_popular, key = most_popular.get, reverse = True)

    return sorted_most_popular[0:5]

#generic for collecting 5 followers
def get_five_followers(twitter_api, current_id):
    print(current_id)
    ff = get_friends_followers_ids(twitter_api, user_id = current_id, friends_limit = 1000, followers_limit = 1000)
    #all_reciprocals is a list of ids
    all_reciprocals = reciprocal_friends(ff)

    five_pop = top_five(twitter_api, all_reciprocals)
    
    return five_pop

def crawler(twitter_api, crawler_id, G):
    #top five
    top_five = get_five_followers(twitter_api, crawler_id)
    #add edges between the nodes - for loop
    for user in top_five:
        G.add_edge(crawler_id, user)

    #dfs
    next_queue = top_five
    depth = 1
    max_depth = 4
    done = False #become true when have 100 nodes

    while depth < max_depth and not done:
        #increase depth every time
        print("depth:", depth)
        depth += 1
        (queue, next_queue) = (next_queue, [])
        print("queue:",queue)
        for id in queue:
            new_top_five = get_five_followers(twitter_api, id)

            #add each item from new_top_five into next_queue
            for i in new_top_five:
                if(i not in next_queue and i not in G.nodes()):
                    next_queue.append(i)

             #insert nodes into the graph - for loop
            for user in new_top_five:
                G.add_node(user)
                    
            #add edges to graph - for loop
            for user in new_top_five:
                G.add_edge(id, user)

            if G.number_of_nodes() == 100:
                done = True
                break
        print("---")
        



def main():
    twitter_api = oauth_login()
    outfile = open("twitternetwork.txt", "w")

    #user = make_twitter_request(twitter_api.users.lookup, screen_name = "CelesteAltalune")

    G = nx.Graph()
    crawler(twitter_api, "1393115905039618049", G)


    outfile.write("Graph size (nodes):"+ str(G.number_of_nodes()) +"(edges):"+str(G.number_of_edges()))
     #Find avg distance and diameter of network
    outfile.write("Diameter:"+ str(nx.diameter(G)))
    outfile.write("Avg distance:"+ str(nx.average_shortest_path_length(G)))

    outfile.close()



main()
