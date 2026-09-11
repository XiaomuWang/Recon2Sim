import urllib.request,pathlib,concurrent.futures
out=pathlib.Path('environment_reconstruction_014346/validation/schema');out.mkdir(parents=True,exist_ok=True)
base='https://raw.githubusercontent.com/esmini/esmini/master/resources/schema/OpenDRIVE_1.7/localSchema/'
def one(p):
 urllib.request.urlretrieve(base+p,out/p);return p
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
 print(list(ex.map(one,['opendrive_17_'+n+'.xsd' for n in ['core','junction','lane','object','railroad','road','signal']])))
