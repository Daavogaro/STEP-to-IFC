# STEP-to-IFC Blender Add-on

Although STEP (ISO 10303-21) and IFC (ISO 16739-1) are both standardized, their conceptual and practical incompatibilities continue to hinder seamless data exchange between the manufacturing and construction sectors. The approach is not merely a format conversion but a structured system to adapt industrial logic to the information needs of civil design—ensuring semantic integrity and computational efficiency. This workflow is scalable, transparent and open-source, and thanks to the intuitive User Interface is usable also in professional context without advanced programming skills. This work is described in a paper, the preprint of which is available at the following link: [Click to read the paper](https://www.mdpi.com/2079-8954/13/6/421)

This addon for Blender was developed as part of a project to convert STEP files to the IFC-SPF (Step Physical File) format. The repository includes a complete guide to the procedure used, with all references used in the process.
Although the main focus is STEP to IFC conversion, the addon is compatible with `glTF`, `FBX`, or any other supported `Blender format`.

## How to install the add-on

1. **Install Blender** </br>
   Download and install the latest version from the official website [Blender Download](https://www.blender.org/download/)
2. **Install Bonsai Extension** </br>
   This add-on uses [Bonsai](https://bonsaibim.org/), a powerful tool for IFC editing in Blender. Follow the instructions here to set it up: [Bonsai Download](https://docs.bonsaibim.org/quickstart/installation.html)
3. **Install the STEP-to-IFC Add-on** </br>

   -  Download or clone this repository.
   -  Copy the entire add-on folder to your Blender add-ons directory: </br>
      `C:\Users\[Your Username]\AppData\Roaming\Blender Foundation\Blender\[Your Blender Version]\scripts\addons`
   -  **Note:**
      -  If you don't see the `AppData` folder, make sure **"Hidden items"** are enabled in File Explorer.
      -  If the `addons` folder doesn't exist, simply create it manually.

4. **Enable the Add-on in Blender** </br>

   -  Open Blender and go to: `Edit > Preferences > Add-ons`
   -  Search for **STEP-to-IFC**, and check the box to enable it.

5. **Access the Add-on Panel** </br>

   -  Press **N** to open the side panel in the 3D viewport, or click the arrow in the top-right corner.
   -  You’ll now see the STEP-to-IFC tab where you can start working with your models.

   ![Blender installation video](/assets/images/addon_installation.gif)

## How to use STEP-to-IFC add-on

As mentioned in the introduction, this add-on was developed as part of a project focused on converting STEP files to the IFC-SPF format. However, the add-on is **not limited to STEP** files but it works with **any file format that Blender can import**.

If you're starting with a STEP file, the next section will guide you through the recommended workflow. Otherwise, feel free to skip ahead.

> ### How to convert STEP in glTF
>
> Blender doesn't support importing STEP files directly, so an intermediate format is needed. Among the available open-source options, `glTF` is the most suitable and widely supported format for this purpose.
>
> 1. **Download Mayo** </br>
>    Mayo is an open source software that can read/write 3D files from/to `STEP, IGES, STL and many other CAD formats`
>    Release packages are available for Windows and Linux. Follow the instructions here to set it up: [Mayo Github Page](https://github.com/fougue/mayo/tree/develop)
> 2. **Import STEP file** </br>
> 3. **Export glTF file** </br>
>    In order to export correctly is necessary to set up properly in `Tools > Options > Export > GLTF`
>
>    - **Target Format:** `JSON` </br>
>      This command allows you to select the encoding format for glTF. The JSON format is faster, and by using the `extra` field, you can assign custom properties to each node. These properties are intended to be integrated into the IFC properties attachment workflow. Although this feature is not yet implemented, it is planned for future development.
>
>    - **Node Name Format:** `InstanceOrProduct` </br>
>      In a STEP file, products are not identified by an _ID_, but rather by a unique _Instance Name_ within the project. This identifier must be used to match properties from the CSV file in the following steps. With this setup, the system will assign the _Instance Name_ to each node. If the _Instance Name_ is not available, the _Product Name_ will be used instead.

<!-- >    - **Mesh Name Format:** `InstanceOrProduct` </br>
>      This -->

### Import your file(s)

Import your `glTF`, `FBX`, or any other supported `Blender format` directly into Blender. In the STEP standard, the term **product** refers to a general entity that can represent either a single component or an entire assembly. This concept supports a hierarchical structure, where assemblies and parts are organized across multiple levels. An **assembly** is a product that consists of one or more parts or nested assemblies, while **parts** are the fundamental building blocks used to create assemblies. This structure naturally forms an assembly tree.
The add-on's user interface features two panels, each displaying a sequence of commands that should be executed in a specific order.

### Geometry and assembly tree simplification

The first panel manages the simplification of geometries and the organization of the assembly hierarchy. To use the available commands, you must first select the product you want to simplify and convert to IFC. These commands operate specifically on the `Active Object` in Blender.

-  **Make meshes uniques:** Blender supports object instancing, where multiple objects share the same mesh data and differ only by spatial transformations (translation, rotation, scaling). While this approach is memory-efficient, it's not suitable for later processing steps that involve merging or modifying individual meshes. This command creates independent mesh copies for each object, making them separately editable.
-  **Delete small objects:** this command automatically removes objects whose dimensions fall below a specified threshold along the X, Y, and Z axes. It helps eliminate minor, often unnecessary components like screws, bolts, or flanges. This step is **optional**, and manual deletion of specific objects can still be done in later stages.
-  **CSV to add system properties:** a CSV file is generated containing hierarchical data for all parts in the assembly tree. The user is prompted to fill out three columns: _To be deleted_, _To be simplified_, and _To be grouped under_.

   | Level_0  | Level_1    | Level_2     | ... | Level X       | Level Y | ... | To be deleted | To be simplified | To be grouped under |
   | -------- | ---------- | ----------- | --- | ------------- | ------- | --- | ------------- | ---------------- | ------------------- |
   | Assembly | Assembly_1 | Assembly_11 | ... | Assembly_11XX | Part 1  |     | Yes           |                  |                     |
   | Assembly | Assembly_1 | Assembly_12 | ... | Assembly_12XX | Part 2  |     | No            | Yes              | Assembly_12         |
   | Assembly | Assembly_1 | Assembly_12 | ... | Part 3        |         |     | No            | No               | Assembly_12         |
   | Assembly | Assembly_1 | Assembly_13 | ... | Part 4        |         |     | No            | No               | Assembly_13         |

   ![Blender exportation CSV](/assets/video/addon_exportCSV.gif)

-  **Delete objects:** removes all meshes marked as _Yes_ in the _To be deleted_ column of the imported CSV file. Afterward, any empty assemblies (i.e., assemblies with no remaining parts) are also deleted to simplify the scene and reduce clutter.
-  **Simplify geometries:** replaces the meshes marked as _Yes_ in the _To be simplified_ column with their corresponding bounding boxes. The original materials are retained, ensuring visual consistency while reducing geometric complexity.
-  **Parse assemblies:** Organizes and groups meshes based on the values specified in the _To be grouped under_ column. Meshes assigned to the same assembly are merged into a single object, streamlining the structure and improving performance by reducing the number of separate elements in the hierarchy. </br>
   ![Blender importation CSV](/assets/video/addon_importCSV.gif)

### Assign IFC classes and PSets

-  **CSV to add IFC properties:** Generates a CSV file listing all meshes along with their paths within the assembly tree. The user is required to specify the _IFC Class_, _Predefined Type_, and, if the type is USERDEFINED, the _Object Type_ as well. Additionally, users can include custom columns using the format _Pset_Name/Prop_Name_ to define Property Sets and their associated properties. Values are then entered directly into the corresponding cells.
   | Level_0 | Level_1 | Level_2 | ... | Ifc Class | Predefined Type | Object Type | Pset_PipeSegmentTypeCommon/ </br> NominalDiameter | Pset_ManufacturerOccurrence/ </br> SerialNumber |
   | -------- | ---------- | ----------- | --- | ---------------------| --------------- | ----------- | ---- | --- |
   | Assembly | Assembly_1 | Assembly_12 | | IfcPipeSegment | RIGIDSEGMENT | | 20 | |
   | Assembly | Assembly_1 | Assembly_13 | | IfcElectricAppliance | USERDEFINED | Magnet | | SN001 |

-  **Assign IFC classes:** assigns the appropriate _IFC Class_, _Predefined Type_, and, when necessary, _Object Type_ to each mesh, based on the information provided in the CSV file.
-  **Assign PSets to IFC elements:** applies _Property Sets_ and their defined _Properties_ to the IFC elements, following the structure of the CSV. When multiple properties are associated with the same Property Set, they are grouped accordingly, ensuring full compliance with the IFC standard. </br>
   ![Blender conversion IFC](/assets/video/addon_convertIFC.gif)
