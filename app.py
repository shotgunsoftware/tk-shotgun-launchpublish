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
App that launches a Publish from inside of Shotgun.

"""

from tank.platform import Application
from tank import TankError
import tank
import sys
import os
import re
import urllib2

class LaunchPublish(Application):
    @property
    def context_change_allowed(self):
        """
        Returns whether this app allows on-the-fly context changes without
        needing itself to be restarted.

        :rtype: bool
        """
        return True
    
    def init_app(self):
        deny_permissions = self.get_setting("deny_permissions")
        deny_platforms = self.get_setting("deny_platforms")
        title = self.get_setting("display_name", "Open in Associated Application")
        
        p = {
            "title": title,
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
            if not app_path: 
                raise KeyError()
        except KeyError:
            raise Exception("Platform '%s' is not supported." % system) 

        # run the app
        if system.startswith("linux"):
            cmd = '%s "%s" &' % (app_path, path)
        elif system == "darwin":
            cmd = 'open -n -a "%s" "%s"' % (app_path, path)
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
                          "on support@shotgunsoftware.com." % app_path )

    def launch_publish(self, entity_type, entity_ids):
        published_file_entity_type = tank.util.get_published_file_entity_type(self.tank)
        
        if entity_type not in [published_file_entity_type, "Version"]:
            raise Exception("Sorry, this app only works with entities of type %s or Version." % published_file_entity_type)

        if len(entity_ids) != 1:
            raise Exception("Action only accepts a single item.")
        try:
            d = self.execute_hook(
                "hook_get_published_file",
                entity_type=entity_type,
                entity_id=entity_ids[0],
                published_file_entity_type=published_file_entity_type
            )
        except TankError as e:
            self.log_error("Failed to get a published file for %s %s: %s" % (entity_type, entity_ids[0], e))
            return

        path_on_disk = self.get_path_on_disk(d)

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
    
        # now get the context - try to be as inclusive as possible here:
        # start with the task, if that doesn't work, fall back onto the path
        # this is because some paths don't include all the metadata that
        # is contained inside the publish record (e.g typically not the task)
        if d.get("task"):
            ctx = self.tank.context_from_entity("Task", d.get("task").get("id"))
        else:
            ctx = self.tank.context_from_path(path_on_disk)
        
        # call out to the hook
        try:
            launched = self.execute_hook("hook_launch_publish", 
                                         path=path_on_disk, 
                                         context=ctx, 
                                         associated_entity=d.get("entity"))
        except TankError, e:
            self.log_error("Failed to launch an application for this published file: %s" % e)
            return
        
        if not launched:
            # hook didn't know how to launch this
            # just use std associated file launch
            self.launch(path_on_disk)

    def get_path_on_disk(self, published_file):
        """
        Retrieve, if possible, the path on disk of a PublishedFile.

        :param published_file: A PublishedFile dictionary.
        :returns: The path on disk if found, otherwise ``None``.
        """
        path_on_disk = published_file.get("path", {}).get("local_path")
        if path_on_disk:
            return path_on_disk
        # If this PublishedFile came from a zero config publish, it will
        # have a file URL rather than a local path.
        url = published_file.get("path", {}).get("url")
        if url is not None:
            # We might have something like a %20, which needs to be
            # unquoted into a space, as an example.
            if "%" in url:
                url = urllib2.unquote(url)

            # If this came from a file url via a zero-config style publish
            # then we'll need to remove that from the head in order to end
            # up with the local disk path to the file.
            #
            # On Windows, we will have a path like file:///E:/path/to/file.jpg
            # and we need to ditch all three of the slashes at the head. On
            # other operating systems it will just be file:///path/to/file.jpg
            # and we will want to keep the leading slash.
            if sys.platform.startswith("win"):
                pattern = r"^file:///"
            else:
                pattern = r"^file://"
            return re.sub(pattern, "", url)
        else:
            self.log_error("Unable to determine the path on disk for entity id=%s." % published_file["id"])
            return None
