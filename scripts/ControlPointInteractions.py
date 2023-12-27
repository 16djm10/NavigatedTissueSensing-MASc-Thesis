'''
# TODO
- Turn off labels of control points
- Transform data to a different reference frame (Use Liv's code )
- 
'''
#
# Control Points
#

# Create a fiducial node of a certain name. This node can then be populated with control points
node_id = slicer.modules.markups.logic().AddNewFiducialNode('pointList')
# self.markup_node = slicer.mrmlScene.GetNodeByID(node_id) # Self used when in module
pointList = slicer.mrmlScene.GetNodeByID(node_id)
# To get a node from the scene
pointList = slicer.util.getNode('nodeList')
# Adding a node to the scene
pointList.AddControlPoint([0, 0, 0])
# Changing the color of a node
pointList.GetDisplayNode().SetSelectedColor(0.3,0.6,0.1) # makes it green for healthy points
# Change visibiility of the points
pointList.SetNthControlPointVisibility(0,True)
#Change the position and orientation of a previously make control point
pointList.SetNthControlPointPositionFromArray(0,np.array([0,0,0]))
# Delete all the points in the pointList_World
pointList.RemoveAllMarkups()

pos = [0,0,0,0]
pointList.getNthFiducialWorldCoordinates(0,pos)
pos = pos[:-1]
# Get length of point list
pointList.GetNumberOfControlPoints()
#
# Transforms
#


# Move the point list to a new reference frame
pointList.SetAndObserveTransformNodeID(EMT2WorldTransform.GetID())


#
# Other Code Snippets
#
set 
# Liv's Code
for i in range(probeTip.GetNumberOfMarkups()):
      # get point position
      pos = np.zeros(3)
      probeTip.GetNthFiducialPosition(i,pos)

      # get and apply probe transforms to point position in retractor coordinates
      probeModelToProbeNode = slicer.util.getNode("probeModelToProbe")
      probeModelToProbeMatrix = probeModelToProbeNode.GetMatrixTransformToParent()
      pos = probeModelToProbeMatrix.MultiplyPoint(np.append(pos,1))

      ProbeToRetractorNode = slicer.util.getNode("ProbeToRetractor")
      ProbeToRetractorMatrix = ProbeToRetractorNode.GetMatrixTransformToParent()
      pos = ProbeToRetractorMatrix.MultiplyPoint(pos)

      # add point to output point list
      n = outputPoints.AddControlPoint(pos[:3])
      #outputPoints.SetNthControlPointLabel(n, str(self.num))
      outputPoints.SetNthControlPointLabel(n, "")
      # set the visibility flag
      outputPoints.SetNthControlPointVisibility(n, 1)

      return outputPoints

# Other code for Control Points
def initialize_points(self):
   slicer.modules.markups.logic().SetActiveListID(self.markup_node)
   self.markup_node.SetControlPointLabelFormat('P%d')
   for i in range(1, self.N_POINT + 1):
       self.markup_node.AddControlPoint([0, 0, 0])
   self.markup_node.UnsetAllControlPoints()
   self.markup_node.SetMaximumNumberOfControlPoints(self.N_POINT)

def place_points(self):
   slicer.modules.markups.logic().SetActiveListID(self.markup_node)
   for i in range(1, self.N_POINT + 1):
       self.markup_node.SetNthControlPointPositionFromArray(i, self.points[i - 1])
       self.markup_node.SetNthControlPointLabel(i, str(i))
       self.markup_node.SetNthControlPointVisibility(i, 1)
