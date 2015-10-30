from novaclient import client
from cloudmesh_client.common.ConfigDict import Config
from cloudmesh_client.common.ConfigDict import ConfigDict
from cloudmesh_client.cloud.iaas.CloudProviderOpenstack import CloudProviderOpenstack
import os
import requests
requests.packages.urllib3.disable_warnings()


#
# TODO: this class is in the wrong directory, it belongs in iaas for openstack
# TODO: the name get environment is quite awkward
# TODO: what implication would there if the cloud would not be openstack,
# we should make at least provisions for that the others are not
# implemented, but in general authentication should take a provider and use
# the provider to authenticate and not reimplementing what a provider is
# supposed to do.

#
# This was duplicated all over and it will not work as we also have to unset
#  the variables
#
def set_os_environ(cloudname):
    """Set os environment variables on a given cloudname"""
    try:
        d = ConfigDict("cloudmesh.yaml")
        credentials = d["cloudmesh"]["clouds"][cloudname]["credentials"]
        for key, value in credentials.iteritems():
            if key == "OS_CACERT":
                os.environ[key] = Config.path_expand(value)
            else:
                os.environ[key] = value
    except Exception, e:
        print(e)


class CloudProvider(object):

    @classmethod
    def get_environ(cls, cloudname):
        try:
            d = ConfigDict("cloudmesh.yaml")
            cloud = d["cloudmesh"]["clouds"][cloudname]
            cert = None

            if cloud["cm_type"] == "openstack":
                credentials = cloud["credentials"]

                # why not reuse the code from iaas?
                '''
                if "OS_CACERT" in credentials:
                    cert = Config.path_expand(credentials["OS_CACERT"])

                # TODO regions, and other OS_ env variables are not passed
                # along. we should use kwargs but make sure that vars not
                # supported bu OS are not passed along. Maybe we need to
                # separate them in the yaml file from the credentials and
                # assume that the credentials dict contains all we need to
                # outhentocate. Than we rename the others to cm_ instead of
                # OS_ and make sure we rewrite the register code and not
                # only read the credentials but also the host.

                if cert is not None:
                    nova = client.Client("2", credentials["OS_USERNAME"],
                                         credentials["OS_PASSWORD"],
                                         credentials["OS_TENANT_NAME"],
                                         credentials["OS_AUTH_URL"],
                                         cert)
                else:
                    nova = client.Client("2", credentials["OS_USERNAME"],
                                         credentials["OS_PASSWORD"],
                                         credentials["OS_TENANT_NAME"],
                                         credentials["OS_AUTH_URL"])


                return nova
                '''
                return CloudProviderOpenstack(cloudname, cloud).nova
        except Exception, e:
            raise Exception("Error in getting environment"
                            " for cloud: {}, {}".format(cloudname, e))