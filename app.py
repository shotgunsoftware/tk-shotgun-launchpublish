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

from sgtk.platform import Application
from sgtk import TankError
from sgtk import util
import sgtk
import sys
import os
import re
from tank_vendor.six.moves import urllib


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

        p = {
            "title": "Open in Associated Application",
            "deny_permissions": deny_permissions,
            "deny_platforms": deny_platforms,
            "supports_multiple_selection": False,
        }

        self.engine.register_command("launch_publish", self.launch_publish, p)

    def launch(self, path):
        self.log_debug("Launching default system viewer for file %s" % path)

        # run the app
        if util.is_linux():
            cmd = 'xdg-open "%s"' % path
        elif util.is_macos():
            cmd = 'open "%s"' % path
        elif util.is_windows():
            cmd = 'cmd.exe /C start "file" "%s"' % path
        else:
            raise Exception("Platform '%s' is not supported." % sys.platform)

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

        try:
            app_path = None
            if util.is_linux():
                app_path = self.get_setting("viewer_path_linux")
                cmd = '%s "%s" &' % (app_path, path)
            elif util.is_macos():
                app_path = self.get_setting("viewer_path_mac")
                cmd = 'open -n "%s" --args "%s"' % (app_path, path)
            elif util.is_windows():
                app_path = self.get_setting("viewer_path_windows")
                cmd = 'start /B "Maya" "%s" "%s"' % (app_path, path)

            if not app_path:
                raise KeyError()
        except KeyError:
            raise Exception("Platform '%s' is not supported." % sys.platform)

        self.log_debug("Executing launch command '%s'" % cmd)
        exit_code = os.system(cmd)
        if exit_code != 0:
            self.log_error(
                "Failed to launch Viewer! This is most likely because the path "
                "to the viewer executable is not set to a correct value. The "
                "current value is '%s' - please double check that this path "
                "is valid and update as needed in this app's configuration. "
                "If you have any questions, don't hesitate to contact support "
                "via %s." % (app_path, sgtk.support_url,)
            )

    def launch_publish(self, entity_type, entity_ids):

        published_file_entity_type = sgtk.util.get_published_file_entity_type(self.sgtk)

        if entity_type not in [published_file_entity_type, "Version"]:
            raise Exception(
                "Sorry, this app only works with entities of type %s or Version."
                % published_file_entity_type
            )

        if len(entity_ids) != 1:
            raise Exception("Action only accepts a single item.")

        if entity_type == "Version":
            # entity is a version so try to get the id
            # of the published file it is linked to:
            if published_file_entity_type == "PublishedFile":
                v = self.shotgun.find_one(
                    "Version", [["id", "is", entity_ids[0]]], ["published_files"]
                )
                if not v.get("published_files"):
                    self.log_error(
                        "Sorry, this can only be used on Versions with an associated Published File."
                    )
                    return
                publish_id = v["published_files"][0]["id"]
            else:  # == "TankPublishedFile":
                v = self.shotgun.find_one(
                    "Version", [["id", "is", entity_ids[0]]], ["tank_published_file"]
                )
                if not v.get("tank_published_file"):
                    self.log_error(
                        "Sorry, this can only be used on Versions with an associated Published File."
                    )
                    return
                publish_id = v["tank_published_file"]["id"]

        else:
            publish_id = entity_ids[0]

        # first get the path to the file on the local platform
        d = self.shotgun.find_one(
            published_file_entity_type,
            [["id", "is", publish_id]],
            ["path", "task", "entity"],
        )
        path_on_disk = d.get("path").get("local_path")

        # If this PublishedFile came from a zero config publish, it will
        # have a file URL rather than a local path.
        if path_on_disk is None:
            path_on_disk = d.get("path").get("url")
            if path_on_disk is not None:
                # We might have something like a %20, which needs to be
                # unquoted into a space, as an example.
                if "%" in path_on_disk:
                    path_on_disk = urllib.parse.unquote(path_on_disk)

                # If this came from a file url via a zero-config style publish
                # then we'll need to remove that from the head in order to end
                # up with the local disk path to the file.
                #
                # On Windows, we will have a path like file:///E:/path/to/file.jpg
                # and we need to ditch all three of the slashes at the head. On
                # other operating systems it will just be file:///path/to/file.jpg
                # and we will want to keep the leading slash.
                if util.is_windows():
                    pattern = r"^file:///"
                else:
                    pattern = r"^file://"

                path_on_disk = re.sub(pattern, "", path_on_disk)
            else:
                self.log_error(
                    "Unable to determine the path on disk for entity id=%s."
                    % publish_id
                )

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
            self.log_error(
                "The file associated with this publish, "
                "%s, cannot be found on disk!" % path_on_disk
            )
            return

        # now get the context - try to be as inclusive as possible here:
        # start with the task, if that doesn't work, fall back onto the path
        # this is because some paths don't include all the metadata that
        # is contained inside the publish record (e.g typically not the task)
        if d.get("task"):
            ctx = self.sgtk.context_from_entity("Task", d.get("task").get("id"))
        else:
            ctx = self.sgtk.context_from_path(path_on_disk)

        # call out to the hook
        try:
            launched = self.execute_hook(
                "hook_launch_publish",
                path=path_on_disk,
                context=ctx,
                associated_entity=d.get("entity"),
            )
        except TankError as e:
            self.log_error(
                "Failed to launch an application for this published file: %s" % e
            )
            return

        if not launched:
            # hook didn't know how to launch this
            # just use std associated file launch
            self.launch(path_on_disk)
