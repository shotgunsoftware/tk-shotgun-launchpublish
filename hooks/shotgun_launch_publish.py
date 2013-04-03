"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

Hook for launching the app for a publish.

This hook typically looks at the extension of the input file
and based on this determine which launcher app to dispatch
the request to.

If no suitable launcher is found, return False, and the app
will launch the file in default viewer.
"""

from tank import Hook
import os

class LaunchAssociatedApp(Hook):
    
    def _create_folders(self, engine, entity):
        """
        Helper method. Creates folders if an entity is specified.
        """
        if entity:
            self.parent.tank.create_filesystem_structure(entity["type"], entity["id"], engine)                
    
    def execute(self, path, context, associated_entity, **kwargs):

        engine = self.parent.engine
        status = False

        ########################################################################
        # Example implementation below:

        if path.endswith(".nk"):
            # nuke
            if "tk-shotgun-launchnuke" in engine.apps:
                # looks like there is a nuke launcher installed in this system!
                self._create_folders("tk-nuke", associated_entity)
                status = True
                engine.apps["tk-shotgun-launchnuke"].launch_from_path(path)

        elif path.endswith(".ma") or path.endswith(".mb"):
            # maya
            
            if "tk-shotgun-launchmaya" in engine.apps:
                # looks like there is a maya launcher installed in this system!
                self._create_folders("tk-maya", associated_entity)
                status = True
                engine.apps["tk-shotgun-launchmaya"].launch_from_path(path)

        elif path.endswith(".fbx"):
            # maya
            if "tk-shotgun-launchmotionbuilder" in engine.apps:
                # looks like there is a maya launcher installed in this system!
                self._create_folders("tk-motionbuilder", associated_entity)
                status = True
                engine.apps["tk-shotgun-launchmotionbuilder"].launch_from_path(path)

        elif path.endswith(".hrx"):
            # maya
            if "tk-shotgun-launchhiero" in engine.apps:
                # looks like there is a maya launcher installed in this system!
                self._create_folders("tk-hiero", associated_entity)
                status = True
                engine.apps["tk-shotgun-launchhiero"].launch_from_path(path)

        elif path.endswith(".max"):
            # maya
            if "tk-shotgun-launch3dsmax" in engine.apps:
                # looks like there is a maya launcher installed in this system!
                self._create_folders("tk-3dsmax", associated_entity)
                status = True
                engine.apps["tk-shotgun-launch3dsmax"].launch_from_path(path)

        elif path.endswith(".psd"):
            # photoshop
            if "tk-shotgun-launchphotoshop" in engine.apps:
                self._create_folders("tk-photoshop", associated_entity)
                status = True
                engine.apps["tk-shotgun-launchphotoshop"].launch_from_path(path)

        return status
