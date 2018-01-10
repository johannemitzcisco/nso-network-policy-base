# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
from ncs.dp import Action
from ncs.maapi import Maapi


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ' ', service.name, ')')
        service_node = service._parent._parent
        self.log.info("Service Node: ", service_node._path)
        self.log.info("Root Node: ", root._path)

        # Apply topology templates
        for topology in service.topology:
            vars = ncs.template.Variables()
            self.log.info('======= Topology Specific Policies =============')
            for policyname in topology.policies: # This gets the list of different policy types defined
                self.log.info('PolicyName: ', policyname)
                policylist = ncs.maagic.cd(topology.policies,policyname)
                for policyentryname in policylist: # This get each list entry in the policy type
                    self.log.info('PolicyEntryName: ', policyentryname)
                    policyentrynode = ncs.maagic.cd(policylist,policyentryname)
                    vars.add('POLICY-NAME', policyentrynode.policy_name)
                    policynodetemplatestr = '/npb:network/npb:policy-definitions/tpb:topology/'+str(policyname)+'{"'+policyentrynode.policy_name+'"}/template'
                    self.log.info('Policy Template Location: ', policynodetemplatestr)
                    policy_template_name = ncs.maagic.cd(root, policynodetemplatestr)
                    for device in topology.endpoint:
                        vars = ncs.template.Variables()
                        for hostname_policy in device.policies.hostname:
                            vars.add('DEVICE-NAME', hostname_policy.hostname)
                            hostname = hostname_policy.hostname
                        if hostname not in root.devices.device:  # If the device does not exist in NSO then we can't configure it
                            continue
                        vars.add('SERVICE-NAME', service.name)
                        vars.add('DEVICE-TOPOLOGY-NAME', device.topology_name)
                        self.log.info('APPLY TEMPLATE: Device: ', hostname, ' Template: ', policy_template_name)
                        template = ncs.template.Template(root.devices)
                        template.apply(policy_template_name, vars)
                        template = ncs.template.Template(service_node)
                        template.apply(policy_template_name, vars)
            template = ncs.template.Template(service_node)
            self.log.info('======= Device Specific Policies =============')
            for device in topology.endpoint:
                vars = ncs.template.Variables()
                for hostname_policy in device.policies.hostname:
                    vars.add('DEVICE-NAME', hostname_policy.hostname)
                    hostname = hostname_policy.hostname
                if hostname not in root.devices.device:  # If the device does not exist in NSO then we can't configure it
                    continue
                vars.add('SERVICE-NAME', service.name)
                vars.add('DEVICE-TOPOLOGY-NAME', device.topology_name)
                for policyname in device.policies: # This gets the list of different policy types defined
                    self.log.info('PolicyName: ', policyname)
                    policylist = ncs.maagic.cd(device.policies,policyname)
                    for policyentryname in policylist: # This get each list entry in the policy type
                        self.log.info('PolicyEntryName: ', policyentryname)
                        policyentrynode = ncs.maagic.cd(policylist,policyentryname)
                        vars.add('POLICY-NAME', policyentrynode.policy_name)
                        policynodetemplatestr = '/npb:network/npb:policy-definitions/tpb:endpoint/'+str(policyname)+'{"'+str(policyentrynode.policy_name)+'"}/template'
                        self.log.info('Policy Template Location: ', policynodetemplatestr)
                        policy_template_name = ncs.maagic.cd(root, policynodetemplatestr)
                        self.log.info('APPLY TEMPLATE: Device: ', hostname, ' Template: ', policy_template_name)
                        if policy_template_name is not None:
                            template.apply(policy_template_name, vars)
            # Apply Interface Policies
            self.log.info('======= Connection Specific Policies =============')
            for connection in topology.connection:
                vars = ncs.template.Variables()
                vars.add('SERVICE-NAME', service.name)
                connection_name = connection.connection_name
                self.log.info('Connection: ', connection_name, ' Path: ', connection._path)
                self.log.info('SERVICE-NAME: ', service.name)
                for connectiontype in connection.type:
                    connectiontypenode = ncs.maagic.cd(connection.type,connectiontype)
                    self.log.info('Connection Type: ', connectiontype, ' ', type(connectiontypenode))
                    try:
                        if connectiontypenode is not None and not isinstance(connectiontypenode, ncs.maagic.Case) and connectiontypenode.policy_name is not None:
                            self.log.info('Policy Name: ', connectiontypenode.policy_name)
                            break
                    except AttributeError as error:
                        self.log.info('error: ', error)
                        pass
                for side in ('A', 'B'):
                    self.log.info('SIDE: ', side)
                    if side in connection.side:
                        side_device = connection.side[side].device
                        if side_device is not None:
                            self.log.info('DEVICE-TOPOLOGY-NAME: ', side_device)
                            for hostname_policy in topology.endpoint[side_device].policies.hostname:
                                hostname = hostname_policy.hostname
                            if hostname not in root.devices.device: # If the device does not exist in NSO then we can't configure it
                                continue
                            self.log.info('CONNECTION-NAME: ', connection_name)
                            self.log.info('DEVICE-NAME: ', hostname)
                            vars.add('DEVICE-TOPOLOGY-NAME', side_device)
                            vars.add('CONNECTION-NAME', connection_name)
                            vars.add('DEVICE-NAME', hostname)
                            side_device_role_location = '/npb:network/npb:network-service{'+service.name+'}/tpb:topology{'+topology.name+'}/tpb:endpoint{'+side_device+'}/tpb:policies/physical-device-policy-base:role'
                            self.log.info('Side Device: ', side_device, ' Location: ', side_device_role_location)
                            side_device_role = ncs.maagic.cd(root, side_device_role_location)
                            role = side_device_role.keys()[0][0] # Get the first key and get the first element from that tuple
                            self.log.info('Device role: ', role, ' side_device_role: ', type(side_device_role), ' ', side_device_role.keys(), ' ::: ', type(side_device_role.keys()))
                            policynodetemplatestr = '/npb:network/npb:policy-definitions/tpb:connection/'+connectiontype+'{"'+connectiontypenode.policy_name+'"}/connection-policy-base:'+str(role)+'/connection-policy-base:template'
                            self.log.info('Policy Node: ', policynodetemplatestr)
                            policy_template_name = ncs.maagic.cd(root, policynodetemplatestr)
                            self.log.info('APPLY TEMPLATE: Device: ', side_device, ' Template: ', policy_template_name)
                            template.apply(policy_template_name, vars)

    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

class LoadServiceTemplate(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):
        service_name = input.network_name
        topology_template = input.topology_template
        self.log.info('action name: ', name)
        self.log.info('Service Name: ', service_name)
        self.log.info('Template: ', topology_template)
        self.log.info('Keypath: ', kp)
#        self.log.info('SELF WT: ', type(self._wt), ' ', dir(self._wt))
        # Updating the output data structure will result in a response
        # being returned to the caller.
        with ncs.maapi.Maapi() as m:
            with ncs.maapi.Session(m, uinfo.username, uinfo.context):
                with m.start_write_trans() as t:
                    template_name = t.get_elem("/network/policy-definitions/network/tpb:topology-templates{"+topology_template+"}/model-template-file")
                    self.log.info('Topology Template Name: ', template_name)
                    vars = ncs.template.Variables()
                    vars.add('SERVICE-NAME', service_name)
                    m.apply_template(t.th,name=str(template_name),path=kp,vars=vars)
                    t.apply()

class TestService(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):
        self.log.info('action name: ', name)
        self.log.info('Keypath: ', kp)

        with ncs.maapi.Maapi() as m:
            with ncs.maapi.Session(m, uinfo.username, uinfo.context):
                with m.start_write_trans() as t:
                    service = ncs.maagic.get_node(t, kp)
                    service_status = "PASSED"
                    for test in service.test:
                        self.log.info('test device: ', test.device)
                        device = ncs.maagic.get_node(t, '/devices/device{'+str(test.device)+'}')
                        command = test.command
                        match_criteria = test.match_criteria
                        self.log.info('device: ', device)
                        self.log.info('test command: ', command)
                        self.log.info('match_criteria: ', match_criteria)
                        action = device.live_status.ios_stats__exec.any
                        action_input = action.get_input()
                        action_input.args = str(command).split(' ')
                        action_result = action.request(action_input)
                        self.log.info('Command Returned: ', action_result.result)
                        test.command_output = action_result.result
                        test_result = "FAILED"
                        for line in action_result.result.splitlines():
                            if all(crition in line for crition in match_criteria):
                                test_result = "PASSED"
                                break;
                        if test_result == "FAILED":
                            service_status = "FAILED"
                        test.status = test_result
                        service.service_status = service_status
                    t.apply()

# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('network-policy-base-servicepoint', ServiceCallbacks)
        self.register_action('loadservicetemplate-action', LoadServiceTemplate)
        self.register_action('testservice-action', TestService)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
