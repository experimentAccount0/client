""" run with

python setup.py install; nosetests -v --nocapture  tests/cm_cloud/test_OS_API.py:Test_osapi.test_001
python setup.py install; py.test tests/cm_cloud/test_OS_API.py:Test_osapi.test_001
nosetests -v --nocapture tests/test_list.py

or

nosetests -v tests/test_list.py

"""

from pprint import pprint

from cloudmesh_client import ConfigDict
from cloudmesh_client.cloud.iaas.provider.openstack.CloudProviderOpenstackAPI import CloudProviderOpenstackAPI
from cloudmesh_client.common.Shell import Shell
from cloudmesh_client.common.dotdict import dotdict
from cloudmesh_client.common.util import HEADING
from cloudmesh_client.common.util import banner
from cloudmesh_client.default import Default


# noinspection PyPep8Naming
class Test_osapi:
    data = dotdict({
        "cloud": Default.cloud,
        "format": "json",
        "user": "fake",
        "wrong_cloud": "no_cloud",
        "key": "my_default_key",
        "value": "my_default_value"
    })

    def run(self, command):
        command = command.format(**self.data)
        banner(command, c="-")
        print(command)
        parameter = command.split(" ")
        shell_command = parameter[0]
        args = parameter[1:]
        result = Shell.execute(shell_command, args)
        print(result)
        return str(result)

    def setup(self):
        pass

    # noinspection PyPep8Naming
    def tearDown(self):
        pass

    def test_001(self):
        HEADING("OS API")

        cloudname = 'kilo'
        d = ConfigDict("cloudmesh.yaml")
        cloud_details = d["cloudmesh"]["clouds"][cloudname]

        cp = CloudProviderOpenstackAPI(cloudname, cloud_details)

        #pprint(cp.list_flavor(cloudname))

        # pprint(cp.list_image(cloudname))


        pprint(cp.list_vm(cloudname))

        #pprint(cp.list_quota(cloudname))

