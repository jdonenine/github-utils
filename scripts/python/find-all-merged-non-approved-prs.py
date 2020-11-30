from github import Github
import argparse
import sys

PR_FILTER = 'is:pr is:merged -review:approved'

def getArgs():
    parser = argparse.ArgumentParser(prog='find-all-merged-non-approved-prs')
    parser.add_argument('-t', '--token', required=True, type=str, help='The GitHub access token of the user to execute as.')
    parser.add_argument('-r', '--repo', required=True, type=str, help='The GitHub repo to operate against.')
    return parser.parse_args()

def connect(token):
    if (token == None):
        return None
    try:
        return Github(token)
    except:
        return None

def getUser(gh):
    if (gh == None):
        return None
    user = None
    try:
        user = gh.get_user()
        login = user.login
        if (login == None):
            return None
    except:
        return None
    return user

def getRepo(gh, repo_name):
    if (gh == None):
        return None
    if (repo_name == None):
        return None
    try:
        return gh.get_repo(repo_name)
    except:
        return None

def getReviews(pr):
    if (pr == None):
        return None
    try:
        return pr.get_reviews()
    except:
        return None

def getMergedNotApprovedPRs(repo):
    if (repo == None):
        return None
    
    prs = None
    try:
        prs = repo.get_pulls('closed')
    except:
        return None

    filtered_prs = []
    if (prs == None):
        return filtered_prs

    for pr in prs:
        if (pr.merged != True):
            continue
        reviews = getReviews(pr)
        if (reviews == None or reviews.totalCount == 0):
            filtered_prs.append(pr)
        else:
            approved = False
            for review in reviews:
                if (review == None or review.state == None or review.state != 'APPROVED'):
                    continue
                else:
                    approved = True
                    break
            if (approved == False):
                filtered_prs.append(pr)
    return filtered_prs

def getCommenters(pr):
    if (pr == None):
        return None
    comments = None
    try:
        comments = pr.get_issue_comments()
    except:
        return None
    commenters = set()
    for comment in comments:
        if (comment == None or comment.user == None or comment.user.login == None):
            continue
        commenters.add(comment.user.login)
    return commenters

args = getArgs()
token = args.token
repo_name = args.repo

print('Connecting to GitHub...')
gh = connect(token)
if (gh == None):
    sys.exit('ERROR: Unable to initialize connection to GitHub')

user = getUser(gh)
if (user == None):
    sys.exit('ERROR: Unable to connect to GitHub as a valid user')

print('Connected as user: %s' % user.login)

print('Accessing repository: %s...' % repo_name)
repo = getRepo(gh, repo_name)
if (repo == None):
    sys.exit('ERROR: Unable to access repository')
print('Accessed repository: %s' % repo.full_name)

print('Processing pull requests...')
prs = getMergedNotApprovedPRs(repo)
if (prs == None):
    sys.exit('ERROR: Unable to retrieve pull requests for the repository')

if (len(prs) == 0):
    print('Found no pull requests that were merged but not approved')
    sys.exit()

prs_unapproved_reviews = list()
prs_comments_no_reviews = list()

print('Identified %s pull requests that were merged but not approved:' % len(prs))
for pr in prs:
    print('\tPull request #%s by %s merged by %s: %s - %s' % (pr.number, pr.user.login, pr.merged_by.login, pr.title, pr.html_url))
    
    commenters = getCommenters(pr)
    if (commenters != None and pr.user.login in commenters):
        commenters.remove(pr.user.login)
    if (commenters != None and len(commenters) > 0):
        commenters_str = ','.join(commenters)
        print('\t\tIdentified %s commenters for pull request #%s: %s' % (len(commenters), pr.number, commenters_str))
    else:
        print('\t\tIdentified 0 commenters for pull request #%s' % pr.number)

    reviews = getReviews(pr)
    if (reviews != None and reviews.totalCount > 0):
        prs_unapproved_reviews.append(pr)
        print('\t\tIdentified %s reviews for pull request #%s:' % (reviews.totalCount, pr.number))
        for review in reviews:
            if (review == None):
                continue
            print('\t\t\tReview %s by user %s: %s' % (review.id, review.user.login, review.html_url))
    else:
        if (commenters != None and len(commenters) > 0):
            prs_comments_no_reviews.append(pr)
        print('\t\tIdentified 0 reviews for pull request #%s' % pr.number)

if (len(prs_unapproved_reviews) > 0):
    print('Identified %s pull requests that had reviews that were not approved:' % len(prs_unapproved_reviews))
    for pr in prs_unapproved_reviews:
        print('\tPull request #%s by %s merged by %s: %s - %s' % (pr.number, pr.user.login, pr.merged_by.login, pr.title, pr.html_url))
else:
    print('Identified 0 pull requests that had reviews that were not approved')

if (len(prs_comments_no_reviews) > 0):
    print('Identified %s pull requests that had comments, but no reviews:' % len(prs_comments_no_reviews))
    for pr in prs_comments_no_reviews:
        print('\tPull request #%s by %s merged by %s: %s - %s' % (pr.number, pr.user.login, pr.merged_by.login, pr.title, pr.html_url))
else:
    print('Identified 0 pull requests that had comments, but no reviews')