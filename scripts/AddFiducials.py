# Create a fiducial node of a certain name. This node can then be populated with control points
node_id = slicer.modules.markups.logic().AddNewFiducialNode('nodeList')
# self.markup_node = slicer.mrmlScene.GetNodeByID(node_id) # Self used when in module
nodeList = slicer.mrmlScene.GetNodeByID(node_id)
# To get a node from the scene
nodeList = slicer.util.getNode('nodeList')
# Adding a node to the scene
nodeList.AddControlPoint([0, 0, 0])
# Changing the color of a node
nodeList.GetDisplayNode().SetSelectedColor(0.3,0.6,0.1) # makes it green for healthy points
# Change visibiility of the points
nodeList.SetNthControlPointVisibility(0,True)


#
# TODO
#

# Turn off labels of control points

# Transform data to a different reference frame (Use Liv's code )



def initialize_points(self):
   slicer.modules.markups.logic().SetActiveListID(self.markup_node)
   self.markup_node.SetControlPointLabelFormat('P%d')
   for i in range(1, self.N_POINT + 1):
       self.markup_node.AddControlPoint([0, 0, 0])
   self.markup_node.UnsetAllControlPoints()
   self.markup_node.SetMaximumNumberOfControlPoints(self.N_POINT)