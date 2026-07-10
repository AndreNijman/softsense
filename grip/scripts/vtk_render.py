"""High-quality VTK off-screen renderer for a solved texture FEA panel.

render_panel(S, vmax, defscale, ...) -> RGB uint8 image (numpy). Builds the
deformed exposed-surface polydata coloured by von Mises, smooths the voxel
stair-steps, and renders with Phong shading + MSAA studio lighting.
"""
import numpy as np
import vtk
from vtk.util import numpy_support as ns
import matplotlib.pyplot as plt

def _turbo_lut(vmax, n=256):
    lut = vtk.vtkLookupTable(); lut.SetNumberOfTableValues(n); lut.SetTableRange(0, vmax)
    cm = plt.cm.turbo
    for i in range(n):
        r, g, b, _ = cm(i/(n-1)); lut.SetTableValue(i, r, g, b, 1.0)
    lut.Build()
    return lut

def render_panel(S, vmax, defscale, size=(860, 720), bg=(0.965, 0.965, 0.972),
                 u=(0.42, -0.78, 0.50), zoom=1.55, smooth_iter=20, sload=1.0):
    coords = np.ascontiguousarray(S["coords"] + defscale*S["U"])
    fnodes = S["fnodes"]; fvm = np.ascontiguousarray(S["fvm"]*sload, np.float64)
    L = S["L"]; ztop = S["base_h"] + S["h"]

    pts = vtk.vtkPoints(); pts.SetData(ns.numpy_to_vtk(coords, deep=1))
    nq = len(fnodes)
    cells = np.empty((nq, 5), np.int64); cells[:, 0] = 4; cells[:, 1:] = fnodes
    ca = vtk.vtkCellArray(); ca.SetCells(nq, ns.numpy_to_vtkIdTypeArray(cells.ravel(), deep=1))
    poly = vtk.vtkPolyData(); poly.SetPoints(pts); poly.SetPolys(ca)
    sc = ns.numpy_to_vtk(fvm, deep=1); sc.SetName("vm"); poly.GetCellData().SetScalars(sc)

    c2p = vtk.vtkCellDataToPointData(); c2p.SetInputData(poly); c2p.Update()
    tri = vtk.vtkTriangleFilter(); tri.SetInputConnection(c2p.GetOutputPort()); tri.Update()
    sm = vtk.vtkWindowedSincPolyDataFilter(); sm.SetInputConnection(tri.GetOutputPort())
    sm.SetNumberOfIterations(smooth_iter); sm.SetPassBand(0.06)
    sm.BoundarySmoothingOn(); sm.FeatureEdgeSmoothingOff(); sm.NonManifoldSmoothingOn()
    sm.NormalizeCoordinatesOn(); sm.Update()
    nrm = vtk.vtkPolyDataNormals(); nrm.SetInputConnection(sm.GetOutputPort())
    nrm.SetFeatureAngle(55); nrm.SplittingOff(); nrm.ConsistencyOn(); nrm.Update()

    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nrm.GetOutputPort())
    mp.SetLookupTable(_turbo_lut(vmax)); mp.SetScalarRange(0, vmax)
    mp.SetScalarModeToUsePointData(); mp.InterpolateScalarsBeforeMappingOn()
    act = vtk.vtkActor(); act.SetMapper(mp)
    pr = act.GetProperty(); pr.SetInterpolationToPhong()
    pr.SetAmbient(0.30); pr.SetDiffuse(0.85); pr.SetSpecular(0.28); pr.SetSpecularPower(28)

    ren = vtk.vtkRenderer(); ren.SetBackground(*bg); ren.AddActor(act)
    ren.AutomaticLightCreationOff()
    key = vtk.vtkLight(); key.SetLightTypeToCameraLight(); key.SetPosition(-0.6, 1.0, 1.0)
    key.SetFocalPoint(0, 0, 0); key.SetIntensity(0.95); key.SetColor(1.0, 0.97, 0.92)
    fill = vtk.vtkLight(); fill.SetLightTypeToCameraLight(); fill.SetPosition(0.9, -0.2, 0.5)
    fill.SetFocalPoint(0, 0, 0); fill.SetIntensity(0.45); fill.SetColor(0.9, 0.95, 1.0)
    rim = vtk.vtkLight(); rim.SetLightTypeToCameraLight(); rim.SetPosition(0.0, 0.3, -1.0)
    rim.SetFocalPoint(0, 0, 0); rim.SetIntensity(0.30); rim.SetColor(1, 1, 1)
    for lt in (key, fill, rim): ren.AddLight(lt)

    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren)
    rw.SetSize(*size); rw.SetMultiSamples(8)

    fx, fy, fz = L/2, L/2, ztop*0.32
    uu = np.array(u, float); uu /= np.linalg.norm(uu)
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1)
    cam.SetFocalPoint(fx, fy, fz)
    cam.SetPosition(fx + 10*uu[0], fy + 10*uu[1], fz + 10*uu[2])
    # fit to FIXED bounds (not the deformed geometry) so framing is identical
    # across a load ramp — only the texture moves, the camera doesn't wobble
    ren.ResetCamera(0, L, 0, L, 0, ztop); ren.ResetCameraClippingRange(); cam.Zoom(zoom)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw)
    w2i.SetInputBufferTypeToRGB(); w2i.ReadFrontBufferOff(); w2i.Update()
    im = w2i.GetOutput(); W, H, _ = im.GetDimensions()
    arr = ns.vtk_to_numpy(im.GetPointData().GetScalars()).reshape(H, W, -1)[::-1].copy()
    rw.Finalize()
    return arr


if __name__ == "__main__":
    import json, os, sys, time
    from voxel_fea import solve_texture
    d = json.load(open(os.path.join(os.path.dirname(__file__), "..", "iterations",
                                    "crosshatch_champ.json")))
    t = time.time(); S = solve_texture("crosshatch", d["params"], a=0.12)
    print(f"solve {time.time()-t:.1f}s  faces={len(S['fnodes'])}")
    vmax = float(np.percentile(S["vm"], 98))
    defs = 0.45/np.abs(S["U"]).max()
    img = render_panel(S, vmax, defs)
    plt.imsave("/tmp/vtk_panel.png", img)
    print("WROTE /tmp/vtk_panel.png", img.shape)
