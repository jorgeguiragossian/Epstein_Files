"""GitHub Pages settings via existing Git credentials. Tokens stay in memory."""
import argparse
import json
import os
import subprocess
from urllib.error import HTTPError
from urllib.request import Request,urlopen

REPOSITORY='jorgeguiragossian/Epstein_Files'


def main(action):
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,timeout=30,env=env)
    values=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    if not values.get('password'):raise SystemExit('Existing Git credentials could not authenticate the GitHub Pages API. No credentials were printed or saved.')
    token=values['password']
    def api(method,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=Request('https://api.github.com/repos/'+REPOSITORY+path,data=data,method=method,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'EpsteinFilesPagesDeployment','Content-Type':'application/json'})
        try:
            with urlopen(request,timeout=30) as response:return response.status,json.load(response) if response.status!=204 else {}
        except HTTPError as exc:
            return exc.code,json.loads(exc.read().decode())
    status,current=api('GET','/pages')
    if action=='enable':
        if status==404:status,current=api('POST','/pages',{'source':{'branch':'gh-pages','path':'/'},'build_type':'legacy'})
        elif status==200 and current.get('source',{}).get('branch')!='gh-pages':
            raise SystemExit('An existing Pages source differs from gh-pages; inspect it before changing configuration.')
    elif action=='build':status,current=api('POST','/pages/builds',{})
    elif action=='build-status':status,current=api('GET','/pages/builds/latest')
    print(json.dumps({'http_status':status,'result':current},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['status','enable','build','build-status'])
    main(parser.parse_args().action)
