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

If it is a Version and there's more than one PublishedFile linked
to it, this hook allows to determine which PublishedFile to pick.

The default implementation cycles through the `viewer_extensions`
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


class GetPublishedFile(HookBaseClass):
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
                publish_id = v[published_files_field][0]["id"]
                return self.published_file(published_file_entity_type, publish_id)
            else:
                # if there are multiple published files, pick one.
                viewer_extensions = self.parent.get_setting("viewer_extensions")
                if not viewer_extensions:
                    raise TankError(
                        "Sorry, viewer extensions must be provided when a Version has multiple PublishedFiles"
                    )
                published_file_ids = [pf["id"] for pf in v[published_files_field]]
                published_files = self.sgtk.shotgun.find(
                    published_file_entity_type,
                    [["id", "in", published_file_ids]],
                    ["path", "task", "entity"]
                )
                for viewer_extension in viewer_extensions:
                    for published_file in published_files:
                        path_on_disk = self.parent.get_path_on_disk(published_file)
                        if path_on_disk and path_on_disk.endswith(".%s" % viewer_extension):
                            return published_file
                return published_files[0]
        else:
            # entity is PublishedFile or TankPublishedFile. Return it
            return self.published_file(entity_type, entity_id)

    def published_file(self, entity_type, entity_id):
        """
        Return the PublishedFile or TankPublishedFile with path, task and entity
        fields

        :param entity_type: PublishedFile or TankPublishedFile
        :param entity_id: a Shotgun ID.
        :returns: the published file with the right fields.
        """
        return self.parent.shotgun.find_one(
            entity_type,
            [["id", "is", entity_id]], ["path", "task", "entity"])
