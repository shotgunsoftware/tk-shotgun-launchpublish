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
Hook that is used to retrieve the local file path for a single PublishedFile entity 
"""
from tank import Hook

class ResolvePublishPath(Hook):
    """
    Hook to find and return the local file path for a single PublishedFile entity
    """    
    
    def execute(self, sg_publish_data, **kwargs):
        """
        Main hook entry point
        
        :param sg_publish_data: The PublishedFile entity to find the local file
                                path for.

        :returns:               The local file path of the published file or None.
        """

        # we already have the functionality we need in the Hook 
        # base class for the default behaviour!
        return self.get_publish_path(sg_publish_data)