import vtk
import slicer


def isosurfaces_from_volume(
    vol_node, thresholds, decimate_target_reduction=0.25, progress_callback=None
):
    """Compute a model node consisting of isosurfaces from the given volume node.
    Uses vtkFlyingEdges3D to generate isosurface mesh.

    Args:
        vol_node: a vtkMRMLScalarVolumeNode
        thresholds: a sequence of floats; values at which to threshold the scalar volume. each value
            should result in one isosurface
        decimate_target_reduction: by how much to decimate after doing vtkFlyingEdges3D
        progress_callback: Optionally, a function that takes a progress_percentage float value.
            If this is provided then progress_callback(progress_percentage) will be called
            while the computation is being done.
    Return: a vtkMRMLModelNode
    """

    if progress_callback is None:

        def progress_callback(progress_percentage):
            pass

    def create_vtk_progress_callback(start_percent, end_percent):
        def vtk_progress_callback(obj, event):
            progress_fraction_for_this_step = obj.GetProgress()
            total_progress_percent = start_percent + progress_fraction_for_this_step * (
                end_percent - start_percent
            )
            progress_callback(total_progress_percent)

        return vtk_progress_callback

    sol_image_data = vol_node.GetImageData()
    ijkToRas_transform = vtk.vtkTransform()
    ijkToRas_matrix = vtk.vtkMatrix4x4()
    vol_node.GetIJKToRASMatrix(ijkToRas_matrix)
    ijkToRas_transform.SetMatrix(ijkToRas_matrix)

    flying_edges = vtk.vtkFlyingEdges3D()
    flying_edges.SetInputData(sol_image_data)
    for i, threshold in enumerate(thresholds):
        flying_edges.SetValue(i, threshold)
    flying_edges.ComputeScalarsOff()
    flying_edges.ComputeGradientsOff()
    flying_edges.ComputeNormalsOff()
    flying_edges.AddObserver(
        vtk.vtkCommand.ProgressEvent, create_vtk_progress_callback(0, 50)
    )

    transformer = vtk.vtkTransformPolyDataFilter()
    transformer.SetInputConnection(flying_edges.GetOutputPort())
    transformer.SetTransform(ijkToRas_transform)
    transformer.AddObserver(
        vtk.vtkCommand.ProgressEvent, create_vtk_progress_callback(50, 55)
    )

    decimator = vtk.vtkDecimatePro()
    decimator.SetInputConnection(transformer.GetOutputPort())
    decimator.SetFeatureAngle(60)
    decimator.SplittingOff()
    decimator.PreserveTopologyOn()
    decimator.SetMaximumError(1)
    decimator.SetTargetReduction(decimate_target_reduction)
    decimator.AddObserver(
        vtk.vtkCommand.ProgressEvent, create_vtk_progress_callback(55, 80)
    )

    normals = vtk.vtkPolyDataNormals()
    normals.SetComputePointNormals(True)
    normals.SetInputConnection(decimator.GetOutputPort())
    normals.SetFeatureAngle(60)
    normals.SetSplitting(True)
    normals.AddObserver(
        vtk.vtkCommand.ProgressEvent, create_vtk_progress_callback(80, 95)
    )

    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())
    stripper.AddObserver(
        vtk.vtkCommand.ProgressEvent, create_vtk_progress_callback(95, 100)
    )

    stripper.Update()
    mesh = stripper.GetOutput()

    fieldData = vtk.vtkFieldData()
    mesh.SetFieldData(fieldData)
    coordinateSystemFieldArray = vtk.vtkStringArray()
    coordinateSystemFieldArray.SetName("SPACE")
    coordinateSystemFieldArray.InsertNextValue("RAS")
    fieldData.AddArray(coordinateSystemFieldArray)

    model = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
    model.SetAndObserveMesh(mesh)
    return model
