# ontology_reader.py

import rdflib
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
import os
from tkinter import messagebox

class OntologyReader:
    def __init__(self):
        self.ontology_graph = Graph()

    def load_ontology(self, ontology_file, namespace_uri):
        self.ontology_graph.remove((None, None, None))
        custom_namespace = Namespace(namespace_uri)
        
        try:
            full_path = os.path.join(os.path.dirname(__file__), 'ontologies', ontology_file)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Ontology file not found: {full_path}")

            with open(full_path, 'rb') as f:
                self.ontology_graph.parse(f, format="turtle")
            print(f"Ontology '{ontology_file}' was loaded successfully.")
            return custom_namespace
        except Exception as e:
            messagebox.showerror("Ontology Error", f"Failed to load ontology: {e}")
            return None

    def get_appliance_functions(self, appliance_uri, namespace):
        functions_list = []
        for s, p, o in self.ontology_graph.triples((appliance_uri, namespace.hasFunction, None)):
            function_uri = o
            function_label = self.ontology_graph.value(function_uri, RDFS.label)
            implements_mp_value = self.ontology_graph.value(function_uri, namespace.implements_mp)

            functions_list.append({
                "name": str(function_label) if function_label else str(function_uri).split('#')[-1],
                "implements_mp": str(implements_mp_value) if implements_mp_value else "None",
                "uri": function_uri
            })
        return functions_list

    def get_first_step(self, appliance_uri, namespace):
        for s, p, o in self.ontology_graph.triples((appliance_uri, namespace.hasStep, None)):
            first_step_uri = o
            function_uri = self.ontology_graph.value(first_step_uri, namespace.isFunctionOf)
            
            if function_uri:
                function_label = self.ontology_graph.value(function_uri, RDFS.label)
                implements_mp_value = self.ontology_graph.value(function_uri, namespace.implements_mp)
                return {
                    "step_uri": first_step_uri,
                    "function_name": str(function_label) if function_label else str(function_uri).split('#')[-1],
                    "implements_mp": str(implements_mp_value) if implements_mp_value else "None",
                }
        return None

    def get_next_step(self, current_step_uri, namespace):
        next_step_uri = self.ontology_graph.value(current_step_uri, namespace.nextStep)
        if next_step_uri:
            function_uri = self.ontology_graph.value(next_step_uri, namespace.isFunctionOf)
            if function_uri:
                function_label = self.ontology_graph.value(function_uri, RDFS.label)
                implements_mp_value = self.ontology_graph.value(function_uri, namespace.implements_mp)
                return {
                    "step_uri": next_step_uri,
                    "function_name": str(function_label) if function_label else str(function_uri).split('#')[-1],
                    "implements_mp": str(implements_mp_value) if implements_mp_value else "None",
                }
        return None