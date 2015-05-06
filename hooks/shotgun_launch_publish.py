# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook for launching the app for a publish.

This hook typically looks at the extension of the input file
and based on this determine which launcher app to dispatch
the request to.

If no suitable launcher is found, return False, and the app
will launch the file in default viewer.
"""

from tank import Hook
from tank import TankError
import os

class LaunchAssociatedApp(Hook):
    
    
    def execute(self, path, context, associated_entity, **kwargs):
        """
        Launches the associated app and starts tank.
        
        :param path: full path to the published file
        :param context: context object representing the publish
        :param associated_entity: same as context.entity
        """
        status = False

        if context is None:
            raise TankError("Context cannot be None!")

        ########################################################################
        # Example implementation below:

        if path.endswith(".nk"):
            # nuke
            status = True
            self._do_launch("launchnuke", "tk-nuke", path, context)

        elif path.endswith(".ma") or path.endswith(".mb"):
            # maya
            status = True
            self._do_launch("launchmaya", "tk-maya", path, context)

        elif path.endswith(".fbx"):
            # Motionbuilder
            status = True
            self._do_launch("launchmotionbuilder", "tk-motionbuilder", path, context)            
            
        elif path.endswith(".hrox"):
            # Hiero
            status = True
            self._do_launch("launchhiero", "tk-hiero", path, context)            
            
        elif path.endswith(".max"):
            # 3ds Max
            status = True
            self._do_launch("launch3dsmax", "tk-3dsmax", path, context)            
            
        elif path.endswith(".psd"):
            # Photoshop
            status = True
            self._do_launch("launchphotoshop", "tk-photoshop", path, context)
            
        # return an indication to the app whether we launched or not
        # if we return True here, the app will just exit
        # if we return False, the app may try other ways to launch the file.
        return status


    def _do_launch(self, launch_app_instance_name, engine_name, path, context):
        """
        Tries to create folders then launch the publish.
        """
        
        # in older configs, launch instances were named tk-shotgun-launchmaya
        # in newer configs, launch instances are named tk-multi-launchamaya
        old_config = "tk-shotgun-%s" % launch_app_instance_name
        new_config = "tk-multi-%s" % launch_app_instance_name
        
        if old_config in self.parent.engine.apps:
            # we have a tk-shotgun-xxx instance in the config
            app_instance = old_config
        
        elif new_config in self.parent.engine.apps:
            # we have a tk-multi-xxx instance in the config
            app_instance = new_config
            
        else:
            raise TankError("The '%s' app could not be found in the '%s' "
                            "environment!" % (new_config, self.parent.engine.environment.get("name")))        
        
        
        # first create folders based on the context - this is important because we 
        # are creating them in deferred mode, meaning that in some cases, new user sandboxes
        # maybe created at this point.
        if context.task:
            self.parent.tank.create_filesystem_structure("Task", context.task["id"], engine_name)
        elif context.entity:
            self.parent.tank.create_filesystem_structure(context.entity["type"], context.entity["id"], engine_name)
                        
        # now try to launch this via the tk-multi-launchapp
        try:
            # use new method
            self.parent.engine.apps[app_instance].launch_from_path_and_context(path, context)
        except AttributeError:
            # fall back onto old method
            self.parent.engine.apps[app_instance].launch_from_path(path)
            
        

