import json
import urllib.request
import sys


if __name__ == "__main__":
    if len(sys.argv)<2:
        print(f"Usage: {sys.argv[0]} username [output.json]")
        exit(1)

    username = sys.argv[1]

    file = sys.stdout
    if len(sys.argv)>2:
        file = open(sys.argv[2], "w+")

    req = urllib.request.Request(f'https://api.github.com/users/{username}/repos')
    req.add_header('Accept', 'application/vnd.github.inertia-preview+json')
    with urllib.request.urlopen(req) as res:
        res = json.load(res)
        json.dump(res, file, indent=4)
