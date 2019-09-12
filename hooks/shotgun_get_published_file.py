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

It decides which published file to return, or if it needs to raise a TankError.

This default implementation returns the first published file it finds, with the proper fields.

"""
import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class GetPublishedFile(HookBaseClass):
    _PUBLISHED_FILE_FIELDS = ["path", "task", "entity"]

    def execute(self, entity_type, entity_id, published_file_entity_type, **kwargs):
        """
        Given a Version, PublishedFile or TankPublishedFile,
        return the PublishedFile or TankPublishedFile linked to it.

        For a Version with multiple PublishedFiles,
        return the first PublishedFile matching
        `viewer_extensions` configuration parameter.
        If no PublishedFile matches the extensions,
        return the first one in the list.

        :param str entity_type: Version, PublishedFile or TankPublishedFile.
        :param int entity_id: The id of the entity.
        :param str published_file_entity_type: PublishedFile or TankPublishedFile.
        :returns: The selected PublishedFile
        :raises: TankError if a PublishedFile cannot be found.
        """
        if entity_type == "Version":
            # entity is a Version so try to get the id
            # of the published file it is linked to
            if published_file_entity_type == "PublishedFile":
                published_files_field = "published_files"
            else:
                published_files_field = "tank_published_file"

            v = self.parent.shotgun.find_one("Version", [["id", "is", entity_id]], [published_files_field])
            if not v.get(published_files_field):
                raise TankError("Sorry, this can only be used on Versions with an associated published file.")
            if len(v[published_files_field]) == 1:
                return self.resolve_single_file(
                    published_file_entity_type,
                    v[published_files_field][0],
                )
            else:
                return self.resolve_multiple_files(
                    published_file_entity_type,
                    v[published_files_field]
                )
        else:
            # entity is PublishedFile or TankPublishedFile. Return it
            return self.published_file(entity_type, entity_id)

    def resolve_single_file(self, entity_type, published_file):
        """
        Decide wether or not to return the published file, or raise a TankError.
        This default implementation returns it.

        :param str entity_type: PublishedFile or TankPublishedFile.
        :param dict published_file: The published file.
        :returns: The published file with the right fields.
        """
        return self.published_file(entity_type, published_file["id"])

    def resolve_multiple_files(self, published_file_type, published_files):
        """
        Decide which published file to return, or raise a TankError.
        This default implementation returns the first one.
        :param str published_file_type: PublishedFile or TankPublishedFile.
        :param list published_files: The published files.
        :returns: The first published file with the right fields.
        """
        return self.published_file(published_file_type, published_files[0]["id"])

    def published_file(self, published_file_type, published_file_id):
        """
        Return the PublishedFile or TankPublishedFile with path, task and entity
        fields.
        :param str published_file_type: PublishedFile or TankPublishedFile
        :param int published_file_id: a Shotgun ID.
        :returns: the published file with the right fields.
        """
        return self.parent.shotgun.find_one(
            published_file_type,
            [["id", "is", published_file_id]], self._PUBLISHED_FILE_FIELDS)
