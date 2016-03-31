# -*- coding: utf-8 -*-
import io
import json

from errbot import BotPlugin, botcmd, arg_botcmd
from errbot.flow import FlowNode, FlowRoot


class Flows(BotPlugin):
    """ Management commands related to flows / conversations.
    """

    def recurse_node(self, response: io.StringIO, stack, f: FlowNode):
        if f in stack:
            response.write("%s⥀\n" % ("\t" * len(stack)))
            return
        if isinstance(f, FlowRoot):
            response.write("Flow " + f.name + ": " + f.description + "\n")
        else:
            cmd = self._bot.commands[f.command]
            response.write("%s⤷%s: %s\n" % ("\t" * len(stack), f, cmd.__doc__))
        for _, sf in f.children:
            self.recurse_node(response, stack + [f], sf)

    # noinspection PyUnusedLocal
    @botcmd(admin_only=True)
    def flows_list(self, mess, args):
        """ Displays the list of setup flows.
        """
        with io.StringIO() as response:
            if args:
                flow = self._bot.flow_executor.flow_roots.get(args, None)
                if flow is None:
                    return "Flow %s doesn't exist." % args
                self.recurse_node(response, [], flow)
            else:
                for name, flow in self._bot.flow_executor.flow_roots.items():
                    response.write(name + ": " + flow.description + "\n")
            return response.getvalue()

    @botcmd(split_args_with=' ', syntax='<name> [initial_payload]')
    def flows_start(self, mess, args):
        """ Manually start a flow within the context of the calling user.
        You can prefeed the flow data with a json payload.
        Example:
             !flows start poll_setup {"title":"yeah!","options":["foo","bar","baz"]}
        """
        if not args:
            return "You need to specify a flow to manually start"

        context = {}
        flow_name = args[0]
        if len(args) > 1:
            json_payload = ' '.join(args[1:])
            try:
                context = json.loads(json_payload)
            except Exception as e:
                return "Cannot parse json %s: %s" % (json_payload, e)
        self._bot.flow_executor.start_flow(flow_name, mess.frm, context)
        return "Flow %s started ..." % flow_name