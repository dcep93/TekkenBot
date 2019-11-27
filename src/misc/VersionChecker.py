#import requests
#from multiprocessing import queues #pyinstaller workaround  https://stackoverflow.com/questions/40768570/importerror-no-module-named-queue-while-running-my-app-freezed-with-cx-freeze
import json

CURRENT_VERSION = 'v0.15.0'


def check_version(force_print=False):
#    if 'dev' in CURRENT_VERSION:
    if 'v0.15.0' in CURRENT_VERSION:
        print("Tekken Bot version check disabled.")
#        print("DEVELOPER NOTE: Remember to update VersionChecker.CURRENT_VERSION before publishing a release.")
    else:
        try:
            r = requests.get('https://api.github.com/repos/roguelike2d/TekkenBot/releases/latest')

            #https://api.github.com
            #GET /repos/:owner/:repo/releases/latest
            if r.ok:
                repoItem = json.loads(r.text or r.content)
                repoTag = repoItem['tag_name']
                print("")
                if (repoTag != CURRENT_VERSION):
                    print("A new version of Tekken Bot is available.")
                #if (repoTag != CURRENT_VERSION or force_print):
                    print(repoItem['html_url'])
                    #print("Release Notes:")
                    #print(repoItem['body'])
                    print('')
                else:
                    print("Tekken Bot is up to date.")
        except:
            print("Tekken Bot version check failed.")

    print("")


if __name__ == '__main__':
    check_version()