import rdflib
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
import os

# Graph initialization is now global
ontology_graph = Graph()

def load_ontology(ontology_file, namespace_uri):
    """
    Loads a specified ontology file and its custom namespace into the RDFLib graph.
    Returns the custom Namespace object.
    """
    global ontology_graph
    
    # Clear previous graph data before loading a new one
    ontology_graph.remove((None, None, None))
    
    custom_namespace = Namespace(namespace_uri)
    
    try:
        if not os.path.exists(ontology_file):
            raise FileNotFoundError(f"Ontology file not found: {ontology_file}")

        with open(ontology_file, 'rb') as f:
            ontology_graph.parse(f, format="turtle")
        print(f"Ontology '{ontology_file}' successfully loaded into RDFLib Graph.")
        return custom_namespace
    except Exception as e:
        print(f"Error loading ontology from '{ontology_file}': {e}")
        raise # Re-raise the exception to stop the program if the ontology fails to load

def get_appliance_functions(appliance_uri, namespace):
    """
    Retrieves the list of available functions for a specific appliance from the ontology.
    Requires the appliance URI and the custom namespace object.
    Returns a list of dictionaries.
    """
    functions_list = []
    
    # Iterate through triples connecting appliance_uri with a function
    for s, p, o in ontology_graph.triples((appliance_uri, namespace.hasFunction, None)):
        function_uri = o
        
        function_label = ontology_graph.value(function_uri, RDFS.label)
        
        # --- PERBAIKAN DI SINI ---
        # Langsung ambil nilai string dari properti `implements_mp`
        implements_mp_value = ontology_graph.value(function_uri, namespace.implements_mp)

        functions_list.append({
            "name": str(function_label) if function_label else str(function_uri).split('#')[-1],
            "implements_mp": str(implements_mp_value) if implements_mp_value else "None",
        })
    return functions_list

if __name__ == "__main__":
    
    # --- 1: Memuat Ontologi Microwave ---
    print("\n--- Testing with Microwave Ontology ---")
    
    microwave_file = "microwave_ontology.ttl"
    microwave_namespace_uri = "http://www.example.org/microwave_ontology#"
    
    try:
        microwave_EX = load_ontology(microwave_file, microwave_namespace_uri)
        microwave_inst_uri = microwave_EX.microwave # Perbaiki di sini, sesuaikan dengan nama instance yang benar
        
        functions = get_appliance_functions(microwave_inst_uri, microwave_EX)
        
        if functions:
            print(f"Functions for {str(microwave_inst_uri).split('#')[-1]}:")
            for func in functions:
                print(f"  - Function Name: {func['name']}, Implements MP: {func['implements_mp']}")
        else:
            print(f"No functions found for {str(microwave_inst_uri).split('#')[-1]}.")
    except (FileNotFoundError, Exception) as e:
        print(f"Skipping microwave test due to an error: {e}")

    # --- 2: Memuat Ontologi Ketel ---
    print("\n--- Testing with Kettle Ontology ---")

    ketel_file = "ketel_ontology.ttl" 
    ketel_namespace_uri = "http://www.example.org/ketel_ontology#"
    
    try:
        ketel_EX = load_ontology(ketel_file, ketel_namespace_uri)
        ketel_inst_uri = ketel_EX.kettle # Perbaiki di sini, sesuaikan dengan nama instance yang benar
        
        functions = get_appliance_functions(ketel_inst_uri, ketel_EX)
        
        if functions:
            print(f"Functions for {str(ketel_inst_uri).split('#')[-1]}:")
            for func in functions:
                print(f"  - Function Name: {func['name']}, Implements MP: {func['implements_mp']}")
        else:
            print(f"No functions found for {str(ketel_inst_uri).split('#')[-1]}.")
    except (FileNotFoundError, Exception) as e:
        print(f"Skipping kettle test due to an error: {e}")
        
    # --- 3: Memuat Ontologi Stove ---
    print("\n--- Testing with Stove Ontology ---")

    stove_file = "stove_ontology.ttl" 
    stove_namespace_uri = "http://www.example.org/stove_ontology#"
    
    try:
        stove_EX = load_ontology(stove_file, stove_namespace_uri)
        stove_inst_uri = stove_EX.stove # Perbaiki di sini, sesuaikan dengan nama instance yang benar
        
        functions = get_appliance_functions(stove_inst_uri, stove_EX)
        
        if functions:
            print(f"Functions for {str(stove_inst_uri).split('#')[-1]}:")
            for func in functions:
                print(f"  - Function Name: {func['name']}, Implements MP: {func['implements_mp']}")
        else:
            print(f"No functions found for {str(stove_inst_uri).split('#')[-1]}.")
    except (FileNotFoundError, Exception) as e:
        print(f"Skipping stove test due to an error: {e}")
        
    # --- 4: Memuat Ontologi Laptop ---
    print("\n--- Testing with Laptop Ontology ---")
    
    laptop_file = "laptop_ontology.ttl"
    laptop_namespace_uri = "http://www.example.org/laptop_ontology#"
    
    try:
        laptop_EX = load_ontology(laptop_file, laptop_namespace_uri)
        laptop_inst_uri = laptop_EX.laptop # Perbaiki di sini, sesuaikan dengan nama instance yang benar
        
        functions = get_appliance_functions(laptop_inst_uri, laptop_EX)
        
        if functions:
            print(f"Functions for {str(laptop_inst_uri).split('#')[-1]}:")
            for func in functions:
                print(f"  - Function Name: {func['name']}, Implements MP: {func['implements_mp']}")
        else:
            print(f"No functions found for {str(laptop_inst_uri).split('#')[-1]}.")
    except (FileNotFoundError, Exception) as e:
        print(f"Skipping laptop test due to an error: {e}")
