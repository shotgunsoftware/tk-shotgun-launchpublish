# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook executed to get a PublishedFile from a Version
or a PublishedFile (legacy TankPublishedFile supported).

This implementation returns the first published file it finds
matching extensions in the order of viewer extensions.
If none are found, raise a TankError.
"""

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class GetPublishedFileForViewer(HookBaseClass):
    """
    In order to work, this hook needs to inherit from shotgun_get_published_file.GetPublishedFile
    """

    def resolve_single_file(self, entity_type, published_file):
        """
        Decide wether or not to return the published file, or raise a TankError.
        This default implementation returns the published file only if it matches
        one of the viewer_extensions.

        :param str entity_type: PublishedFile or TankPublishedFile.
        :param dict published_file: The published file.
        :returns: The published file with the right fields.
        :raises: TankError
        """
        viewer_extensions = self.parent.get_setting("viewer_extensions")
        if not viewer_extensions:
            raise TankError(
                "Sorry, viewer extensions must be provided."
            )
        path_on_disk = self.parent.get_path_on_disk(published_file)
        if path_on_disk:
            for viewer_extension in viewer_extensions:
                if path_on_disk.endswith(".%s" % viewer_extension):
                    return self.published_file(entity_type, published_file["id"])
        raise TankError("Published File %s does not match viewer extensions %s" % (
            published_file,
            viewer_extensions
        ))

    def resolve_multiple_files(self, published_file_type, published_files):
        """
        Decide which published file to return, or raise a TankError.
        Return the first published file matching a viewer extension,
        otherwise raise a TankError.

        :param str published_file_type: PublishedFile or TankPublishedFile.
        :param list published_files: The published files.
        :returns: The first published file with the right fields.
        :raises: TankError
        """
        viewer_extensions = self.parent.get_setting("viewer_extensions")
        if not viewer_extensions:
            raise TankError(
                "Sorry, viewer extensions must be provided."
            )
        published_file_ids = [pf["id"] for pf in published_files]
        published_files = self.sgtk.shotgun.find(
            published_file_type,
            [["id", "in", published_file_ids]],
            self._PUBLISHED_FILE_FIELDS
        )
        for viewer_extension in viewer_extensions:
            for published_file in published_files:
                path_on_disk = self.parent.get_path_on_disk(published_file)
                if path_on_disk and path_on_disk.endswith(".%s" % viewer_extension):
                    return published_file
        raise TankError(
            "Could not find a published file matching viewer extensions %s. Published files: %s" % (
                viewer_extensions,
                published_files
            )
        )

