from __future__ import print_function
from cloudmesh_client.common.ConfigDict import ConfigDict

from cloudmesh_client.common.todo import TODO
# add imports for other cloud providers in future
from cloudmesh_client.shell.console import Console
from cloudmesh_client.cloud.ListResource import ListResource
from cloudmesh_client.common.Printer import Printer
from cloudmesh_client.db import CloudmeshDatabase
from cloudmesh_client.cloud.iaas.CloudProvider import CloudProvider
from cloudmesh_client.common.Error import Error
from uuid import UUID
from cloudmesh_client.common.dotdict import dotdict
from builtins import input
from pprint import pprint
from cloudmesh_client.default import Default

# noinspection PyPep8Naming
class Vm(ListResource):
    cm = CloudmeshDatabase()

    @classmethod
    def construct_ip_dict(cls, ip_addr, name="kilo"):
        try:
            d = ConfigDict("cloudmesh.yaml")
            cloud_details = d["cloudmesh"]["clouds"][name]

            # Handle Openstack Specific Output
            if cloud_details["cm_type"] == "openstack":
                ipaddr = {}
                for network in ip_addr:
                    index = 0
                    for ip in ip_addr[network]:
                        ipaddr[index] = {}
                        ipaddr[index]["network"] = network
                        ipaddr[index]["version"] = ip["version"]
                        ipaddr[index]["addr"] = ip["addr"]
                        index += 1
                return ipaddr

            # Handle EC2 Specific Output
            if cloud_details["cm_type"] == "ec2":
                print("ec2 ip dict yet to be implemented")
                TODO.implement()

            # Handle Azure Specific Output
            if cloud_details["cm_type"] == "azure":
                print("azure ip dict yet to be implemented")
                TODO.implement()

        except Exception as e:
            Error.error("error in vm construct dict", traceback=True)

    @classmethod
    def isUuid(cls, name):
        try:
            UUID(name, version=4)
            return True
        except ValueError:
            return False

    @classmethod
    def boot(cls, **kwargs):

        arg = dotdict(kwargs)

        for a in ["key", "name", "image", "flavor"]:
            if a not in kwargs:
                raise ValueError(a + " not in arguments to vm boot")

        conf = ConfigDict("cloudmesh.yaml")
        arg.username = conf["cloudmesh"]["profile"]["username"]
        arg.group = arg.group or Default.group
        cloud_provider = CloudProvider(arg.cloud).provider

        if "nics" in arg:
            nics = arg.nics
        else:
            nics = None

        d = {
            "name": arg.name,
            "image": arg.image,
            "flavor": arg.flavor,
            "key": arg.key,
            "secgroup": [arg.secgroup],
            "nics": nics,
            "meta": {'kind': 'cloudmesh',
                     'group': '{group}'.format(**arg)}
         }

        Console.ok("Machine {name} is being booted on cloud {cloud} ...".format(**arg))

        print(Printer.attribute(d))

        vm = cloud_provider.boot_vm(**d)

        cls.refresh(cloud=arg.cloud)

        # cls.cm.update("vm", name=data.name)

        return vm

    @classmethod
    def start(cls, **kwargs):
        arg = dotdict(kwargs)
        cloud_provider = CloudProvider(arg.cloud).provider
        for server in kwargs["servers"]:
            cloud_provider.start_vm(server)
            print("Machine {:} is being started on {:} Cloud...".format(server, cloud_provider.cloud))

            # Explicit refresh called after VM start, to update db.
            # cls.refresh(cloud=kwargs["cloud"])

    @classmethod
    def stop(cls, **kwargs):
        arg = dotdict(kwargs)
        cloud_provider = CloudProvider(arg.cloud).provider
        for server in kwargs["servers"]:
            cloud_provider.stop_vm(server)
            print("Machine {:} is being stopped on {:} Cloud...".format(server, cloud_provider.cloud))

            # Explicit refresh called after VM stop, to update db.
            # cls.refresh(cloud=kwargs["cloud"])

    @classmethod
    def delete(cls, **kwargs):
        arg = dotdict(kwargs)
        if "cloud" in arg:
            cloud_provider = CloudProvider(arg.cloud).provider
            for server in kwargs["servers"]:
                cloud_provider.delete_vm(server)
                print("VM {:} is being deleted on {:} cloud...".format(server, cloud_provider.cloud))

            cls.refresh(cloud=arg.cloud)
        else:

            clouds = set()
            for server in arg.servers:
                try:
                    vm = cls.cm.find(kind="vm", name=server)
                    cloud = vm[0]["category"]
                    cloud_provider = CloudProvider(cloud).provider
                    clouds.add(cloud)
                    cloud_provider.delete_vm(server)
                    print("VM {:} is being deleted on {:} cloud...".format(server, cloud))
                except:
                    print("VM {:} can not be found.".format(server))

            for cloud in clouds:
                cls.refresh(cloud=cloud)

    @classmethod
    def get_vms_by_name(cls, name, cloud):

        vm_data = cls.cm.find(kind="vm", name=name, category=cloud)
        if vm_data is None or len(vm_data) == 0:
            raise RuntimeError("VM data not found in database.")
        return vm_data

    @classmethod
    def rename(cls, **kwargs):

        arg = dotdict(kwargs)

        dry_run = False

        if arg.is_dry_run is not None:
            dry_run = arg.is_dry_run

        if dry_run:
            print("Running in dryrun mode...")

        cloud_provider = CloudProvider(kwargs["cloud"]).provider
        new_name = arg.new_name
        for server in arg.servers:

            # Check for vms with duplicate names in DB.
            vms = cls.get_vms_by_name(name=server, cloud=arg.cloud)

            if len(vms) > 1:
                users_choice = "y"

                if not arg.force:
                    print("More than 1 vms found with the same name as {}.".format(server))
                    users_choice = input("Would you like to auto-order the new names? (y/n): ")

                if users_choice.strip() == "y":
                    count = 1
                    for index in vms:
                        count_new_name = "{0}{1}".format(new_name, count)
                        # print(vms[index])

                        if not dry_run:
                            cloud_provider.rename_vm(vms[index]["uuid"], count_new_name)

                        print("Machine {0} with UUID {1} renamed to {2} on {3} cloud".format(vms[index]["name"],
                                                                                             vms[index]["uuid"],
                                                                                             count_new_name,
                                                                                             cloud_provider.cloud))
                        count += 1
                elif users_choice.strip() == "n":
                    if not dry_run:
                        cloud_provider.rename_vm(server, new_name)
                    print("Machine {0} renamed to {1} on {2} Cloud...".format(server, new_name, cloud_provider.cloud))
                else:
                    Console.error("Invalid Choice.")
                    return
            else:
                if not dry_run:
                    cloud_provider.rename_vm(server, new_name)
                print("Machine {0} renamed to {1} on {2} Cloud...".format(server, new_name, cloud_provider.cloud))

        if not dry_run:
            # Explicit refresh called after VM rename, to update db.
            cls.refresh(cloud=arg.cloud)

    @classmethod
    def info(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def list(cls, **kwargs):
        """
        This method lists all VMs of the cloud
        """

        arg = dotdict(kwargs)
        if "name" in arg:
            arg.name = arg.name

        arg.output = arg.output or 'table'

        #pprint (kwargs)
        # prevent circular dependency
        def vm_groups(vm):
            """

            :param vm: name of the vm
            :return: a list of groups the vm is in
            """

            try:
                query = {
                    "type": "vm",
                    "member": vm
                }

                d = cls.cm.find(kind="group", **query)
                groups_vm = set()
                if d is not None and len(d) > 0:
                    for vm in d:
                        groups_vm.add(d[vm]['name'])
                return list(groups_vm)
            except Exception as ex:
                Console.error(ex.message, ex)

        try:
            if "name" in arg and arg.name is not None:
                if cls.isUuid(arg.name):
                    elements = cls.cm.find(kind="vm",
                                           category=arg.category,
                                           uuid=arg.name)
                else:
                    elements = cls.cm.find(kind="vm",
                                           category=arg.category,
                                           label=arg.name)
            else:
                elements = cls.cm.find(kind="vm",
                                       category=arg.category)

            if elements is None or len(elements) == 0:
                return None

            for elem in elements:
                element = elem
                name = element["name"]
                groups = vm_groups(name)
                element["group"] = ','.join(groups)

            # print(elements)

            # order = ['id', 'uuid', 'name', 'cloud']
            (order, header) = CloudProvider(arg.category).get_attributes("vm")

            # order = None
            if "name" in arg and arg.name is not None:
                return Printer.attribute(elements[0],
                                         output=arg.output)
            else:
                return Printer.write(elements,
                                     order=order,
                                     output=arg.output)
        except Exception as ex:
            Console.error(ex.message, ex)

    @classmethod
    def clear(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def refresh(cls, **kwargs):
        # print("Inside refresh")

        return cls.cm.refresh("vm", kwargs["cloud"])

    @classmethod
    def status_from_cloud(cls, **kwargs):
        cloud_provider = CloudProvider(kwargs["cloud"]).provider
        vm = cloud_provider.get_vm(name=kwargs["name"])
        return vm["status"]

    @classmethod
    def set_vm_login_user(cls, name, cloud, username):
        print(name, username)
        ValueError("this method is wrong implemented")

        '''
        if cls.isUuid(name):
            uuid = name
        else:
            vm_data = cls.cm.find(kind="vm", category=cloud, label=name)
            if vm_data is None or len(vm_data) == 0:
                raise RuntimeError("VM with label {} not found in database.".format(name))
            uuid = list(vm_data.values())[0]["uuid"]

        user_map_entry = cls.cm.find(kind="VMUSERMAP", vm_uuid=uuid)

        if user_map_entry is None or len(user_map_entry) == 0:
            user_map_dict = cls.cm.db_obj_dict("VMUSERMAP", vm_uuid=uuid, username=username)
            cls.cm.add_obj(user_map_dict)
            cls.cm.save()
        else:
            cls.cm.update_vm_username(vm_uuid=uuid, username=username)
        '''

    @classmethod
    def get_vm_login_user(cls, name, cloud):
        print(name, cloud)

        ValueError("this method is wrong implemented")

        '''
        if cls.isUuid(name):
            uuid = name
        else:
            vm_data = cls.cm.find(kind="vm", category=cloud, label=name)
            if vm_data is None or len(vm_data) == 0:
                raise RuntimeError("VM with label {} not found in database.".format(name))
            uuid = list(vm_data.values())[0]["uuid"]

        # print(uuid)

        user_map_entry = cls.cm.find("VMUSERMAP", vm_uuid=uuid)

        # print(user_map_entry)

        if user_map_entry is None or len(user_map_entry) == 0:
            return None
        else:
            return list(user_map_entry.values())[0]["username"]
        '''

    @classmethod
    def get_vm_public_ip(cls, vm_name, cloud):
        """

        :param vm_name: Name of the VM instance whose Public IP has to be retrieved from the DB
        :param cloud: Libcloud supported Cloud provider name
        :return: Public IP as a list
        """
        public_ip_list = []
        vms = cls.get_vms_by_name(vm_name, cloud)
        keys = vms.keys()
        if keys is not None and len(keys) > 0:
            public_ip = vms[keys[0]]["public_ips"]
            if public_ip is not None and public_ip != "":
                public_ip_list.append(public_ip)
        return public_ip_list
