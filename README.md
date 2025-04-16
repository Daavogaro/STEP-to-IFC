# STEP-to-IFC Blender Add-on

This addon for Blender was developed as part of a project to convert STEP files to the IFC-SPF (Step Physical File) format. The repository includes a complete guide to the procedure used, with all references used in the process.
Although the main focus is STEP to IFC conversion, the addon is compatible with any format that can be imported into Blender.

### How to install the add-on

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

### How to use STEP-to-IFC add-on

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

## Import your file(s)
