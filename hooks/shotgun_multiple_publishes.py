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
Hook executed when there are multiple published files in a Version.
This allows to determine which PublishedFile to pick in the list.

This default implementation cycles through the `viewer_extensions`
config parameter, and returns the first published file matching
one of the extensions.

This allows to select PublishedFiles based on the order of
`viewer_extensions`.

If none of the PublishedFiles match any of the extensions,
return the first one in the list.
"""
import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class ChoosePublishedFile(HookBaseClass):
    def execute(self, published_files, **kwargs):
        """
        Return the first PublishedFile matching
        `viewer_extensions` configuration parameter.

        If no PublishedFile matches the extensions,
        return the first one in the list.

        :param list published_files: A list of PublishedFiles
        :returns: The selected PublishedFile
        :raises: TankError if no PublishedFiles are provided.
        """
        if not published_files:
            raise TankError("published_files cannot be None!")
        viewer_extensions = self.parent.get_setting("viewer_extensions")
        published_file_ids = [pf["id"] for pf in published_files]
        published_files = self.sgtk.shotgun.find(
            "PublishedFile",
            [["id", "in", published_file_ids]],
            ["path"]
        )
        for viewer_extension in viewer_extensions:
            for published_file in published_files:
                path_on_disk = self.parent.get_path_on_disk(published_file)
                if path_on_disk and path_on_disk.endswith(".%s" % viewer_extension):
                    return published_file
        return published_files[0]




