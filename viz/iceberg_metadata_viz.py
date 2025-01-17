import argparse
import json
from pyiceberg.catalog import Catalog
from pyiceberg.catalog.rest import RESTCatalog
from d3blocks import D3Tree

def get_iceberg_catalog(catalog_config):
    # Initialize the REST Catalog
    catalog = RESTCatalog(
        uri=catalog_config['uri'],
        token=catalog_config.get('token', None),
        properties=catalog_config.get('properties', {})
    )
    return catalog

def get_table_metadata(catalog, namespace, table_name):
    # Get the table from the catalog
    table = catalog.load_table(f"{namespace}.{table_name}")
    # Extract metadata
    metadata = {
        "table_name": table.name,
        "schema": [str(field) for field in table.schema.fields],
        "location": table.location,
        "properties": table.properties
    }
    return metadata

def create_tree_structure(metadata):
    # Create a tree structure for visualization
    tree_data = {
        "name": metadata["table_name"],
        "children": [
            {"name": "Schema", "children": [{"name": field} for field in metadata["schema"]]},
            {"name": "Location", "children": [{"name": metadata["location"]}]},
            {"name": "Properties", "children": [{"name": f"{k}: {v}"} for k, v in metadata["properties"].items()]}
        ]
    }
    return tree_data

def visualize_metadata(tree_data, output_file):
    # Visualize the tree structure using d3blocks
    d3 = D3Tree()
    d3.show(tree_data, output_file)

def main():
    parser = argparse.ArgumentParser(description="Visualize Apache Iceberg Table Metadata")
    parser.add_argument('--uri', required=True, help='URI of the REST catalog')
    parser.add_argument('--token', help='Token for authentication (if required)')
    parser.add_argument('--namespace', required=True, help='Namespace of the table')
    parser.add_argument('--table_name', required=True, help='Name of the table')
    parser.add_argument('--output_file', default='table_metadata.html', help='Output file for the visualization')
    args = parser.parse_args()

    catalog_config = {
        'uri': args.uri,
        'token': args.token
    }

    catalog = get_iceberg_catalog(catalog_config)
    metadata = get_table_metadata(catalog, args.namespace, args.table_name)
    tree_data = create_tree_structure(metadata)
    visualize_metadata(tree_data, args.output_file)

if __name__ == "__main__":
    main()
