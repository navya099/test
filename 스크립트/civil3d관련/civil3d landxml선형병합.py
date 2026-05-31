import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk, simpledialog, messagebox

def merge_coord_geoms_and_profiles(xml_file, order_list, modified_file, merged_name):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Define the namespace
    ns = {'ns0': 'http://www.landxml.org/schema/LandXML-1.2'}

    # Retrieve all alignments
    alignments = root.findall('ns0:Alignments/ns0:Alignment', ns)

    # Dictionaries to store <CoordGeom> and <Profile> elements keyed by alignment name
    coord_geom_dict = {}
    profile_dict = {}
    
    # Populate the dictionaries with <CoordGeom> and <Profile> elements keyed by alignment name
    for alignment in alignments:
        name = alignment.get('name')
        coord_geom = alignment.find('ns0:CoordGeom', ns)
        profile = alignment.find('ns0:Profile', ns)
        if coord_geom is not None:
            coord_geom_dict[name] = coord_geom
        if profile is not None:
            profile_dict[name] = profile

    # Create a new <Alignments> element
    new_alignments = ET.Element('Alignments')

    # Create a single <CoordGeom> element to hold all merged <CoordGeom> elements
    merged_coord_geom = ET.Element('CoordGeom')

    # Create a single <Profile> element to hold all merged <Profile> elements
    merged_profile = ET.Element('Profile', name=merged_name)

    # Variables to manage PVI adjustments
    last_pvi_station = 0
    profile_pvi_list = []

    # First, merge <CoordGeom> elements
    for index in order_list:
        alignment_name = list(coord_geom_dict.keys())[index]
        coord_geom = coord_geom_dict[alignment_name]
        if coord_geom is not None:
            # Append each <CoordGeom> child to the new merged <CoordGeom>
            for child in coord_geom:
                merged_coord_geom.append(child)

    # Then, merge and adjust <Profile> elements
    for index in order_list:
        alignment_name = list(profile_dict.keys())[index]
        profile = profile_dict[alignment_name]

        if profile is not None:
            for prof_align in profile.findall('ns0:ProfAlign', ns):
                for elem in prof_align:
                    if elem.tag.endswith('PVI'):
                        pvi_station, pvi_elevation = elem.text.split()
                        new_pvi_station = float(pvi_station) + last_pvi_station
                        profile_pvi_list.append(('PVI', new_pvi_station, pvi_elevation))
                    elif elem.tag.endswith('ParaCurve'):
                        pvi_station, pvi_elevation = elem.text.split()
                        para_curve_length = elem.attrib.get('length', '0')
                        new_pvi_station = float(pvi_station) + last_pvi_station
                        profile_pvi_list.append(('ParaCurve', new_pvi_station, pvi_elevation, para_curve_length))

                # Update last PVI station
                last_pvi_station += float(prof_align.findall('ns0:PVI', ns)[-1].text.split()[0])

    # Create a new <ProfAlign> element with combined PVI and ParaCurve values
    new_prof_align = ET.Element('ProfAlign', name="Combined Profile")
    for item in profile_pvi_list:
        if item[0] == 'PVI':
            new_pvi = ET.Element('PVI')
            new_pvi.text = f"{item[1]} {item[2]}"
            new_prof_align.append(new_pvi)
        elif item[0] == 'ParaCurve':
            new_para_curve = ET.Element('ParaCurve', length=item[3])
            new_para_curve.text = f"{item[1]} {item[2]}"
            new_prof_align.append(new_para_curve)

    merged_profile.append(new_prof_align)

    # Create the new <Alignment> element and append the merged <CoordGeom> and <Profile>
    new_alignment = ET.Element('Alignment', name=merged_name, attrib={'length': str(last_pvi_station)})
    new_alignment.append(merged_coord_geom)
    new_alignment.append(merged_profile)

    # Append the new <Alignment> to the new <Alignments> element
    new_alignments.append(new_alignment)

    # Remove old <Alignments> element
    root.remove(root.find('ns0:Alignments', ns))

    # Append the new <Alignments> element
    root.append(new_alignments)
    
    # Save the modified XML to a new file
    with open(modified_file, 'wb') as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding='utf-8', xml_declaration=False)

    # Read the file and remove namespace prefixes
    with open(modified_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove 'ns0:' prefix
    content = content.replace('ns0:', '')
    content = content.replace(':ns0', '')
    # Write the modified content back to the file
    with open(modified_file, 'w', encoding='utf-8') as file:
        file.write(content)

def select_file(title):
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title=title, filetypes=[("XML files", "*.xml")])
    root.destroy()
    return file_path

def save_file(title):
    root = Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.asksaveasfilename(title=title, defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    root.destroy()
    return file_path

def get_order(num_items, names):
    root = Tk()
    root.withdraw()  # Hide the root window
    
    # Create a formatted string with alignment names
    options = '\n'.join([f"{i}: {name}" for i, name in enumerate(names)])
    order_str = simpledialog.askstring("Order Input", f"Enter the order of alignments (0 to {num_items-1}), separated by commas:\n\n{options}")
    root.destroy()
    
    if order_str:
        try:
            order_list = [int(i.strip()) for i in order_str.split(',')]
            if all(0 <= i < num_items for i in order_list):
                return order_list
            else:
                messagebox.showerror("Error", "Order values must be within the valid range.")
                return None
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter integers separated by commas.")
            return None
    return None

def get_merged_name():
    root = Tk()
    root.withdraw()  # Hide the root window
    merged_name = simpledialog.askstring("Merged Alignment Name", "Enter a name for the merged alignment:")
    root.destroy()
    return merged_name

if __name__ == "__main__":
    # Step 1: Select the input XML file
    xml_file = select_file("Select the XML file")
    if not xml_file:
        messagebox.showinfo("Info", "No file selected. Exiting.")
        exit()

    # Step 2: Get the alignment order from the user
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {'ns0': 'http://www.landxml.org/schema/LandXML-1.2'}
    alignments = root.findall('ns0:Alignments/ns0:Alignment', ns)
    num_items = len(alignments)
    
    # Extract alignment names
    names = [alignment.get('name') for alignment in alignments]

    order_list = get_order(num_items, names)
    if order_list is None:
        exit()

    # Step 3: Get the name for the merged alignment from the user
    merged_name = get_merged_name()
    if not merged_name:
        messagebox.showinfo("Info", "No name provided. Exiting.")
        exit()

    # Step 4: Select the output XML file
    modified_file = save_file("Save the modified XML file")
    if not modified_file:
        messagebox.showinfo("Info", "No file selected. Exiting.")
        exit()

    # Step 5: Merge <CoordGeom> and <Profile> elements and save the result
    merge_coord_geoms_and_profiles(xml_file, order_list, modified_file, merged_name)
    messagebox.showinfo("Success", "File has been modified and saved successfully.")
