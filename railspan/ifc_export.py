"""Export Railspan's generated conceptual solids as IFC4 tessellations."""

from .alignment import Alignment

ELEMENT_TYPES = {
    "deck": "IfcSlab",
    "girder": "IfcBeam",
    "foundation": "IfcFooting",
}

# Each section is ordered (low y/low z, low y/high z, high y/low z, high y/high z).
START_FACE = (0, 1, 3, 2)
END_FACE = (4, 6, 7, 5)
SIDES = ((0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6))


def triangulate(segments):
    """Share adjacent section vertices and omit internal caps."""
    vertices = list(segments[0][:4])
    triangles = []
    for index, segment in enumerate(segments):
        vertices.extend(segment[4:])
        faces = list(SIDES)
        if index == 0:
            faces.append(START_FACE)
        if index == len(segments) - 1:
            faces.append(END_FACE)
        offset = 4 * index + 1  # IFC coordinate indices are one-based.
        for face in faces:
            a, b, c, d = (offset + vertex for vertex in face)
            triangles.extend(((a, b, c), (a, c, d)))
    return [tuple(map(float, point)) for point in vertices], triangles


def projected_crs_name(epsg):
    from pyproj import CRS
    from pyproj.exceptions import CRSError

    try:
        crs = CRS.from_epsg(epsg)
    except CRSError as error:
        raise ValueError(f"EPSG:{epsg} 좌표계를 찾을 수 없습니다.") from error
    axes = crs.axis_info
    if (not crs.is_projected or len(axes) != 2
            or {axis.direction for axis in axes} != {"east", "north"}
            or any(axis.unit_conversion_factor != 1 for axis in axes)):
        raise ValueError(f"EPSG:{epsg}는 동·북 방향의 미터 단위 투영좌표계여야 합니다.")
    return f"EPSG:{epsg}"


def export_ifc(model, ifc):
    file = ifc.file(schema="IFC4")
    create = file.create_entity
    guid = ifc.guid.new
    origin = create("IfcCartesianPoint", Coordinates=(0., 0., 0.))
    axis = create("IfcAxis2Placement3D", Location=origin)
    context = create("IfcGeometricRepresentationContext", ContextType="Model",
                     CoordinateSpaceDimension=3, Precision=1e-7, WorldCoordinateSystem=axis)
    body = create("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                  ContextType="Model", ParentContext=context, TargetView="MODEL_VIEW")
    metre = create("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    epsg = model["alignment"].get("epsg")
    eastings = northings = 0.
    if epsg is not None:
        crs = create("IfcProjectedCRS", Name=projected_crs_name(epsg), MapUnit=metre)
        location = model["alignment"]["placement"]
        eastings, northings = float(location["site_x"]), float(location["site_y"])
        # The generated vertices are already oriented to grid east and north.
        create("IfcMapConversion", SourceCRS=context, TargetCRS=crs,
               Eastings=eastings, Northings=northings, OrthogonalHeight=0.,
               XAxisAbscissa=1., XAxisOrdinate=0., Scale=1.)
    project = create("IfcProject", GlobalId=guid(), Name="Railspan | " + model["kind"],
                     RepresentationContexts=[context],
                     UnitsInContext=create("IfcUnitAssignment", Units=[metre]))
    site_placement = create("IfcLocalPlacement", RelativePlacement=axis)
    site = create("IfcSite", GlobalId=guid(), Name="Railspan conceptual bridge",
                  ObjectPlacement=site_placement, CompositionType="ELEMENT")
    create("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
    placement = create("IfcLocalPlacement", PlacementRelTo=site_placement, RelativePlacement=axis)

    elements = []
    untransformed = Alignment(0, 0, 0, 0)
    for item in model["objects"]:
        segments = item.get("mesh")
        if segments is None:
            segments = [vertices for _, _, vertices in
                        untransformed.cells(item, None, follow_profile=False)]
        vertices, coordinates = triangulate(segments)
        if epsg is not None:
            vertices = [(x-eastings, y-northings, z) for x,y,z in vertices]
        points = create("IfcCartesianPointList3D", CoordList=vertices)
        mesh = create("IfcTriangulatedFaceSet", Coordinates=points, CoordIndex=coordinates,
                      Closed=True)
        shape = create("IfcShapeRepresentation", ContextOfItems=body,
                       RepresentationIdentifier="Body", RepresentationType="Tessellation", Items=[mesh])
        element = create(ELEMENT_TYPES.get(item["group"], "IfcBuildingElementProxy"),
                         GlobalId=guid(), Name=item["name"], ObjectType=item["group"],
                         Tag=str(item["id"]), ObjectPlacement=placement,
                         Representation=create("IfcProductDefinitionShape", Representations=[shape]))
        elements.append(element)

        attributes = [("Role", "IfcLabel", item["role"])]
        if item["role"] != "bridge":
            attributes.extend([
                ("TargetCategory", "IfcLabel", model["target_categories"][item["category"]]),
                ("RequiredClearance", "IfcLengthMeasure", float(item["required_clearance"])),
                ("ClearanceMode", "IfcLabel", item["clearance_mode"]),
            ])
        properties = [create("IfcPropertySingleValue", Name=name, NominalValue=create(type_name, value))
                      for name, type_name, value in attributes]
        property_set = create("IfcPropertySet", GlobalId=guid(), Name="RailspanReview", HasProperties=properties)
        create("IfcRelDefinesByProperties", GlobalId=guid(), RelatedObjects=[element],
               RelatingPropertyDefinition=property_set)
    create("IfcRelContainedInSpatialStructure", GlobalId=guid(),
           RelatedElements=elements, RelatingStructure=site)
    return file.to_string().encode("ascii")
