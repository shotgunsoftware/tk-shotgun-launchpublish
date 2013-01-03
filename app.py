"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

App that launches a Publish from inside of Shotgun.

"""

from tank.platform import Application
import tank
import sys
import os

class LaunchPublish(Application):
    
    def init_app(self):
        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")
        
        p = {
            "title": "Open in Associated Application",
            "entity_types": ["TankPublishedFile"],
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": False
        }
        
        self.engine.register_command("launch_publish", self.launch_publish, p)

    def launch(self, path):
        self.log_debug("Launching default system viewer for file %s" % path)        
        
        # get the setting        
        system = sys.platform
        
        # run the app
        if system == "linux2":
            cmd = 'xdg-open "%s"' % path
        elif system == "darwin":
            cmd = 'open "%s"' % path
        elif system == "win32":
            cmd = 'cmd.exe /C start "file" "%s"' % path
        else:
            raise Exception("Platform '%s' is not supported." % system)
        
        self.log_debug("Executing command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            self.log_error("Failed to launch '%s'!" % cmd)


    def _launch_viewer(self, path):
        """
        Launches an image viewer based on config settings.
        We assume that the path to the image is just passed as a param to the viewer.
        This seems to be standard for most apps.
        """
        
        # get the setting        
        system = sys.platform
        try:
            app_setting = {"linux2": "viewer_path_linux", 
                           "darwin": "viewer_path_mac", 
                           "win32": "viewer_path_windows"}[system]
            app_path = self.get_setting(app_setting)
            if not app_path: raise KeyError()
        except KeyError:
            raise Exception("Platform '%s' is not supported." % system) 

        # run the app
        if system == "linux2":
            cmd = '%s "%s" &' % (app_path, path)
        elif system == "darwin":
            cmd = 'open -n "%s" --args "%s"' % (app_path, path)
        elif system == "win32":
            cmd = 'start /B "Maya" "%s" "%s"' % (app_path, path)
        else:
            raise Exception("Platform '%s' is not supported." % system)
        
        self.log_debug("Executing launch command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            self.log_error("Failed to launch Viewer! This is most likely because the path "
                          "to the viewer executable is not set to a correct value. The " 
                          "current value is '%s' - please double check that this path "
                          "is valid and update as needed in this app's configuration. "
                          "If you have any questions, don't hesitate to contact support "
                          "on tanksupport@shotgunsoftware.com." % app_path )
        

    def launch_publish(self, entity_type, entity_ids):
        if entity_type != "TankPublishedFile":
            raise Exception("Action only allows entity_type='TankPublishedFile'.")
        
        if len(entity_ids) != 1:
            raise Exception("Action only accepts a single item.")

        publish_id = entity_ids[0]

        # first get the path to the file on the local platform
        d = self.shotgun.find_one("TankPublishedFile", [["id", "is", publish_id]], ["path"])
        path_on_disk = d.get("path").get("local_path")
        
        # first check if we should pass this to the viewer
        # hopefully this will cover most image sequence types
        # any image sequence types not passed to the viewer
        # will fail later when we check if the file exists on disk
        for x in self.get_setting("viewer_extensions", {}):
            if path_on_disk.endswith(".%s" % x):
                self._launch_viewer(path_on_disk)
                return
        
        # check that it exists        
        if not os.path.exists(path_on_disk):            
            self.log_error("The file associated with this publish, "
                            "%s, cannot be found on disk!" % path_on_disk)
            return
    
        # get the context
        ctx = self.tank.context_from_path(path_on_disk)
        
        # call out to the hook
        result = self.execute_hook("hook_launch_publish", path=path_on_disk, context=ctx)
        
        if result == False:
            # hook didn't know how to launch this
            # just use std associated file launch
            self.launch(path_on_disk)

        