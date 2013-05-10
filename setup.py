from distutils.core import setup
from plstackapi.util.glob import recursive_glob

setup(name='plstackapi',
      version='0.1',
      description='PlanetStack API',
      packages=['plstackapi', 'plstackapi/planetstack', 'plstackapi/core','plstackapi/core/models' , 'plstackapi/core/views', 'plstackapi/core/api', 'plstackapi/core/fixtures', 'plstackapi/openstack' ,'plstackapi/util', 'plstackapi/importer', 'plstackapi/importer/plclassic'],
      scripts=['plstackapi/plstackapi-debug-server.py'],
      data_files=[
        ('/etc/planetstack/', ['config/plstackapi_config']),
        ('/opt/planetstack/', recursive_glob('plstackapi/planetstack/', '*')),
        ])
